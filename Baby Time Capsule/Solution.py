import socket
import json
from Crypto.Util.number import long_to_bytes

host = "94.237.57.1"
port = 58305

def fetch_one_capsule():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.recv(8096)  # Receive the initial prompt
    sock.sendall(b'Y\n')
    data = b''
    while True:
        chunk = sock.recv(1024)
        if not chunk:
            break
        data += chunk
        if b'\n' in data:
            break
    sock.close()
    lines = data.split(b'\n')
    json_line = lines[0]
    try:
        capsule = json.loads(json_line.decode())
        return capsule
    except json.JSONDecodeError:
        print("Error decoding JSON:", json_line)
        return None

def extended_gcd(a, b):
    if b == 0:
        return (1, 0, a)
    else:
        x0, y0, g = extended_gcd(b, a % b)
        x = y0
        y = x0 - (a // b) * y0
        return (x, y, g)

def crt(residues, moduli):
    n = len(residues)
    if n != len(moduli):
        raise ValueError("Number of residues and moduli must be the same")
    
    # Compute the product of all moduli
    N = 1
    for m in moduli:
        N *= m
        
    x = 0
    for i in range(n):
        a = residues[i]
        n_i = moduli[i]
        m_i = N // n_i
        inv, _, g = extended_gcd(m_i, n_i)
        if g != 1:
            raise ValueError("Moduli are not coprime")
        x += a * m_i * inv
    return x % N, N

def iroot(x, n):
    low, high = 1, x
    while low <= high:
        mid = (low + high) // 2
        mid_power = pow(mid, n)
        if mid_power < x:
            low = mid + 1
        elif mid_power > x:
            high = mid - 1
        else:
            return mid
    return low - 1

# Collect 5 capsules
capsules = []
for i in range(5):
    cap = fetch_one_capsule()
    if cap is None:
        print("Failed to fetch capsule", i+1)
        exit(1)
    capsules.append(cap)
    print("Fetched capsule", i+1)

moduli = []
residues = []
for cap in capsules:
    n_hex = cap['pubkey'][0]
    c_hex = cap['time_capsule']
    n = int(n_hex, 16)
    c = int(c_hex, 16)
    moduli.append(n)
    residues.append(c)

x, N = crt(residues, moduli)
m = iroot(x, 5)
if pow(m, 5) == x:
    flag = long_to_bytes(m)
    print("Flag:", flag.decode())
else:
    print("Failed to recover flag. Try more capsules.")