"""Backtracking. Invariant: path is a valid partial answer; every choice made is undone before the next.
Bug: appending `path` itself instead of a copy; forgetting the undo; skipping duplicates incorrectly."""

def subsets(nums):
    out, path = [], []
    def go(i):
        out.append(path[:])            # copy
        for j in range(i, len(nums)):
            if j > i and nums[j] == nums[j - 1]:   # skip duplicates (requires sorted input)
                continue
            path.append(nums[j])
            go(j + 1)
            path.pop()                 # undo
    nums.sort()
    go(0)
    return out

def permutations(nums):
    out, path, used = [], [], [False] * len(nums)
    def go():
        if len(path) == len(nums):
            out.append(path[:]); return
        for i in range(len(nums)):
            if used[i]:
                continue
            used[i] = True; path.append(nums[i])
            go()
            path.pop(); used[i] = False
    go()
    return out

# Combination Sum: pass `i` (not i+1) to allow reuse. Prune when remaining < 0.
