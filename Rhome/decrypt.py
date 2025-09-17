import socket
from Crypto.Util.number import isPrime, long_to_bytes
from math import gcd
from random import randint
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import re

def pollard_rho(n):
    if n == 1:
        return n
    if n % 2 == 0:
        return 2
    x = randint(2, n-2)
    y = x
    c = randint(1, n-1)
    d = 1
    f = lambda x: (x*x + c) % n
    while d == 1:
        x = f(x)
        y = f(f(y))
        d = gcd(abs(x-y), n)
        if d == n:
            break
    return d

def get_q(p):
    n = (p-1) // 2
    d = pollard_rho(n)
    while d == n or d == 1:
        d = pollard_rho(n)
    q1 = d
    q2 = n // d
    if q1.bit_length() == 42 and isPrime(q1):
        return q1
    elif q2.bit_length() == 42 and isPrime(q2):
        return q2
    else:
        raise ValueError("Could not find q from p")

def bsgs(g, A, p, order):
    m = int(order**0.5) + 1
    baby = {}
    current = 1
    for j in range(m):
        baby[current] = j
        current = (current * g) % p
    gm = pow(g, -m, p)
    temp = A
    for i in range(m):
        if temp in baby:
            j = baby[temp]
            return i * m + j
        temp = (temp * gm) % p
    raise ValueError("BSGS failed to find discrete log")

def main():
    host = '94.237.122.241'  # Replace with actual host
    port = 44998        # Replace with actual port

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    
    data = s.recv(1024).decode()
    print(data)
    
    s.send(b'1\n')
    data = s.recv(1024).decode()
    print(data)
    
    match_p = re.search(r'p = (\d+)', data)
    match_g = re.search(r'g = (\d+)', data)
    match_A = re.search(r'A = (\d+)', data)
    match_B = re.search(r'B = (\d+)', data)
    if not (match_p and match_g and match_A and match_B):
        data += s.recv(1024).decode()
        match_p = re.search(r'p = (\d+)', data)
        match_g = re.search(r'g = (\d+)', data)
        match_A = re.search(r'A = (\d+)', data)
        match_B = re.search(r'B = (\d+)', data)
        if not (match_p and match_g and match_A and match_B):
            print("Failed to get parameters")
            return

    p = int(match_p.group(1))
    g = int(match_g.group(1))
    A = int(match_A.group(1))
    B = int(match_B.group(1))

    print("Got parameters")
    print("p =", p)
    print("g =", g)
    print("A =", A)
    print("B =", B)

    q = get_q(p)
    print("q =", q)

    if pow(g, q, p) != 1:
        print("Warning: g^q != 1 mod p")

    a_mod_q = bsgs(g, A, p, q)
    print("a mod q =", a_mod_q)

    ss = pow(B, a_mod_q, p)
    print("ss =", ss)

    s.send(b'3\n')
    data = s.recv(1024).decode()
    print(data)
    match_enc = re.search(r'encrypted = (\w+)', data)
    if not match_enc:
        data += s.recv(1024).decode()
        match_enc = re.search(r'encrypted = (\w+)', data)
        if not match_enc:
            print("Failed to get encrypted flag")
            return

    enc_hex = match_enc.group(1)
    enc_bytes = bytes.fromhex(enc_hex)

    key = sha256(long_to_bytes(ss)).digest()[:16]
    cipher = AES.new(key, AES.MODE_ECB)
    try:
        flag = unpad(cipher.decrypt(enc_bytes), 16)
        print("Flag:", flag.decode())
    except Exception as e:
        print("Decryption error:", e)

if __name__ == '__main__':
    main()