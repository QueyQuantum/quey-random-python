# Quey: Cloud Quantum RNG for Python

Standard Pseudo-Random Number Generators (like Python's Mersenne Twister or Numpy's PCG64) are great for everyday tasks. But when running massive Monte Carlo simulations or cryptographic key derivations, two fundamental issues arise:

1.  **Parallel Seed Collisions:** Spawning multiple cloud workers often results in identical time-based seeds, silently ruining the statistical variance of parallel simulations.
2.  **Predictability:** Standard PRNGs are deterministic. In security-sensitive workflows, observing enough outputs allows complete state recovery.

Quey was built to solve this. It provides true, unseeded physical randomness that scales effortlessly across parallel computing clusters.

## How it works

Quey operates on a proprietary Edge-to-Cloud infrastructure. Dedicated hardware nodes, isolated in absolute darkness, continuously harvest true quantum shot noise (dark current) from optical sensors. 

This raw physical entropy is cryptographically whitened (SHA-256) to guarantee mathematical uniformity, chunked, and pushed to a highly available NoSQL Cloud Buffer. The `quey-random` Python SDK allows your applications to pull this pure entropy instantly.

**Zero seeds. True physical independence.**

## Installation

```bash
pip install quey-random
```
(Optional) Install numpy for vectorized scientific arrays:
```bash
pip install numpy
```
## Benchmarks & Proofs of Concept
I built this to solve my own simulation issues, so I benchmarked it strictly against Numpy. You can find the raw scripts in the benchmarks/ folder.

### 1. The HPC Seed Collision Problem
If you spawn parallel workers requesting random numbers simultaneously, standard PRNGs often collide. Quey pulls fundamentally independent physical entropy from the cloud, making seed collision mathematically impossible.

### 2. State Recovery Attack (Security)
Using the randcrack library, we simulated an attacker observing 624 32-bit outputs to reverse-engineer the generator's matrix.
Python's Mersenne Twister: 100% predictable after observation.
Quey Quantum Entropy: 0% predictable (it's physical noise, not an algorithm).

### 3. Physical Neutrality (Ising Model)
To prove the hardware sensor introduces zero thermal bias, we ran a Metropolis algorithm on a 16x16 grid. Quey perfectly reproduced the theoretical phase transition ($T_c \approx 2.269$), matching Numpy's statistical robustness but with true quantum data.

## Quick Start
Get your free API key at queyquantum.io and set it as an environment variable (QUEY_API_KEY).

```Python
from quey_random import QueyRandom

quey = QueyRandom(api_key="your_api_key")

# 1. Standard usage
val = quey.random()
print(f"True random float: {val}")

# 2. Vectorized Numpy usage (optimized network fetching)
matrix = quey.uniform_array((1000, 1000))

# 3. Cryptographic Key Derivation (HKDF RFC 5869)
secure_key = quey.hkdf_derive(length=32, info=b"database_encryption")
```

### Architecture Notes
The edge node extraction engine (written in pure C) and backend routing remain closed-source to protect the infrastructure, but this SDK and the benchmark scripts are fully open for peer review.