# benchmarks/security_state_recovery.py
import random
from randcrack import RandCrack
from quey_random import QueyRandom

# WARNING: Replace with your actual Quey Cloud API Key
QUEY_API_KEY = "YOUR_API_KEY"
def hack_standard_prng():
    """
    Demonstrates how standard PRNGs (Mersenne Twister) can be 100% predicted
    after observing 624 outputs.
    """
    print("--- Initiating State Recovery Attack on Standard PRNG ---")
    cracker = RandCrack()
    
    # Initialize standard PRNG with a random seed
    random.seed()
    
    # Attacker observes 624 32-bit integers to solve the linear matrix
    for _ in range(624):
        observed_value = random.getrandbits(32)
        cracker.submit(observed_value)
        
    print("[!] Matrix solved. Predicting next outputs...")
    
    success_count = 0
    test_samples = 10
    
    for _ in range(test_samples):
        predicted = cracker.predict_getrandbits(32)
        actual = random.getrandbits(32)
        if predicted == actual:
            success_count += 1
            
    accuracy = (success_count / test_samples) * 100.0
    print(f"--> PRNG Predictability Accuracy: {accuracy}%\n")

def attack_quey_qrng():
    """
    Demonstrates that Quey's Quantum Randomness is immune to state recovery
    because it lacks a deterministic mathematical state.
    """
    print("--- Initiating State Recovery Attack on Quey QRNG ---")
    cracker = RandCrack()
    quey = QueyRandom(api_key=QUEY_API_KEY)
    
    print("Fetching 624 physical quantum integers from Cloud Ocean...")
    
    # OPTIMIZATION: Fetch all needed bytes in ONE single network request
    # 624 integers * 4 bytes each = 2496 bytes
    bulk_entropy = quey.get_bytes(624 * 4)
    
    # Attacker attempts to feed true random quantum bits into the cracker
    for i in range(624):
        # Slice 4 bytes from our bulk payload
        chunk = bulk_entropy[i*4 : (i+1)*4]
        observed_value = int.from_bytes(chunk, byteorder='big')
        cracker.submit(observed_value)
        
    print("[!] Attempting to predict next quantum outputs...")
    
    success_count = 0
    test_samples = 10
    
    # Fetch verification bytes in one single request too
    verification_entropy = quey.get_bytes(test_samples * 4)
    
    for i in range(test_samples):
        try:
            predicted = cracker.predict_getrandbits(32)
        except Exception:
            # Cracker fails internally on true randomness
            predicted = None 
            
        chunk = verification_entropy[i*4 : (i+1)*4]
        actual = int.from_bytes(chunk, byteorder='big')
        
        if predicted == actual:
            success_count += 1
            
    accuracy = (success_count / test_samples) * 100.0
    print(f"--> Quey QRNG Predictability Accuracy: {accuracy}%\n")
if __name__ == "__main__":
    print("SECURITY BENCHMARK: QUEY VS MERSENNE TWISTER\n")
    hack_standard_prng()
    attack_quey_qrng()
