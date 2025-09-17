from pwnlib.util.fiddling import unhex, xor
eb = bytes.fromhex('134af6e1297bc4a96f6a87fe046684e8047084ee046d84c5282dd7ef292dc9')
key = xor(eb, b'HTB{')[:4]
print(xor(eb, key).decode())