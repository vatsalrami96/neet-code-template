"""DFS on an adjacency list, iterative and recursive. Invariant: every node is visited at most once.
Bug: recursion depth on 10^5 nodes; forgetting to add both directions for undirected edges."""
from collections import defaultdict

def build(n, edges, directed=False):
    g = defaultdict(list)
    for u, v in edges:
        g[u].append(v)
        if not directed:
            g[v].append(u)
    return g

def dfs_iter(g, start):
    seen = {start}
    stack = [start]
    while stack:
        u = stack.pop()
        for v in g[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen

def count_components(n, g):
    seen = set()
    comps = 0
    for s in range(n):
        if s not in seen:
            comps += 1
            seen |= dfs_iter(g, s)
    return comps

# Cycle detection in a DIRECTED graph needs three colors: 0 unvisited, 1 on the current path, 2 done.
def has_cycle(n, g):
    color = [0] * n
    def visit(u):
        color[u] = 1
        for v in g[u]:
            if color[v] == 1 or (color[v] == 0 and visit(v)):
                return True
        color[u] = 2
        return False
    return any(color[u] == 0 and visit(u) for u in range(n))
