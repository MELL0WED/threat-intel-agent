# Security Threat-Intel Agent

A retrieval-augmented agent for security vulnerability lookup: given a natural-language
question, it retrieves the relevant CVE, classifies its severity using a self-trained
model, and generates a grounded answer — escalating automatically on CRITICAL findings.

Built as a learning project to demonstrate applied AI/ML engineering: RAG, streaming
ingestion, model training/distillation, and agent orchestration — with every technique
validated against a measured baseline, not just demoed.

## Architecture
Kafka (or batch script) → CVE ingestion → Qdrant vector store
↓
Question → [Redis cache check] → Retrieve (Qdrant) → Classify (DistilBERT) → Generate (LLM)
↓
Cache result in Redis


- **Ingestion**: two parallel, interchangeable paths — a batch script (`app/ingest.py`) and
  a Kafka producer/consumer pair (`app/producer.py`, `app/consumer.py`) — both writing to
  the same Qdrant collection via a shared, deterministic point-ID scheme.
- **Retrieval**: `sentence-transformers` embeddings + Qdrant cosine similarity search,
  with an optional cross-encoder reranking stage.
- **Classification**: a DistilBERT model fine-tuned on real NVD severity labels to predict
  MEDIUM/HIGH/CRITICAL. Hosted on Hugging Face Hub:
  [FalconGlide/cve-severity-classifier](https://huggingface.co/FalconGlide/cve-severity-classifier).
- **Agent**: a LangGraph state machine (`app/agent.py`) with true conditional routing — a
  semantic cache check gates the rest of the pipeline.
- **Serving**: FastAPI (`app/main.py`), exposing `/query` and `/health`.

## Results

### Retrieval (50 hand-curated, deliberately confusable CVEs; 50 hand-written eval questions)

| Method | Hit-rate@1 | Hit-rate@3 |
|---|---|---|
| Naive (embedding similarity only) | 78.0% | 90.0% |
| + Cross-encoder reranking | 80.0% | 92.0% |

Reranking helped on cases where the correct document ranked 2nd–3rd (promoted to 1st),
but hurt on a cluster of near-duplicate Office/document-exploit CVEs — a net positive,
not a uniform win.

### Severity classifier (979 real CVEs pulled via NVD bulk API, 80/20 stratified split)

Real-world CVE severity data is heavily skewed (LOW: 12/979 examples). LOW was merged
into MEDIUM after an initial 4-class run produced an unusable LOW F1 of 0.0.

| Run | Accuracy | Macro F1 | MEDIUM F1 | HIGH F1 | CRITICAL F1 |
|---|---|---|---|---|---|
| Baseline (hard labels, full 783-example train set) | 69.4% | 0.612 | 0.747 | 0.726 | 0.364 |

### Knowledge distillation (248-example subset, isolated comparison)

Distilled a DistilBERT student against soft labels from three different teacher setups
(local Llama-3-8B, the same model with a CVSS rubric prompt, and a hosted 120B model via
Groq), combining hard-label cross-entropy with KL-divergence loss.

| Teacher | Teacher accuracy | Teacher CRITICAL accuracy |
|---|---|---|
| Local Llama-3-8B, plain prompt | 52% | 3% (1/31) |
| Local Llama-3-8B, CVSS rubric prompt | 57% | 29% (9/31) — but degraded HIGH/MEDIUM accuracy elsewhere |
| Hosted gpt-oss-120b (Groq) | 63% | 16% (5/31) |

| Run (same 248-example subset) | Macro F1 |
|---|---|
| Hard-label control | 0.449 |
| Distilled (hard label + KD loss, gpt-oss-120b teacher) | 0.434 |

**Finding**: distillation degraded performance here. All three teachers, at different
model scales, systematically under-predicted CRITICAL severity in favor of HIGH — a
consistent bias, not model-specific noise. Training the student on soft labels from a
miscalibrated teacher transferred that bias, dropping the student's own CRITICAL F1 to
0.0. This demonstrates that distillation quality is bounded by teacher quality: soft
labels aren't automatically better than hard labels, and a larger model's judgment
shouldn't be trusted without first evaluating its calibration on the specific task.

## Key engineering decisions

- **Kafka** decouples advisory ingestion from processing (fetch/embed latency shouldn't
  block ingestion triggering), even though this project's scale doesn't strictly need it —
  included to demonstrate the pattern.
- **Point-ID consistency bug**: the batch and streaming ingestion paths initially used
  different point-ID schemes (`id=i` vs. Python's randomized `hash()`), causing silent
  duplicate entries in Qdrant. Fixed with a shared deterministic `hashlib.md5`-based ID
  function used by both paths.
- **vLLM vs. Ollama vs. LM Studio**: vLLM requires Linux and is built for concurrent
  multi-request serving at scale — not the right fit for local, single-user inference on a
  6GB laptop GPU. LM Studio was used for local generation/teacher-scoring instead.
- **Accidental API key commit**: two API keys were briefly hardcoded into `config.py`
  instead of `.env`, caught by GitHub's push protection before merging to the remote.
  Both keys were revoked and rotated; the commit was amended before pushing.

## Deployment attempt

Attempted live deployment on Render's free tier (512MB RAM), backed by Qdrant Cloud
(retrieval) and Groq (generation), with local dependencies (LM Studio, Docker Compose
Kafka/Redis) swapped for cloud equivalents.

Docker build succeeded after resolving several environment-mismatch issues along the
way (a Windows-only `pywin32` dependency picked up by `pip freeze`, a CUDA-specific
`torch` build with no CPU equivalent on the deploy target, and Render defaulting to a
Python version with no prebuilt wheels for several pinned packages — fixed by pinning
Python 3.10 explicitly via Docker rather than relying on buildpack auto-detection).

The running service then hit a hard memory ceiling: the agent's two loaded models
(sentence-transformer embedder + fine-tuned DistilBERT classifier) require ~1GB RAM at
startup, measured directly — roughly double Render's free-tier 512MB limit. This is a
genuine resource constraint, not a bug: multi-model inference services are memory-heavy
by nature, and free hosting tiers are generally sized for lightweight web apps rather
than services holding transformer models in memory.

The project runs correctly end-to-end locally (see "Running locally" below) and via
Docker on any host with ≥1GB available RAM. Deploying on a paid tier, or reducing
memory footprint via model quantization/lazy-loading, would resolve this — scoped as a
known next step rather than completed here.

## Stack

Python, FastAPI, LangGraph, Qdrant (local + Cloud), Redis, Kafka, Docker Compose,
sentence-transformers, DistilBERT (HuggingFace Transformers, PyTorch), scikit-learn,
LM Studio (local Llama-3-8B inference), Groq API (teacher scoring + deployed generation).

## Running locally

```bash
docker compose up -d          # Qdrant, Redis, Kafka
pip install -r requirements.txt
cp .env.example .env          # fill in NVD_API_KEY, GROQ_API_KEY as needed
python -m app.ingest           # populate Qdrant
uvicorn app.main:app --reload
```

Then POST to `http://localhost:8000/query`:
```json
{"question": "What vulnerability let attackers run code remotely through a Java logging library?"}
```

### Local quantized serving benchmark (Llama-3-8B-Instruct via LM Studio, RTX 3060 6GB)

| Quantization | Avg latency (3 prompts) |
|---|---|
| Q4_K_M (4-bit) | 12.93s |
| Q8_0 (8-bit) | 37.90s |

Q4_K_M is ~2.9x faster. VRAM measurement via `nvidia-smi` was inconclusive as designed
(captured steady-state usage after manual model-switching, not an isolated delta) —
noted as a known limitation of this benchmark's methodology.

## What's not built

- Live public deployment — blocked by free-tier memory limits (see "Deployment attempt").