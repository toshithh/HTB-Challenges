import socket, sys, time
from math import prod

HOST = '94.237.49.23'
PORT = 56593
TIMEOUT = 5.0
MOD = 257

# ----------------- network helpers -----------------
def recv_until(sock, delim=b'> ', timeout=5.0):
    sock.settimeout(timeout)
    data = b''
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
            if delim in data:
                break
    except socket.timeout:
        pass
    finally:
        sock.settimeout(None)
    return data

def sendline(sock, s: bytes):
    # send bytes followed by newline
    sock.sendall(s + b'\n')

def read_ciphertext_hex_from_output(txt: str):
    # try to find 32+ hex chars in the server line(s)
    import re
    # remove common escapes like leading '\x00' text fragments
    # find hex groups (at least 32 hex chars)
    m = re.search(r'([0-9a-fA-F]{32,})', txt)
    if not m:
        return None
    return m.group(1).strip()

# ----------------- math helpers (mod 257) -----------------
def modinv(a):
    a %= MOD
    if a == 0: raise ZeroDivisionError("no inverse for 0")
    return pow(a, MOD-2, MOD)

def mat_add(A,B):
    return [[(A[i][j]+B[i][j])%MOD for j in range(4)] for i in range(4)]
def mat_sub(A,B):
    return [[(A[i][j]-B[i][j])%MOD for j in range(4)] for i in range(4)]
def mat_mul(A,B):
    C = [[0]*4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            s=0
            for k in range(4):
                s=(s + A[i][k]*B[k][j])%MOD
            C[i][j]=s
    return C
def outer(u,v):
    return [[(u[i]*v[j])%MOD for j in range(4)] for i in range(4)]

def invert_matrix(A):
    n=4
    M = [ [A[i][j]%MOD for j in range(n)] + [1 if i==j else 0 for j in range(n)] for i in range(n) ]
    for col in range(n):
        pivot=None
        for r in range(col,n):
            if M[r][col] % MOD != 0:
                pivot=r; break
        if pivot is None:
            raise ValueError("singular")
        if pivot!=col:
            M[col], M[pivot] = M[pivot], M[col]
        invp = modinv(M[col][col])
        M[col] = [(x*invp)%MOD for x in M[col]]
        for r in range(n):
            if r==col: continue
            fac = M[r][col]
            if fac==0: continue
            M[r] = [ (M[r][c] - fac * M[col][c]) % MOD for c in range(2*n) ]
    inv = [[M[i][n+j] for j in range(n)] for i in range(n)]
    return inv

def S_inv(x):
    return pow(x % MOD, 171, MOD)

def parse_ct_block_hex32(h):
    if len(h) < 32:
        raise ValueError("block hex too short")
    vals = [int(h[i:i+2],16) for i in range(0,32,2)]
    M = [[0]*4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            M[i][j] = vals[4*i + j] % MOD
    return M

def matrix_to_bytes(M):
    out = bytearray()
    for i in range(4):
        for j in range(4):
            v = M[i][j] % MOD
            out.append(v % 256)
    return bytes(out)

def factor_rank1(A):
    a0=b0=None
    for i in range(4):
        for j in range(4):
            if A[i][j] % MOD != 0:
                a0=i; b0=j; break
        if a0 is not None: break
    if a0 is None:
        return [0,0,0,0],[0,0,0,0]
    u = [A[r][b0]%MOD for r in range(4)]
    ua0 = u[a0]
    if ua0 == 0:
        raise ZeroDivisionError("pivot zero")
    inv = modinv(ua0)
    v = [ (A[a0][c] * inv) % MOD for c in range(4)]
    return u,v

# ----------------- service interaction -----------------
def get_cipher_for_block(sock, block_bytes):
    # at menu prompt: send option 1, then send block (raw) as a line
    # (the server reads input().strip(), sending binary nulls is okay as long as newline ends input)
    # wait prompt
    data = recv_until(sock, delim=b'> ')
    # send '1'
    sendline(sock, b'1')
    # server will prompt "Enter message (raw text):"
    data = recv_until(sock, delim=b':')  # stop at colon probably
    # send the raw block (we send bytes and newline)
    sendline(sock, block_bytes)
    # read until next prompt or until it prints 'Ciphertext'
    data = recv_until(sock, delim=b'\n')
    # read more - server prints "Ciphertext (hex): ..." then newline then menu again, so read until next prompt
    data += recv_until(sock, delim=b'> ')
    txt = data.decode('latin1', errors='ignore')
    # extract hex
    hx = read_ciphertext_hex_from_output(txt)
    return hx, txt

def get_blueprint_cipher(sock):
    data = recv_until(sock, delim=b'> ')
    sendline(sock, b'2')
    data = recv_until(sock, delim=b'> ')
    txt = data.decode('latin1', errors='ignore')
    hx = read_ciphertext_hex_from_output(txt)
    return hx, txt

# ----------------- main exploit flow -----------------
def main():
    print(f"[+] connecting to {HOST}:{PORT}")
    s = socket.create_connection((HOST, PORT), timeout=TIMEOUT)
    try:
        # build blocks
        zero_block = bytes([0]*16)
        diag_blocks = []
        for i in range(4):
            b = bytearray(16)
            b[5*i] = 1
            diag_blocks.append(bytes(b))
        row0_blocks = []
        for j in range(1,4):
            b = bytearray(16)
            b[j] = 1
            row0_blocks.append(bytes(b))

        print("[*] fetching encryption of zero block...")
        h_zero, raw_zero = get_cipher_for_block(s, zero_block)
        if not h_zero:
            print("[-] failed to obtain zero block ciphertext; server output:")
            print(raw_zero)
            return
        print("[+] zero block ct:", h_zero[:64])

        A_diag = []
        for i,blk in enumerate(diag_blocks):
            print(f"[*] fetching diag block {i} ...")
            h, txt = get_cipher_for_block(s, blk)
            if not h:
                print("[-] failed diag", i); print(txt); return
            print("[+] diag ct:", h[:64])
            A_diag.append(parse_ct_block_hex32(h))

        A_row0 = []
        for j,blk in enumerate(row0_blocks, start=1):
            print(f"[*] fetching row0 block index {j} ...")
            h, txt = get_cipher_for_block(s, blk)
            if not h:
                print("[-] failed row0", j); print(txt); return
            print("[+] row0 ct:", h[:64])
            A_row0.append(parse_ct_block_hex32(h))

        print("[*] fetching blueprint (option 2)...")
        target_hex, ttxt = get_blueprint_cipher(s)
        if not target_hex:
            print("[-] failed to fetch blueprint ciphertext. Server output:\n", ttxt)
            return
        print("[+] blueprint ct length:", len(target_hex), "hex chars")
        # parse matrices
        T = parse_ct_block_hex32(h_zero)
        A_sub = [ mat_sub(A_diag[i], T) for i in range(4) ]
        B_sub = [ mat_sub(A_row0[i], T) for i in range(3) ]

        # factor rank-1
        u_list=[]; v_list=[]
        for i in range(4):
            u,v = factor_rank1(A_sub[i])
            u_list.append(u); v_list.append(v)

        # compute alphas (alpha_0 = 1)
        alpha = [1,1,1,1]
        for j in range(1,4):
            Aj = B_sub[j-1]
            found=False
            for a in range(4):
                for b in range(4):
                    denom = (u_list[0][a] * v_list[j][b]) % MOD
                    if denom != 0:
                        numer = Aj[a][b] % MOD
                        ratio = (numer * modinv(denom)) % MOD
                        alpha[j] = modinv(ratio) % MOD
                        found=True; break
                if found: break
            if not found:
                print("[-] could not resolve alpha for column", j)
                return

        # assemble K and L
        K = [[0]*4 for _ in range(4)]
        L = [[0]*4 for _ in range(4)]
        for i in range(4):
            kc = [ (alpha[i] * u_list[i][r]) % MOD for r in range(4) ]
            for r in range(4): K[r][i] = kc[r]
            inva = modinv(alpha[i])
            lr = [ (v_list[i][c] * inva) % MOD for c in range(4) ]
            for c in range(4): L[i][c] = lr[c]

        # decrypt target (may be multiple blocks)
        th = target_hex
        if len(th) % 32 != 0:
            th = th[: (len(th)//32)*32 ]
        blocks = [ th[i:i+32] for i in range(0,len(th),32) ]
        Kinv = invert_matrix(K); Linv = invert_matrix(L)
        plain = b''
        for bhex in blocks:
            Cmat = parse_ct_block_hex32(bhex)
            Amat = mat_sub(Cmat, T)
            X = mat_mul(mat_mul(Kinv, Amat), Linv)
            Mmat = [[ S_inv(X[i][j]) for j in range(4)] for i in range(4)]
            blk = matrix_to_bytes(Mmat)
            plain += blk

        # strip PKCS#7 padding
        if not plain:
            print("[-] no plaintext recovered")
            return
        padlen = plain[-1]
        if 1 <= padlen <= 16:
            maybe = plain[:-padlen]
        else:
            maybe = plain
        print("\n[+] Recovered plaintext bytes (raw):", plain)
        try:
            print("\n[+] Recovered (utf-8):\n", maybe.decode())
        except:
            print("\n[+] Recovered (bytes):", maybe)

    finally:
        s.close()

if __name__ == '__main__':
    main()
