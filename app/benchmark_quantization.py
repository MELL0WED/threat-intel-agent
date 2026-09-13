import time
import subprocess

import requests

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

TEST_PROMPTS = [
    "Explain what CVE-2021-44228 is in two sentences.",
    "What makes a vulnerability CRITICAL severity under CVSS?",
    "Summarize the risk of an unauthenticated remote code execution flaw.",
]


def get_gpu_memory_mb() -> int:
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        capture_output=True, text=True,
    )
    return int(result.stdout.strip())


def run_benchmark(model_id: str, label: str):
    print(f"\n=== Benchmarking {label} ({model_id}) ===")
    print("Make sure this model is loaded in LM Studio before continuing.")
    input("Press Enter when ready...")

    vram_before = get_gpu_memory_mb()

    latencies = []
    for prompt in TEST_PROMPTS:
        start = time.time()
        response = requests.post(
            LM_STUDIO_URL,
            json={
                "model": model_id,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            },
            timeout=60,
        )
        elapsed = time.time() - start
        latencies.append(elapsed)
        print(f"  Prompt took {elapsed:.2f}s")

    vram_during = get_gpu_memory_mb()

    avg_latency = sum(latencies) / len(latencies)
    print(f"\n{label} results:")
    print(f"  Avg latency: {avg_latency:.2f}s")
    print(f"  VRAM used (approx, includes OS/other apps): {vram_during} MB")
    print(f"  VRAM delta from before test: {vram_during - vram_before} MB")

    return {"label": label, "avg_latency": avg_latency, "vram_mb": vram_during}


def main():
    results = []
    results.append(run_benchmark("meta-llama-3-8b-instruct@q4_k_m", "Q4_K_M (4-bit quantized)"))
    results.append(run_benchmark("meta-llama-3-8b-instruct@q8_0", "Q8_0 (8-bit, near full precision)"))

    print("\n=== Comparison ===")
    for r in results:
        print(f"{r['label']}: {r['avg_latency']:.2f}s avg latency, {r['vram_mb']} MB VRAM")


if __name__ == "__main__":
    main()  