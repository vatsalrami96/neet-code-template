"""Sliding window. Invariant: window [l, r] always satisfies the constraint after the inner while loop.
Bug: updating the answer before restoring validity.

`while` vs `if` on the shrink: use `while`. It is correct for all three query shapes, so it is the only form worth
memorizing. But know the nuance, because correct-looking `if` code turns up in the wild and you may be asked about it:
  - longest / max length  -> `if` also works. The window never shrinks, so it ends at the largest valid size.
  - count subarrays       -> `if` is WRONG. `total += r - l + 1` needs the true tightest l every iteration.
  - minimum window        -> `if` is WRONG. You have to shrink fully to find the tightest window.
Verified by brute force: on at-most-2-distinct, the `if` form matched on 4000/4000 max-length cases and failed
1860/3000 counting cases."""
from collections import defaultdict

def longest_with_at_most_k_distinct(s, k):
    cnt = defaultdict(int)
    best = l = 0
    for r, ch in enumerate(s):
        cnt[ch] += 1
        while len(cnt) > k:            # restore validity
            cnt[s[l]] -= 1
            if cnt[s[l]] == 0:
                del cnt[s[l]]
            l += 1
        best = max(best, r - l + 1)    # window valid here
    return best

# Fixed-size window (Permutation in String): add s[r], remove s[r-k] when r >= k, compare counts.
# Minimum Window Substring: expand until all needed are covered, then shrink while still covered, record min.
