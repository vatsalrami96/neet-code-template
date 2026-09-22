"""Top-k with a heap. Invariant: a min-heap of size k holds the k largest seen so far; its root is the k-th largest.
O(n log k). Bug: using a max-heap of size n (O(n log n)), or forgetting Python's heap is a min-heap."""
import heapq

def k_largest(nums, k):
    h = []
    for x in nums:
        heapq.heappush(h, x)
        if len(h) > k:
            heapq.heappop(h)
    return h                      # h[0] is the k-th largest

def k_closest(points, k):
    h = []
    for x, y in points:
        heapq.heappush(h, (-(x * x + y * y), x, y))   # max-heap by distance via negation
        if len(h) > k:
            heapq.heappop(h)
    return [(x, y) for _, x, y in h]

# Two heaps (Find Median from Data Stream): max-heap for the lower half, min-heap for the upper, rebalance so sizes differ by <= 1.
# Lazy deletion: push (key, item); on pop, skip entries whose key is stale.
