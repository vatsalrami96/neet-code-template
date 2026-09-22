"""BFS on a grid. Invariant: the queue holds cells at distance d then d+1; a cell is marked visited when ENQUEUED.
Bug: marking visited on dequeue (causes duplicates and blows up the queue)."""
from collections import deque

def bfs(grid, sr, sc):
    R, C = len(grid), len(grid[0])
    dist = [[-1] * C for _ in range(R)]
    q = deque([(sr, sc)])
    dist[sr][sc] = 0
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and grid[nr][nc] != '#' and dist[nr][nc] == -1:
                dist[nr][nc] = dist[r][c] + 1
                q.append((nr, nc))
    return dist

# Multi-source BFS (Rotting Oranges, Walls and Gates): seed the queue with ALL sources at distance 0.
