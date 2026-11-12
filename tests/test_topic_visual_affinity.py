"""Unit tests verifying strict topic-affinity and prevention of repeated/generic visuals."""

import unittest
from pathlib import Path

from src.scheduler import validate_topic_attachment
from src.linkedin_diagrams import build_topic_flow_spec, render_flow_diagram_gif


class TestTopicVisualAffinity(unittest.TestCase):

    def test_validate_topic_attachment_accepts_matching_media(self):
        # Create a mock temporary topic-specific file
        test_dir = Path("generated_visuals") / "linkedin" / "flow_distributed_agent_memory_test"
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / "flow_distributed_agent_memory_test.gif"
        test_file.write_bytes(b"GIF89a" + b"\x00" * 20)

        try:
            self.assertTrue(
                validate_topic_attachment(str(test_file), "Distributed Agent Memory Storage"),
                "Should accept media containing key topic words"
            )
        finally:
            if test_file.exists():
                test_file.unlink()
            if test_dir.exists():
                test_dir.rmdir()

    def test_validate_topic_attachment_rejects_generic_files(self):
        # Generic test files must always be rejected
        for bad_name in ["test_code_arch.gif", "test_token_pipe.gif", "transformer_flow.gif"]:
            bad_path = Path("generated_visuals") / bad_name
            bad_path.write_bytes(b"DATA")
            try:
                self.assertFalse(
                    validate_topic_attachment(str(bad_path), "Kubernetes vs Docker Swarm"),
                    f"Should reject generic test file {bad_name}"
                )
            finally:
                if bad_path.exists():
                    bad_path.unlink()

    def test_validate_topic_attachment_rejects_off_topic_media(self):
        # An existing file for one topic must be rejected if tested against an unrelated topic
        test_dir = Path("generated_visuals") / "linkedin" / "flow_kv_cache_pipeline_test"
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / "flow_kv_cache_pipeline_test.gif"
        test_file.write_bytes(b"GIF89a" + b"\x00" * 20)

        try:
            self.assertFalse(
                validate_topic_attachment(str(test_file), "PostgreSQL vs MongoDB Document Storage"),
                "Should reject KV-cache media for a PostgreSQL vs MongoDB topic"
            )
        finally:
            if test_file.exists():
                test_file.unlink()
            if test_dir.exists():
                test_dir.rmdir()

    def test_dynamic_flow_diagram_generation(self):
        title = "Kafka Message Ingestion Flow"
        summary = "How distributed partitions process high-throughput consumer streams"
        steps = [
            {"label": "Producer Send", "detail": "Pushes batched records to leader", "icon": "tokens"},
            {"label": "Partition Broker", "detail": "Appends to sequential write-ahead log", "icon": "embedding"},
            {"label": "ISR Replication", "detail": "Follower replicas sync log offset", "icon": "attention"},
            {"label": "Consumer Read", "detail": "Consumer group polls committed offset", "icon": "predict"},
        ]
        spec = build_topic_flow_spec(title, summary, steps=steps)
        res = render_flow_diagram_gif(spec, frames=6, duration=50)
        
        self.assertTrue(Path(res["gif_path"]).exists())
        self.assertGreater(Path(res["gif_path"]).stat().st_size, 0)
        self.assertIn("kafka", res["gif_path"].lower())
        self.assertEqual(res["stage_count"], 4)

        # Cleanup
        try:
            Path(res["gif_path"]).unlink(missing_ok=True)
            Path(res["preview_path"]).unlink(missing_ok=True)
            Path(res["folder"]).rmdir()
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()
