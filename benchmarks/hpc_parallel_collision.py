import multiprocessing
import numpy as np
import time
import matplotlib.pyplot as plt
import os
from quey_random import QueyRandom

QUEY_API_KEY = "YOUR_QUEY_API_KEY"

def simulate_prng_worker(worker_id, num_samples):
    """
    Simulates a cloud worker using standard pseudo-randomness.
    """
    np.random.seed(int(time.time())) 
    
    x = np.random.uniform(-1.0, 1.0, num_samples)
    y = np.random.uniform(-1.0, 1.0, num_samples)
    
    distances_squared = x**2 + y**2
    inside_circle = np.sum(distances_squared <= 1.0)
    
    estimated_pi = (inside_circle / num_samples) * 4.0
    return estimated_pi

def simulate_quey_worker(worker_id, num_samples):
    """
    Simulates a cloud worker using Quey Quantum Entropy via the official SDK.
    Includes a slight desynchronization delay to prevent Firestore transaction lock contention.
    """
    # Stagger the cloud requests by 0.5 seconds per worker id to avoid DDOSing Firestore locks
    time.sleep(worker_id * 0.5)
    
    qr = QueyRandom(api_key=QUEY_API_KEY)
    
    quantum_floats_x = qr.uniform_array(num_samples)
    quantum_floats_y = qr.uniform_array(num_samples)
    
    x = quantum_floats_x * 2.0 - 1.0
    y = quantum_floats_y * 2.0 - 1.0
    
    distances_squared = x**2 + y**2
    inside_circle = np.sum(distances_squared <= 1.0)
    
    estimated_pi = (inside_circle / num_samples) * 4.0
    return estimated_pi

if __name__ == '__main__':
    print("--- HPC Parallel Seed Collision Benchmark ---")
    
    num_workers = 10
    samples_per_worker = 1000 # Reduced to 1000 to require only 160KB of pool entropy
    
    print(f"\n[1] Running {num_workers} Standard PRNG Workers (Numpy)...")
    with multiprocessing.Pool(processes=num_workers) as pool:
        prng_results = pool.starmap(simulate_prng_worker, [(i, samples_per_worker) for i in range(num_workers)])
        
    print(f"[2] Running {num_workers} Quey Quantum Workers (Cloud QRNG)...")
    # Ensuring the workers stagger properly with maxtasksperchild or mapped asynchronously
    with multiprocessing.Pool(processes=num_workers) as pool:
        quey_results = pool.starmap(simulate_quey_worker, [(i, samples_per_worker) for i in range(num_workers)])
        
    print("\n[3] Generating benchmark visualization...")
    
    plt.figure(figsize=(10, 6))
    plt.axhline(y=np.pi, color='r', linestyle='--', label='Theoretical Pi')
    plt.scatter(range(1, num_workers + 1), prng_results, color='blue', s=100, alpha=0.7, label='Standard PRNG (Seed Collision)')
    plt.scatter(range(1, num_workers + 1), quey_results, color='orange', marker='s', s=100, alpha=0.9, label='Quey QRNG (True Independence)')
    
    plt.title('Parallel Monte Carlo Estimation of Pi: PRNG vs Quey QRNG', fontsize=14)
    plt.xlabel('Worker Node ID', fontsize=12)
    plt.ylabel('Estimated Value of Pi', fontsize=12)
    plt.xticks(range(1, num_workers + 1))
    plt.legend(loc='upper right')
    plt.grid(True, linestyle=':', alpha=0.6)
    
    filename = "quey_parallel_collision_benchmark.png"
    filepath = os.path.abspath(filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    
    print("\n--- Benchmark Complete ---")
    print(f"--> Image saved at: {filepath}")