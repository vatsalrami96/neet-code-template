"""Dijkstra and topological sort (Kahn). Two templates people fumble under pressure."""
import heapq
from collections import deque, defaultdict

def dijkstra(n, g, src):
    """g[u] = list of (v, w). Invariant: when a node is popped with dist d, d is final. Skip stale entries."""
    dist = [float('inf')] * n
    dist[src] = 0
    h = [(0, src)]
    while h:
        d, u = heapq.heappop(h)
        if d > dist[u]:
            continue                       # stale
        for v, w in g[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                heapq.heappush(h, (dist[v], v))
    return dist

def topo_order(n, edges):
    """Kahn's algorithm. If the result has fewer than n nodes, there is a cycle (Course Schedule)."""
    g = defaultdict(list)
    indeg = [0] * n
    for u, v in edges:                     # u -> v (u before v)
        g[u].append(v); indeg[v] += 1
    q = deque(i for i in range(n) if indeg[i] == 0)
    order = []
    while q:
        u = q.popleft(); order.append(u)
        for v in g[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return order if len(order) == n else None
