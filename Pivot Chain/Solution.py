import sys
import heapq

input = sys.stdin.readline

# read first line
n, m, start, end = input().split()
n = int(n)
m = int(m)

graph = {}
for _ in range(m):
    a, b, c = input().split()
    c = int(c)
    if a not in graph:
        graph[a] = []
    graph[a].append((b, c))

# Dijkstra
INF = 10**18
dist = {}
pq = [(0, start)]
dist[start] = 0

while pq:
    risk, node = heapq.heappop(pq)
    if node == end:
        print(risk)
        sys.exit(0)
    if risk > dist[node]:
        continue
    for nei, cost in graph.get(node, []):
        newrisk = risk + cost
        if nei not in dist or newrisk < dist[nei]:
            dist[nei] = newrisk
            heapq.heappush(pq, (newrisk, nei))

# if no path found
print(-1)