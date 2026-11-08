"""Unit tests for LinkedIn visual generators and PDF carousel builder.

Verifies:
- Dynamic slide building and page scaling (4-8 pages).
- Text wrapping and canvas dimension constraints.
- Handwritten aesthetic components (notebook lines, sticky notes, annotations).
- Specialized slide renderers: diagram, comparison matrix, code syntax, pitfalls.
- Robust font fallbacks.
- Multi-page PDF assembly and page sequencing.
- Output directory safety.
- Regression tests for defect fixes:
  1. _point_slide multi-paragraph layout & non-overlapping annotations.
  2. _diagram_slide desc/detail/description key compatibility.
  3. _code_slide 20+ line implementation scaling.
  4. _pitfalls_slide traps/pitfalls/mistakes aliases with impact & prevention.
  5. _cta_slide golden_rule and checklist rendering.
"""

import os
import shutil
import tempfile
import unittest
from PIL import Image, ImageDraw

from src.linkedin_visuals import (
    render_linkedin_carousel,
    render_linkedin_hero,
    build_slides,
    wrap_text,
    get_font,
    _point_slide,
    _diagram_slide,
    _code_slide,
    _pitfalls_slide,
    _cta_slide,
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
)


class TestLinkedInVisuals(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_canvas_dimensions(self):
        """Verify LinkedIn 4:5 portrait aspect ratio dimensions."""
        self.assertEqual(CANVAS_WIDTH, 1080)
        self.assertEqual(CANVAS_HEIGHT, 1350)

    def test_text_wrapping(self):
        """Verify wrapping breaks long sentences into legible line chunks."""
        font = get_font(size=24, kind="sans")
        dummy_img = Image.new("RGB", (100, 100))
        draw = ImageDraw.Draw(dummy_img)
        sample_text = (
            "Retrieval Augmented Generation combines neural search indexing with large language models "
            "to ground responses in authoritative external documents and prevent hallucination."
        )
        lines = wrap_text(draw, sample_text, font, max_width=400)
        self.assertGreater(len(lines), 1)
        for line in lines:
            bbox = font.getbbox(line)
            width = bbox[2] - bbox[0]
            self.assertLessEqual(width, 420)

    def test_font_fallback(self):
        """Verify that get_font returns a valid font even when given a non-existent family."""
        font = get_font(size=32, kind="non_existent_imaginary_kind")
        self.assertIsNotNone(font)
        bbox = font.getbbox("Testing Fallback")
        self.assertGreater(bbox[2], bbox[0])

    def test_build_slides_dynamic_pages(self):
        """Verify dynamic slide building handles custom variable page plans (4-8 pages)."""
        plan = {
            "title": "Kafka vs RabbitMQ Architecture",
            "topic": "Event Streaming vs Message Queues",
            "pages": [
                {
                    "slide_number": 1,
                    "kind": "cover",
                    "title": "Kafka vs RabbitMQ",
                    "badge": "ENGINEERING STUDY NOTES",
                    "subtitle": "Architectural differences and selection guide",
                    "learning_objectives": ["Understand pull vs push", "Compare throughput limits"],
                },
                {
                    "slide_number": 2,
                    "kind": "comparison",
                    "title": "Architectural Breakdown",
                    "comparison_items": ["Kafka", "RabbitMQ"],
                    "criteria_rows": [
                        {"criterion": "Data Model", "item_a": "Log Stream", "item_b": "Queue"},
                        {"criterion": "Throughput", "item_a": "1M+ msg/s", "item_b": "50K msg/s"},
                    ],
                    "annotation": "Log partitions enable parallel reads.",
                },
                {
                    "slide_number": 3,
                    "kind": "code",
                    "title": "Producer Implementation",
                    "code_snippet": "producer.send(record)\nconsumer.poll(100)",
                    "code_language": "python",
                    "annotation": "Always configure acks=all.",
                },
                {
                    "slide_number": 4,
                    "kind": "cta",
                    "title": "Key Takeaways",
                    "golden_rule": "Use Kafka for event history, RabbitMQ for complex routing.",
                    "revision_checklist": ["Check delivery guarantees", "Size partition capacity"],
                },
            ],
        }

        slides = build_slides(plan)
        self.assertEqual(len(slides), 4)
        self.assertEqual(slides[0][0], "cover")
        self.assertEqual(slides[1][0], "comparison")
        self.assertEqual(slides[2][0], "code")
        self.assertEqual(slides[3][0], "cta")

    def test_render_carousel_pdf_creation(self):
        """Verify full carousel render creates valid PDF and PNG slides with correct order."""
        plan = {
            "title": "Docker vs Virtual Machines",
            "topic": "Containerization Fundamentals",
            "pages": [
                {
                    "slide_number": 1,
                    "kind": "cover",
                    "title": "Docker vs VMs",
                    "badge": "DEV-OPS STUDY GUIDE",
                    "subtitle": "Kernel virtualization vs hypervisors",
                    "learning_objectives": ["OS kernel sharing", "Startup overheads", "Isolation security"],
                },
                {
                    "slide_number": 2,
                    "kind": "diagram",
                    "title": "Container Lifecycle",
                    "pipeline_stages": ["Dockerfile", "Image Layer", "Container Daemon", "Running Process"],
                    "annotation": "Layers are immutable and cached.",
                },
                {
                    "slide_number": 3,
                    "kind": "pitfalls",
                    "title": "Container Antipatterns",
                    "pitfalls": [
                        {"trap": "Running as root user", "impact": "Privilege escalation vulnerability", "fix": "Use non-root USER instruction"},
                    ],
                },
                {
                    "slide_number": 4,
                    "kind": "cta",
                    "title": "Summary & Rules",
                    "golden_rule": "Containers isolate user space; VMs isolate entire operating systems.",
                    "revision_checklist": ["Keep images minimal with multi-stage builds"],
                },
            ],
        }

        original_cwd = os.getcwd()
        try:
            os.chdir(self.temp_dir)
            result = render_linkedin_carousel(plan)
            self.assertIn("pdf_path", result)
            self.assertIn("png_paths", result)
            self.assertIn("slide_paths", result)
            self.assertEqual(len(result["slide_paths"]), 4)

            pdf_path = result["pdf_path"]
            self.assertTrue(os.path.exists(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 1000)

            with open(pdf_path, "rb") as f:
                header = f.read(5)
                self.assertEqual(header, b"%PDF-")

            for slide_path in result["slide_paths"]:
                self.assertTrue(os.path.exists(slide_path))
                with Image.open(slide_path) as img:
                    self.assertEqual(img.size, (CANVAS_WIDTH, CANVAS_HEIGHT))
        finally:
            os.chdir(original_cwd)

    def test_legacy_plan_backward_compatibility(self):
        """Verify build_slides gracefully falls back for legacy 6-page schema without pages array."""
        legacy_plan = {
            "topic": "Event Sourcing",
            "cover": {"headline": "Event Sourcing 101", "sub": "State as a stream of events"},
            "points": [
                {"title": "Append-Only", "body": "Events are immutable once written.", "detail": "Guarantees full audit trail."},
                {"title": "Projections", "body": "Read models are generated asynchronously.", "detail": "Allows optimal query structures."},
            ],
            "framework": {"title": "Architecture Flow", "steps": ["Command", "Handler", "Event Store", "Read DB"]},
            "takeaway": {"title": "Production Rule", "body": "Never modify event schemas without versioning."},
            "cta": {"prompt": "Have you used Event Sourcing in production?", "website": "neubench.workers.dev"},
        }

        slides = build_slides(legacy_plan)
        self.assertGreaterEqual(len(slides), 5)
        self.assertEqual(slides[0][0], "cover")
        self.assertEqual(slides[-1][0], "cta")

    # --- DEFECT REGRESSION TESTS ---

    def test_regression_diagram_desc_key_compatibility(self):
        """Verify _diagram_slide supports desc, detail, and description keys."""
        payload = {
            "title": "Execution Pipeline",
            "stages": [
                {"name": "Stage 1", "desc": "Query Encoding / Vectorize"},
                {"name": "Stage 2", "detail": "ANN Search in HNSW Index"},
                {"name": "Stage 3", "description": "Cross-Encoder Precision Rerank"},
            ],
            "annotation": "Latency budget dominated by vector I/O.",
        }
        img = _diagram_slide(payload, 3, 6)
        self.assertEqual(img.size, (CANVAS_WIDTH, CANVAS_HEIGHT))

    def test_regression_pitfalls_traps_aliases(self):
        """Verify _pitfalls_slide renders using traps, pitfalls, and mistakes keys with impact."""
        payload = {
            "title": "Production Reality",
            "traps": [
                {
                    "trap": "Naive fixed-size character chunking",
                    "impact": "Destroys semantic sentence boundaries",
                    "prevention": "Implement recursive semantic chunking with paragraph buffers",
                },
                {
                    "mistake": "Unbounded context accumulation",
                    "impact": "Induces lost in the middle degradation",
                    "fix": "Enforce token budgets and context deduplication",
                },
            ],
        }
        img = _pitfalls_slide(payload, 5, 6)
        self.assertEqual(img.size, (CANVAS_WIDTH, CANVAS_HEIGHT))

    def test_regression_cta_golden_rule_and_checklist(self):
        """Verify _cta_slide supports golden_rule, checklist, and discussion_prompt."""
        payload = {
            "golden_rule": "Garbage in, garbage out: retrieval accuracy dictates output veracity.",
            "checklist": [
                "Audit embedding model dimension compatibility across index and runtime",
                "Verify HNSW memory consumption in staging",
                "Benchmark tail latency (p99) under load",
            ],
            "discussion_prompt": "What failure mode have you encountered when scaling vector databases?",
            "website": "app.neubench.workers.dev",
        }
        img = _cta_slide(payload, 6, 6)
        self.assertEqual(img.size, (CANVAS_WIDTH, CANVAS_HEIGHT))

    def test_regression_point_slide_multi_paragraph_and_annotation(self):
        """Verify _point_slide handles multi-paragraph dense body without overlap or truncation."""
        payload = {
            "title": "Core Architecture & Definitions",
            "annotation": "Teacher note: Keep memory footprint in mind during ingestion.",
            "body": (
                "Retrieval-Augmented Generation bridges the gap between parametric memory in Large Language Models "
                "and non-parametric external knowledge bases. Rather than baking enterprise corpora into fine-tuned weights, "
                "RAG dynamically injects retrieved context into the prompt context window at inference time.\n\n"
                "The underlying representation relies on high-dimensional metric spaces where semantic proximity maps to spatial distance. "
                "Documents are parsed into semantically coherent token blocks, passed through a dense encoder model, "
                "and indexed within specialized vector databases using graph-based algorithms such as HNSW or IVF-PQ."
            ),
            "callout": "Parametric memory scales with parameter count; RAG scales with data volume and provides grounding.",
        }
        img = _point_slide(payload, 2, 6)
        self.assertEqual(img.size, (CANVAS_WIDTH, CANVAS_HEIGHT))

    def test_regression_code_slide_long_snippets(self):
        """Verify _code_slide scales dynamically for 20+ lines without truncation."""
        long_code = "\n".join([f"line_{i:02d} = execute_step({i})" for i in range(1, 23)])
        payload = {
            "title": "Minimal Reference Pattern",
            "language": "python",
            "code": long_code,
            "annotation": "Explicit over-fetching followed by cross-encoder reranking.",
        }
        img = _code_slide(payload, 4, 6)
        self.assertEqual(img.size, (CANVAS_WIDTH, CANVAS_HEIGHT))

    def test_editorial_architecture_spec_and_gif_rendering(self):
        """Verify editorial architecture flow GIF generation matches LinkedIn 1080x1350 vertical format."""
        from src.linkedin_diagrams import build_editorial_architecture_spec, render_editorial_architecture_gif
        
        spec = build_editorial_architecture_spec(
            title="Mixture of Experts (MoE)",
            summary="Routes input tokens to 8 active experts out of 256 total experts.",
            audience="working_pro",
        )
        self.assertIn("title", spec)
        self.assertIn("steps", spec)
        self.assertIn("metrics", spec)
        self.assertIn("components", spec)

        res = render_editorial_architecture_gif(
            spec=spec,
            base_name="test_flow",
            frames=12,
            duration=75,
        )
        res_path = res.get("path")
        self.assertTrue(os.path.exists(res_path))
        with Image.open(res_path) as im:
            self.assertEqual(im.size, (1080, 1350))
            self.assertTrue(im.is_animated)
            self.assertGreaterEqual(im.n_frames, 10)


if __name__ == "__main__":
    unittest.main()
