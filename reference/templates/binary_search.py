"""Binary search. Invariant: answer is in [lo, hi). Loop ends with lo == hi == first index where pred is true.
Bug: using hi = mid - 1 with an exclusive hi, or lo <= hi with an exclusive hi."""

def first_true(lo, hi, pred):
    """Smallest x in [lo, hi) with pred(x) True; pred must be False...False True...True."""
    while lo < hi:
        mid = (lo + hi) // 2
        if pred(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo

def search(a, target):
    i = first_true(0, len(a), lambda m: a[m] >= target)
    return i if i < len(a) and a[i] == target else -1

# "Binary search on the answer": pred(x) = "can we do it with capacity x". Monotonic in x -> first_true.
