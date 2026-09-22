# Edge-case checklist

Run this before you say "done", and again in step 7 of the process. `sync` asks which of these you checked.

## Always
- Empty input: `[]`, `""`, `None`, empty tree, graph with no edges
- Single element
- Two elements (the smallest case where "pairs" and "adjacent" mean something)
- All elements identical
- Already sorted, reverse sorted
- Maximum size (does your recursion depth or memory survive n = 10^5?)

## Numbers
- Zero, negative numbers, mixed signs
- Overflow is not a Python problem, but the *interviewer's* language may have it; mention it
- Integer division and modulo with negatives (`-7 // 2 == -4` in Python)
- Duplicates when the problem says "distinct" or doesn't

## Strings
- Case sensitivity, spaces, punctuation
- Unicode is usually out of scope; say so
- Single character, all same character

## Arrays and matrices
- k larger than n, k = 0, k = n
- 1 x n and n x 1 matrices
- Target not present, target at first or last index

## Linked lists
- Head is None, single node, two nodes
- Cycle present when not expected, or the whole list is a cycle
- Removing the head

## Trees
- Root only, skewed (a linked list in disguise), duplicate values
- Negative values when computing path sums

## Graphs
- Disconnected components, self-loops, parallel edges
- Directed vs undirected: did you add both edges?
- Node ids not 0..n-1

## Intervals
- Touching intervals `[1,2],[2,3]`: is that an overlap? Ask
- Single interval, fully nested interval

## Output
- Order required? Stable? Return indices or values?
- Return type when there is no answer: -1, empty list, None, or an exception?
