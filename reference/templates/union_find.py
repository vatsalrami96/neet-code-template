"""Union-Find with path compression and union by size. Near O(1) per op.
Invariant: parent[x] == x iff x is a root. Bug: forgetting to compress, or unioning roots' sizes wrong."""

class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.count = n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]   # path halving
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False                 # already connected -> this edge is redundant / makes a cycle
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.count -= 1
        return True

# Graph Valid Tree: n-1 edges AND union never returns False.
