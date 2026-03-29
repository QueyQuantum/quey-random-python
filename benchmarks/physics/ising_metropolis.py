import numpy as np
import matplotlib.pyplot as plt
from quey_random import QueyRandom

# WARNING: Replace with your actual Quey Cloud API Key
QUEY_API_KEY = "YOUR_QUEY_CLOUD_API_KEY"

# ==========================================
# 1. ISING MODEL PHYSICAL PARAMETERS
# ==========================================
L = 16              # Grid size L x L (256 spins)
EQ_STEPS = 500      # Thermalization sweeps (discarded to reach equilibrium)
MC_STEPS = 1000     # Measurement sweeps
T_range = np.linspace(1.5, 3.5, 12)  # Temperature range

# Initialize the Quey SDK Client
qr = QueyRandom(api_key=QUEY_API_KEY)

# ==========================================
# 2. CORE FUNCTIONS (METROPOLIS ALGORITHM)
# ==========================================
def initial_state(N):
    """Generates a random spin configuration (+1 or -1) for an N x N grid."""
    return 2 * np.random.randint(2, size=(N, N)) - 1

def mcmove_numpy(config, beta):
    """Monte Carlo move using standard PRNG (Numpy)."""
    for _ in range(L):
        for _ in range(L):
            a = np.random.randint(0, L)
            b = np.random.randint(0, L)
            s = config[a, b]
            
            # Periodic boundary conditions
            nb = config[(a+1)%L, b] + config[a, (b+1)%L] + config[(a-1)%L, b] + config[a, (b-1)%L]
            cost = 2 * s * nb
            
            # Metropolis acceptance criterion
            if cost < 0:
                s *= -1
            elif np.random.rand() < np.exp(-cost * beta):
                s *= -1
            config[a, b] = s
    return config

def mcmove_quey(config, beta):
    """
    Monte Carlo move using True QRNG (Quey Cloud).
    Fetches quantum entropy in bulk to optimize network requests.
    """
    # Fetch exactly L*L quantum floats in a single vectorized API call
    rand_array = qr.uniform_array(L * L)
    rand_idx = 0
    
    for _ in range(L):
        for _ in range(L):
            # Coordinates can remain PRNG or use Quey's randbelow if strict
            # For thermodynamic accuracy, the acceptance float is the critical quantum component
            a = np.random.randint(0, L)
            b = np.random.randint(0, L)
            s = config[a, b]
            
            nb = config[(a+1)%L, b] + config[a, (b+1)%L] + config[(a-1)%L, b] + config[a, (b-1)%L]
            cost = 2 * s * nb
            
            if cost < 0:
                s *= -1
            elif rand_array[rand_idx] < np.exp(-cost * beta):
                s *= -1
                
            rand_idx += 1
            config[a, b] = s
            
    return config

def calculate_magnetization(config):
    """Calculates the total magnetization of the lattice."""
    return np.sum(config)

# ==========================================
# 3. MAIN SIMULATION LOOP
# ==========================================
def run_simulation(mcmove_func):
    """Runs the Ising model simulation over the temperature range."""
    M_avg = np.zeros(len(T_range))
    
    for idx, T in enumerate(T_range):
        print(f"Calculating for T = {T:.2f}...")
        config = initial_state(L)
        beta = 1.0 / T
        
        # Phase 1: Thermalization (system reaches thermodynamic equilibrium)
        for _ in range(EQ_STEPS):
            mcmove_func(config, beta)
            
        # Phase 2: Measurement
        M_temp = 0
        for _ in range(MC_STEPS):
            mcmove_func(config, beta)
            M_temp += abs(calculate_magnetization(config))
            
        # Average magnetization per spin
        M_avg[idx] = M_temp / (MC_STEPS * (L * L))
        
    return M_avg

# ==========================================
# 4. EXECUTION AND PLOTTING
# ==========================================
if __name__ == "__main__":
    print("--- Starting Standard PRNG Benchmark (Numpy) ---")
    M_numpy = run_simulation(mcmove_numpy)

    print("\n--- Starting True QRNG Benchmark (Quey Cloud) ---")
    # Warning: This will consume entropy from your Firestore pool
    M_quey = run_simulation(mcmove_quey) 

    print("\nGenerating phase transition visualization...")
    plt.figure(figsize=(10, 6))
    plt.plot(T_range, M_numpy, 'o--', label='Standard PRNG (Numpy)', color='#1f77b4')
    plt.plot(T_range, M_quey, 's-', label='Quey Quantum (Cloud Ocean)', color='#ff7f0e', linewidth=2)

    # Theoretical phase transition line
    plt.axvline(x=2.269, color='red', linestyle=':', label='Theoretical Critical Temp ($T_c \\approx 2.269$)')

    plt.title('2D Ising Model Phase Transition: PRNG vs Quey QRNG ($L=16$)')
    plt.xlabel('Temperature (T)')
    plt.ylabel('Absolute Magnetization $|M|$')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend()
    
    filename = 'quey_ising_benchmark_v2.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Benchmark complete! Graph saved successfully as '{filename}'.")