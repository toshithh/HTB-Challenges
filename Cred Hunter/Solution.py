import re


n = int(input())
potential_passwords = []
creds = {}

email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-z0-9.-]+\.[a-zA-Z]{2,}$'

for i in range(n):
    _line = input()
    if (re.match(email_pattern, _line)):  
        creds[_line] = []
    else:    potential_passwords.append(_line)

for x in creds.keys():
    i = 0
    while i<len(potential_passwords):
        if x.split('@')[0][:-1] in potential_passwords[i]:
            creds[x].append(potential_passwords[i])
        i+=1

_tmp = list(creds.keys())
_tmp.sort()
for x in _tmp:
    creds[x].sort()
    for y in creds[x]:
        print(x, y)
