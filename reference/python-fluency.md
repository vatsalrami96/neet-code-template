# Python fluency for interviews

The standard-library pieces that save minutes, and the gotchas that lose them.

## Collections
```python
from collections import defaultdict, Counter, deque, OrderedDict
g = defaultdict(list)            # adjacency list without key checks
c = Counter(s)                   # counts; c[x] is 0 for missing keys, WITHOUT inserting x
dq = deque()                     # append, appendleft, pop, popleft all O(1); use for BFS and sliding windows
```
```python
c.most_common(k)     # -> list of (element, count) TUPLES, descending by count, ties in insertion order
c.most_common()      # -> all of them, sorted
[x for x, _ in c.most_common(k)]   # bare elements; this is Top K Frequent in one line
```
Reading a missing key differs: `c["z"]` on a `Counter` returns 0 and leaves the Counter alone, but `d["z"]` on a
`defaultdict(int)` **inserts** `z: 0`. That shows up later in `len(d)`, iteration, and `==`. Probe a `Counter`, build a
`defaultdict`.

`list.pop(0)` is O(n). Never use it for a queue.

## Heaps
```python
import heapq
heapq.heapify(a)                 # O(n), min-heap in place
heapq.heappush(h, (key, item)); heapq.heappop(h)
heapq.nlargest(k, a); heapq.nsmallest(k, a, key=...)   # -> list of the k ELEMENTS themselves,
                                                       # not (value, count) tuples like most_common
# max-heap: push -x. Tuples compare element by element; add an index to break ties if items aren't comparable.
```

## Binary search
```python
import bisect
bisect.bisect_left(a, x)   # first index i with a[i] >= x
bisect.bisect_right(a, x)  # first index i with a[i] > x
bisect.insort(a, x)        # O(n) insert, fine for small n
```
Hand-written template: `lo, hi = 0, n` (hi exclusive), `while lo < hi: mid = (lo + hi) // 2`, move `lo = mid + 1`
or `hi = mid`. Answer is `lo`. For "search on answer", the predicate must be monotonic.

## Sorting
```python
a.sort(key=lambda x: (x[0], -x[1]))   # stable; tuple keys for multi-level
sorted(d.items(), key=lambda kv: kv[1], reverse=True)
```

## Strings
```python
"".join(parts)             # never s += c in a loop for large n
s.split(), s.strip(), s.isalnum(), s.lower(), ord(c) - ord('a')
```
Strings are immutable. Build a list of chars, join at the end.

## Iteration idioms
```python
for i, x in enumerate(a): ...
for a_i, b_i in zip(a, b): ...
for r in range(n - 1, -1, -1): ...      # reverse
any(...), all(...), sum(x for x in a if ...)
```

## Recursion
```python
import sys; sys.setrecursionlimit(10**6)   # DFS on 10^5 nodes will hit the default 1000 otherwise
```
Prefer iterative DFS with an explicit stack for deep graphs. Say this out loud in an interview.

## Memoization
```python
from functools import lru_cache
@lru_cache(None)
def f(i, j): ...
```
Arguments must be hashable (tuples, not lists). Clear with `f.cache_clear()` between test cases.

## Sets and dicts
- `dict` keeps insertion order (3.7+). `OrderedDict.move_to_end` is what makes LRU Cache clean.
- `frozenset` for a hashable set. Tuples for hashable coordinates: `seen.add((r, c))`.
- `d.get(k, default)`, `d.setdefault(k, [])`, `d.items()`.

## Gotchas
- `[[0] * m] * n` makes n references to the same row. Use `[[0] * m for _ in range(n)]`.
- `-7 // 2 == -4` and `-7 % 2 == 1`. For truncation toward zero use `int(-7 / 2)`.
- Default mutable arguments (`def f(a=[])`) persist across calls.
- `is` vs `==`: use `==` for values, `is None` for None.
- Slicing copies: `a[i:j]` is O(j - i). Inside a loop that is a hidden O(n^2).
- `math.inf` for infinity; `float('inf')` works too.
- `divmod(a, b)` returns both quotient and remainder.

## Cost table
| Structure | Access | Search | Insert | Delete | Worst case | Notes |
|---|---|---|---|---|---|---|
| list | O(1) | O(n) | O(1) end, O(n) middle | O(1) end, O(n) middle | append is O(1) *amortized* | `in` is O(n) |
| dict / set | O(1) avg | O(1) avg | O(1) avg | O(1) avg | **O(n) per op** on hash collisions | keys must be hashable |
| deque | O(n) middle | O(n) | O(1) both ends | O(1) both ends | same | |
| heapq | O(1) min | O(n) | O(log n) | O(log n) pop min | same | no decrease-key; push a new entry and skip stale ones |
| sorted list + bisect | O(1) | O(log n) | O(n) | O(n) | same | fine up to ~10^4 inserts |

Three worst cases worth being able to say out loud:

- **`list.append` is O(1) amortized, not O(1).** The list reallocates when it fills, so one append in n is O(n). Over n
  appends it averages to O(1). Say "amortized" and you have answered the follow-up before it is asked.
- **`dict` and `set` are O(1) only if hashing behaves.** Every average case in that row assumes collisions are rare.
  Adversarial or degenerate keys make every operation O(n). For interviews: state O(1) average, and note the
  assumption if the interviewer is probing.
- **A `dict`'s worst-case n is the largest it ever got, not its current size.** Copy and iteration stay slow after you
  delete keys, because the table does not shrink.

Slicing is the one that silently costs you: `a[i:j]` is O(j - i), so a slice inside a loop is a hidden O(n^2).
