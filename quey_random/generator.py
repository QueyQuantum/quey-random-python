import requests
import os
import math
import itertools
import bisect
import logging

# Configure minimal logging for SDK events
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [QUEY-SDK] %(levelname)s - %(message)s')

class QueyRandom:
    """
    Core generator pulling true quantum entropy from a Quey Node.
    Features an internal Entropy Pool to minimize network latency.
    Supports both local hardware nodes (Lab Mode) and remote SaaS (Cloud Mode).
    """
    def __init__(self, host='localhost', port=5000, key_file='quey_api.key', api_token=None, pool_size=4096):
        self.host = host
        self.port = port
        self.key_file = key_file
        self.api_token = api_token
        
        # --- ENTROPY POOL CONFIGURATION ---
        self.pool_size = pool_size
        self._entropy_pool = bytearray()
        
        # --- BOX-MULLER STATE ---
        self._has_spare_gauss = False
        self._spare_gauss = None

        # --- ROUTING & AUTHENTICATION ---
        self.mode = "cloud" if self.api_token else "lab"
        self.base_url = self._build_url()
        self.auth_headers = self._build_auth_headers()

    def _build_url(self):
        """Routes the requests to the correct server based on the mode."""
        if self.mode == "cloud":
            # Updated to your live Firebase SaaS endpoint
            return "https://us-central1-quey-deb85.cloudfunctions.net/getQuantumEntropy"
        return f"http://{self.host}:{self.port}/key"

    def _build_auth_headers(self):
        """Constructs the appropriate security headers."""
        if self.mode == "cloud":
            # Updated to match the backend 'x-quey-key' requirement
            return {'x-quey-key': self.api_token}
        
        local_key = self._load_local_key()
        return {'X-API-Key': local_key} if local_key else {}

    def _load_local_key(self):
        """Safely loads the hardware API key from standard locations."""
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, 'r') as f:
                    return f.read().strip()
            fallback = os.path.expanduser(f"~/Quey/{self.key_file}")
            if os.path.exists(fallback):
                 with open(fallback, 'r') as f:
                    return f.read().strip()
            return None
        except Exception:
            return None

    def _fill_pool(self, min_bytes_needed):
        """Fetches a large chunk of quantum entropy to minimize network overhead."""
        request_size = max(self.pool_size, min_bytes_needed)
        try:
            response = requests.get(self.base_url, headers=self.auth_headers, params={'size': request_size}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Cloud returns 'entropy_hex', Edge Node returns 'key'
                hex_data = data.get('entropy_hex') or data.get('key')
                
                if hex_data:
                    # Convert hex string to bytes and add to the RAM pool
                    self._entropy_pool.extend(bytes.fromhex(hex_data))
                    return
            elif response.status_code == 403:
                logging.error("Quota Exceeded. Please check your billing.")
                raise PermissionError("Quota Exceeded")
            elif response.status_code == 401:
                logging.error(f"Unauthorized. Check credentials for {self.mode.upper()} mode.")
                raise PermissionError("Invalid API Key")
            else:
                logging.error(f"Server error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error: {e}")
            
        raise ConnectionError(f"Quey Node unavailable or unauthorized in {self.mode.upper()} mode.")

    def _get_raw_hex(self, size_bytes=32):
        """Retrieves bytes from the local entropy pool, refilling it if necessary."""
        # 1. Check if the pool has enough bytes, if not, fill it
        if len(self._entropy_pool) < size_bytes:
            self._fill_pool(size_bytes)
            
        # 2. Extract the required bytes from the beginning of the pool
        chunk = self._entropy_pool[:size_bytes]
        del self._entropy_pool[:size_bytes]
        
        # 3. Convert back to hex string for the math functions
        return chunk.hex()

    # --- CORE UNIFORM DISTRIBUTIONS ---

    def random(self):
        """Returns a true random float in the range [0.0, 1.0)."""
        hex_val = self._get_raw_hex(8)
        int_val = int(hex_val, 16)
        return int_val / (2**64)

    def randint(self, a, b):
        """Returns a true random integer in range [a, b]."""
        if a > b:
            raise ValueError("Empty range for randint")
        range_size = b - a + 1
        bytes_needed = math.ceil(range_size.bit_length() / 8)
        if bytes_needed == 0: bytes_needed = 1
        hex_val = self._get_raw_hex(bytes_needed)
        int_val = int(hex_val, 16)
        return a + (int_val % range_size)

    def choice(self, seq):
        """Chooses a true random element from a non-empty sequence."""
        if not seq: raise IndexError("Cannot choose from an empty sequence")
        return seq[self.randint(0, len(seq) - 1)]

    def choices(self, population, weights=None, k=1):
        """Return a k sized list of elements chosen from the population with optional weights."""
        if weights is None:
            return [self.choice(population) for _ in range(k)]
        
        if len(population) != len(weights):
            raise ValueError("The number of weights does not match the population")

        cum_weights = list(itertools.accumulate(weights))
        total = cum_weights[-1]
        
        return [population[bisect.bisect(cum_weights, self.random() * total)] for _ in range(k)]

    # --- SCIENTIFIC DISTRIBUTIONS ---

    def gauss(self, mu=0.0, sigma=1.0):
        """Gaussian distribution using the Box-Muller transform."""
        if self._has_spare_gauss:
            self._has_spare_gauss = False
            return mu + sigma * self._spare_gauss

        u1 = self.random()
        while u1 == 0.0: u1 = self.random()
        u2 = self.random()

        r = math.sqrt(-2.0 * math.log(u1))
        theta = 2.0 * math.pi * u2

        self._spare_gauss = r * math.sin(theta)
        self._has_spare_gauss = True

        return mu + sigma * (r * math.cos(theta))

    def expovariate(self, lambd):
        """Exponential distribution. lambd is 1.0 divided by the desired mean."""
        u = self.random()
        while u == 0.0: u = self.random()
        return -math.log(u) / lambd

    def poisson(self, lambd):
        """Poisson distribution (Knuth's algorithm). Good for photon counting."""
        L = math.exp(-lambd)
        k = 0
        p = 1.0
        while p > L:
            k += 1
            p *= self.random()
        return k - 1

    def complex_phase(self):
        """Returns a true random complex number on the unit circle (e^(i*theta))."""
        theta = 2.0 * math.pi * self.random()
        return complex(math.cos(theta), math.sin(theta))

# Global instance
_inst = QueyRandom()

random = _inst.random
randint = _inst.randint
choice = _inst.choice
choices = _inst.choices
gauss = _inst.gauss
expovariate = _inst.expovariate
poisson = _inst.poisson
complex_phase = _inst.complex_phase