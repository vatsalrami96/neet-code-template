"""Monotonic stack. Invariant: stack holds indices whose values are strictly increasing (for next-greater).
When a new value pops something, the new value is that element's next greater. Each index pushed/popped once -> O(n).
Bug: comparing values but storing values instead of indices (you usually need the distance)."""

def next_greater(a):
    res = [-1] * len(a)
    st = []                          # indices, values increasing bottom->top
    for i, x in enumerate(a):
        while st and a[st[-1]] < x:
            res[st.pop()] = i        # i is the next greater index for the popped one
        st.append(i)
    return res

# Daily Temperatures: res[j] = i - j.
# Largest Rectangle in Histogram: increasing stack of heights; on pop, width = i - st[-1] - 1 (append a 0 sentinel).
# Sliding Window Maximum: monotonic DEQUE (decreasing), pop front when it leaves the window.
