# 📚 AI Explained: Zero to Advanced — Complete 90-Day Curriculum

> **Guiding Principle:** Every topic builds upon the previous day. Go slow, explain ONE concept deeply, and avoid concept whiplash.

---

## 🟢 LEVEL 1: AI FUNDAMENTALS & TRADITIONAL ML (Days 1–30)

### Chapter 1: The Core Mental Model (Days 1–5)
- **Day 01:** What is Artificial Intelligence? (Rules-based Code vs. Learned Behavior)
- **Day 02:** The Big Picture: AI vs. Machine Learning vs. Deep Learning
- **Day 03:** How Computers Actually "Learn" (The Function Approximation Analogy)
- **Day 04:** What is a Dataset? (Inputs, Targets, and Why Data Quality Trumps Code)
- **Day 05:** Features and Labels: How Real-World Problems are Translated into Numbers

### Chapter 2: The Three Paradigms of Learning (Days 6–10)
- **Day 06:** Supervised Learning (Learning with a Teacher / Ground Truth)
- **Day 07:** Classification vs. Regression (Predicting Categories vs. Predicting Numbers)
- **Day 08:** Unsupervised Learning (Finding Hidden Patterns without Labels)
- **Day 09:** Clustering and Dimensionality Reduction (Grouping Data Naturally)
- **Day 10:** Reinforcement Learning (Learning via Trial, Error, and Rewards)

### Chapter 3: Training Mechanics & Model Pitfalls (Days 11–17)
- **Day 11:** Training vs. Inference (The Difference Between Studying and Taking the Exam)
- **Day 12:** Parameters vs. Hyperparameters (What the Model Learns vs. What the Engineer Sets)
- **Day 13:** The Train / Validation / Test Split (How to Prevent Cheating in ML)
- **Day 14:** Overfitting and Underfitting (The Memorization Trap vs. The Oversimplification Trap)
- **Day 15:** Bias-Variance Tradeoff (The Golden Balance of Machine Learning)
- **Day 16:** Model Evaluation Metrics (Accuracy vs. Precision vs. Recall vs. F1-Score)
- **Day 17:** Loss Functions (How a Model Calculates Its Own Mistakes)

### Chapter 4: Optimization & Neural Networks from Scratch (Days 18–25)
- **Day 18:** Gradient Descent (Walking Down the Mountain in the Fog)
- **Day 19:** Learning Rate (Why Too Fast Explodes and Too Slow Freezes)
- **Day 20:** The Biological vs. Artificial Neuron (How the Perceptron Was Born)
- **Day 21:** Activation Functions (Why Non-Linearity like ReLU and Sigmoid is Essential)
- **Day 22:** Forward Propagation (Passing Data Through the Layers)
- **Day 23:** Backpropagation & The Chain Rule (How Errors Flow Backward to Adjust Weights)
- **Day 24:** Deep Neural Networks (What Makes a Network "Deep"?)
- **Day 25:** Epochs, Batches, and Iterations (Pacing the Training Loop)

### Chapter 5: Representations & Foundations of Perception (Days 26–30)
- **Day 26:** Vectors: How Numbers Become Spatial Coordinates
- **Day 27:** Embeddings: Translating Concepts into Meaningful Geometry
- **Day 28:** Cosine Similarity & Distance (How Machines Measure If Two Things are Alike)
- **Day 29:** Introduction to NLP (How Computers Read Text Before Transformers)
- **Day 30:** Introduction to Computer Vision (How Computers "See" Pixels and Convolutions)

---

## 🟡 LEVEL 2: MODERN AI & GENERATIVE SYSTEMS (Days 31–60)

### Chapter 6: The Foundation of Modern LLMs (Days 31–37)
- **Day 31:** What is Generative AI? (Discriminative vs. Generative Systems)
- **Day 32:** What is a Large Language Model (LLM)? (Next-Token Prediction at Scale)
- **Day 33:** Tokens & Tokenization (How Words are Broken into Numbers & Why Spaces Matter)
- **Day 34:** The Multilingual Token Tax (Why Non-English Prompts Cost 4x More)
- **Day 35:** Context Windows (What 128k Tokens Really Means & Memory Limits)
- **Day 36:** Recurrent Neural Networks (RNNs) & LSTMs (Why Old NLP Hit a Memory Wall)
- **Day 37:** The 2017 Breakthrough: "Attention Is All You Need"

### Chapter 7: Deep Dive into Transformers (Days 38–45)
- **Day 38:** The Attention Mechanism (How Words Learn to Focus on Each Other)
- **Day 39:** Self-Attention Demystified (Query, Key, and Value Vectors Explained)
- **Day 40:** Multi-Head Attention (Looking at a Sentence from Multiple Perspectives)
- **Day 41:** Positional Encoding (Teaching the Transformer Word Order)
- **Day 42:** Feed-Forward Networks & Residual Connections within Transformers
- **Day 43:** Transformer Encoders vs. Decoders (BERT vs. GPT vs. T5)
- **Day 44:** The GPT Architecture (Why Autoregressive Decoder-Only Models Won)
- **Day 45:** Mixture of Experts (MoE) Architecture (How DeepSeek & Mixtral Scale Sparsely)

### Chapter 8: Training & Alignment of LLMs (Days 46–52)
- **Day 46:** Pretraining (Scraping the Web and Predicting the Next Token on 10,000 GPUs)
- **Day 47:** Supervised Fine-Tuning (SFT) (Turning a Raw Next-Token Predictor into a Helpful Assistant)
- **Day 48:** Reinforcement Learning from Human Feedback (RLHF)
- **Day 49:** Direct Preference Optimization (DPO) (Aligning Models Without Complex RL Loops)
- **Day 50:** Reasoning Models (Test-Time Compute, Extended Thinking & Chain-of-Thought)
- **Day 51:** Inference Sampling Mechanics (Greedy vs. Top-K vs. Top-P / Nucleus Sampling)
- **Day 52:** Temperature (The Dial Between Deterministic Code and Creative Hallucination)

### Chapter 9: Practical LLM Behavior & Multimodal Frontier (Days 53–60)
- **Day 53:** Hallucinations (Why LLMs Confidently Make Up Facts and How to Mitigate)
- **Day 54:** Prompt Engineering Fundamentals (Zero-Shot, Few-Shot & Step-by-Step Prompting)
- **Day 55:** System Prompts & Guardrails (Steering Model Persona and Setting Hard Boundaries)
- **Day 56:** Multimodal AI (How Models Unify Text, Audio, and Image Inputs)
- **Day 57:** Vision-Language Models (VLMs) (How LLMs "See" User Interfaces and Documents)
- **Day 58:** Diffusion Models (How Image Generation Reverses Gaussian Noise)
- **Day 59:** Text-to-Image Generation (CLIP Guidance & Latent Diffusion Architecture)
- **Day 60:** Open Weights vs. Closed APIs (The 2026 Landscape: Meta Llama & DeepSeek vs. OpenAI & Anthropic)

---

## 🔴 LEVEL 3: ADVANCED AI ENGINEERING & PRODUCTION (Days 61–90)

### Chapter 10: Retrieval-Augmented Generation (RAG) Architecture (Days 61–68)
- **Day 61:** What is RAG and Why LLMs Need External Memory?
- **Day 62:** Vector Databases (How HNSW and Vector Indexing Power Sub-Second Search)
- **Day 63:** Document Chunking Strategies (Fixed-size, Recursive, Semantic & Document-Specific)
- **Day 64:** Embedding Models in Production (Choosing Dimension, Quality, and Latency)
- **Day 65:** Retrieval Strategies (Dense Vector Search vs. Sparse BM25 Keyword Search)
- **Day 66:** Hybrid Search (Combining Vectors with Full-Text Inverted Indexes)
- **Day 67:** Reranking (Why Cross-Encoders are Crucial After Initial Retrieval)
- **Day 68:** Context Window Degradation & "Lost in the Middle" (Optimizing Context Ordering)

### Chapter 11: Fine-Tuning, Adaptation & Compression (Days 69–75)
- **Day 69:** When to Use Prompting vs. RAG vs. Fine-Tuning (The 3-Way Architectural Matrix)
- **Day 70:** Parameter-Efficient Fine-Tuning (PEFT) & LoRA (Low-Rank Adaptation)
- **Day 71:** QLoRA (Fine-Tuning 70B Models on a Single Consumer GPU with 4-bit Quantization)
- **Day 72:** Model Quantization (FP16 vs. INT8 vs. INT4: GGUF, AWQ, and EXL2)
- **Day 73:** Knowledge Distillation (Training Small, Fast 3B Models from 70B Giants)
- **Day 74:** Context Engineering & Prompt Compression (Trimming Token Bloat Without Accuracy Loss)
- **Day 75:** Prompt Caching (Saving Up to 80% on Latency and API Spend)

### Chapter 12: Autonomous AI Agents & Tool Calling (Days 76–82)
- **Day 76:** What is an AI Agent? (LLM + State Memory + Tools + Self-Correction)
- **Day 77:** The ReAct Framework (Reasoning + Acting in Real-World Execution Loops)
- **Day 78:** Function Calling & Structured JSON Outputs (How LLMs Query Databases and Run APIs)
- **Day 79:** Model Context Protocol (MCP) (Standardizing AI Connections to External Services)
- **Day 80:** Multi-Agent Architectures (Orchestrators, Workers, and Evaluators)
- **Day 81:** Human-in-the-Loop Agent Workflows (Safe Approval Gates for Enterprise Actions)
- **Day 82:** Agentic Traps: Infinite Loops, State Drift, and Tool Failure Recovery

### Chapter 13: Production Deployment, Observability & NeuBench Telemetry (Days 83–90)
- **Day 83:** LLM Evaluation & Evals (Why Automated Evals Beat "Vibe Checks")
- **Day 84:** Production LLM Observability & Tracing (Monitoring Latency, Cost, and Token Drift)
- **Day 85:** AI Security & Vulnerabilities (Prompt Injection, Jailbreaks, and Data Poisoning)
- **Day 86:** Inference Optimization: TTFT (Time-to-First-Token) vs. Inter-Token Latency
- **Day 87:** GPU Memory Economics & KV Cache (Understanding VRAM Bottlenecks in Serving)
- **Day 88:** Model Serving Frameworks (vLLM, Ollama, TensorRT-LLM, and TGI)
- **Day 89:** Multi-Model Smart Gateways (Routing Cheap Queries to Fast Models and Hard Queries to Reasoning Giants)
- **Day 90:** The Complete 2026 Production AI Architecture (The Master Blueprint & NeuBench Full Stack)
