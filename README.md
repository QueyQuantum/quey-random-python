# Quey Python SDK

Verifiable randomness from a physical entropy source.

[queyquantum.io](https://queyquantum.io) · [Documentation](https://queyquantum.io/documentation) · [Verify a draw](https://queyquantum.io/verify/89421ffc-6af3-427e-8123-fa6c799cc166)

---

## What is Quey?

Quey extracts true randomness from photonic shot noise — a measurable physical process, not an algorithm. The entropy is captured by a dedicated hardware node (Raspberry Pi 5 + NoIR camera in an isolated enclosure), processed through an extraction pipeline (LSB extraction → Von Neumann debiasing → SHA3-256 hashing), and served via a REST API.

Every selection can be signed with Ed25519 and published to a verification page anyone can check in their browser — trustlessly, via WebCrypto, with no server call required.

**Validation:** NIST SP 800-90B (min-entropy: 0.6236 bits/bit) · NIST SP 800-22 (188/188 sub-tests passed) · Shannon entropy: 7.999994 bits/byte.

---

## Installation

```bash
pip install quey-random
```

Optional, for NumPy array methods:

```bash
pip install numpy
```

---

## Quick Start

```python
from quey_random import QueyRandom

# Reads QUEY_API_KEY from environment if not provided
qr = QueyRandom()

# Random float in [0, 1)
value = qr.random()
print(value)  # 0.7391042...

# Raw entropy bytes
entropy = qr.get_bytes(32)

# Pick a winner from a list
participants = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
winner = qr.choice(participants)
print(f"Winner: {winner}")
```

Or with an explicit API key:

```python
qr = QueyRandom(api_key="qu_cloud_xxxxxxxxxxxxxxxx")
```

---

## API Reference

### `QueyRandom(api_key=None, base_url=None)`

Creates a client. If `api_key` is omitted, reads from the `QUEY_API_KEY` environment variable.

### Methods

| Method | Returns | Description |
|---|---|---|
| `random()` | `float` | Random float in [0, 1) |
| `get_bytes(length)` | `bytes` | Raw physical entropy |
| `choice(seq)` | `T` | Random element from a sequence |
| `randbelow(n)` | `int` | Random integer in [0, n) |
| `uniform_array(shape)` | `np.ndarray` | Uniform [0, 1) array — requires NumPy |
| `normal_array(shape, loc=0.0, scale=1.0)` | `np.ndarray` | Normal distribution array — requires NumPy |
| `mixed_entropy(length)` | `bytes` | Mixed local + cloud entropy |
| `hkdf_derive(length, info=b'', salt=None, input_entropy_length=32)` | `bytes` | HKDF key derivation from physical entropy |

### Exceptions

| Exception | When |
|---|---|
| `AuthenticationError` | Invalid or missing API key |
| `QuotaExceededError` | Monthly quota exceeded |
| `MissingDependencyError` | NumPy not installed (for array methods) |
| `QueyAPIError` | Base exception for other API errors |

---

## Verifiable Draws

Quey can produce cryptographically signed selections via the [Verifiable Draw API](https://queyquantum.io/documentation):

1. Winners are selected using rejection sampling — never biased modulo
2. The result is signed with Ed25519
3. A certificate is published to a public verification page

Anyone can verify the draw in their browser via WebCrypto — no server call, no trust in Quey required.

**See a real verified draw →** [queyquantum.io/verify/89421ffc-...](https://queyquantum.io/verify/89421ffc-6af3-427e-8123-fa6c799cc166)

---


## Architecture

This SDK connects to Quey's cloud buffer, which is continuously fed by a dedicated hardware node running a C extraction engine (closed-source). The extraction pipeline processes photonic shot noise through LSB extraction, Von Neumann debiasing, and SHA3-256 cryptographic hashing. This SDK and the benchmark scripts in this repository are fully open for review.

---

## Links

- **Website:** [queyquantum.io](https://queyquantum.io)
- **Documentation:** [queyquantum.io/documentation](https://queyquantum.io/documentation)
- **NIST Validation:** [queyquantum.io/stats](https://queyquantum.io/stats)
- **Verify a Draw:** [queyquantum.io/verify/89421ffc-...](https://queyquantum.io/verify/89421ffc-6af3-427e-8123-fa6c799cc166)
- **Node.js SDK:** `npm install quey-random`
