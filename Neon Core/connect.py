import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
Host = '94.237.49.23'
Port = 56593
s.connect((Host, Port))

try:
    while 1:
        msg = s.recv(8096)
        if not msg:
            print('Connection Closed by server')
            break
        print(msg.decode(), end='')
        time.sleep(0.1)
        s.sendall((input(" ")+'\n').encode())
        time.sleep(0.1)
except:
    s.close()