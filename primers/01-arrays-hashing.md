# Arrays & Hashing

## Before you start
- Python `dict` and `set`: O(1) average insert, lookup, delete. Keys must be hashable (tuples yes, lists no).
- `sorted()` and `list.sort(key=...)` are O(n log n) and stable.
- You can index, slice, and iterate with `enumerate` without thinking about it.

## The pattern and its templates
**Trade space for time with a hash map.** The invariant: *after processing index i, the map holds everything you
need to know about indices 0..i to answer the question at i.* You decide what "everything you need" is: seen values,
counts, first index, running prefix sum.

Three shapes:
1. **Seen-set.** "Have I encountered X before?" Contains Duplicate, Two Sum (map value to index, look up
   `target - x` before inserting x).
2. **Counter / canonical key.** Group things that are "the same" under some key. Valid Anagram (count letters),
   Group Anagrams (key = sorted string or 26-count tuple), Top K Frequent (Counter then bucket by count).
3. **Prefix / suffix products or sums.** Product of Array Except Self: left pass then right pass, no division.
   Longest Consecutive Sequence: put everything in a set, only start counting from numbers with no `x - 1`.

## How to recognize it
"Find a pair / duplicate / anagram", "group by", "count frequency", "k most frequent", "in O(n)", "without
sorting", "contiguous range". If the naive solution is a double loop over the array, the map is usually the fix.

## Classic mistakes
- Inserting into the map *before* checking (Two Sum returns the same index twice).
- Using a list as a dict key. Use `tuple(counts)` or `''.join(sorted(s))`.
- Sorting when a Counter would do, turning O(n) into O(n log n).
- Longest Consecutive Sequence: counting from every number instead of only sequence starts; that is O(n^2) in the worst case.
- Forgetting the empty input and the single-element input.

## Complexity you should expect
O(n) time, O(n) space for almost everything here. If you wrote O(n^2), there is a map you missed. If you wrote
O(n log n), ask whether the sort was necessary.

## Warm-ups
1. Given `s = "aabbbc"`, produce a dict of letter counts two different ways, one with a plain dict and one with
   the standard library, and say which is O(n).
2. In one sentence: why can't a `list` be a `dict` key, and what do you use instead for a 26-letter count?

## The problems, in order
| # | Problem | Teaches | Note |
|---|---|---|---|
| 1 | Contains Duplicate | seen-set | |
| 2 | Valid Anagram | counting key | prerequisite for Group Anagrams |
| 3 | Two Sum | value-to-index map, check before insert | prerequisite for Two Sum II and 3Sum |
| 4 | Group Anagrams | canonical key | |
| 5 | Top K Frequent Elements | Counter + bucket sort (O(n)) or heap (O(n log k)) | know both |
| 6 | Encode and Decode Strings | length-prefix encoding | design flavor, Premium on LeetCode |
| 7 | Product of Array Except Self | prefix and suffix passes | no division |
| 8 | Valid Sudoku | multiple seen-sets keyed by (row), (col), (box) | |
| 9 | Longest Consecutive Sequence | set + start-of-sequence check | the O(n) argument is the interview |
