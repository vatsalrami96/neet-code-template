# The interview process, seven steps

This is the rubric. `sync` and `mock` score against it. Practice it on every problem until it is automatic.

| # | Step | What it sounds like | Time in a 45-min round |
|---|---|---|---|
| 1 | **Restate** | "So I'm given X and need to return Y. Y is defined as..." | 1 min |
| 2 | **Constraints** | "How big is n? Can values be negative? Duplicates? Empty input? Is the array sorted?" | 1 to 2 min |
| 3 | **Example** | Walk one small example by hand, write expected output. | 1 to 2 min |
| 4 | **Brute force + cost** | "The obvious way is ..., which is O(n^2). Can we do better?" | 1 to 2 min |
| 5 | **Approach** | Name the pattern, state the invariant, say the complexity before coding. Get a nod. | 3 to 5 min |
| 6 | **Code** | Talk while typing. Small helper functions. Meaningful names. | 15 to 20 min |
| 7 | **Test + complexity** | Dry-run the example through the code by hand, then an edge case. State final time and space. | 5 min |

## Constraints to complexity

Read the constraint, know the target before you think about the approach.

| n up to | Target | Typical tools |
|---|---|---|
| 10 to 12 | O(n!) or O(2^n · n) | backtracking, permutations |
| 20 to 25 | O(2^n) | bitmask, subsets |
| 100 | O(n^3) | triple loop, Floyd-Warshall |
| 1,000 to 5,000 | O(n^2) | 2-D DP, pairwise |
| 10^5 to 10^6 | O(n log n) or O(n) | sorting, heap, binary search, two pointers, sliding window, hash map |
| 10^8 or more | O(log n) or O(1) | binary search on answer, math |

## Trade-offs (the fifth element of every explain-back)

`sync` asks for five things: what the problem asks, the approach, why it is correct, time and space, and **one
trade-off**. The trade-off is the one people invent on the spot and get wrong, so here is the shape.

> "The alternative is **X**. X is better at **A**, but it costs **B**. I chose **Y** because here **B matters more** -
> given **constraint C**."

Three obligations, all required:

1. **Name a real alternative.** Something that actually solves the problem, not a strawman.
2. **Concede what it is better at.** If the alternative has no advantage, it is not a trade-off, it is just a worse
   solution.
3. **Say what decides it** - the constraint that makes your side win here.

**The test:** if the sentence never mentions anything other than what you built, it is not a trade-off. If nothing is
given up, it is not a trade-off.

### Not trade-offs

These all describe one solution, and all three have been graded `sloppy`:

- "We use a hash map to get O(n)." - restates the approach.
- "I used `#` as the delimiter but could have used `*`." - substitution with no consequence.
- "We avoid recomputing the product each time." - beats brute force, which is assumed. Beating brute force earns
  nothing; the interviewer already expects it.

### Axes worth scanning when nothing comes to mind

Time vs space · average vs worst case · preprocessing vs query cost · simplicity vs performance · generality vs
assumptions (sorted? bounded alphabet? fits in memory?) · **offline vs streaming**.

The last one is the Amazon favourite - it is the same list as the follow-ups under "Amazon specifics" below. When
stuck, ask: what breaks if the data arrives one item at a time?

### Worked examples

- **Top K Frequent** - "The alternative is a size-k heap: O(n log k) instead of my O(n), so asymptotically worse. But
  it uses O(k) space instead of O(n) and it works on a stream, which buckets cannot, because they need every count
  before the first answer. I chose buckets because n is bounded and it is all in memory."
- **Encode and Decode Strings** - "The alternative is escaping the delimiter inside the payload: no length prefix,
  fewer bytes. But then decode examines every character instead of jumping over the payload. I paid bytes to buy the
  jump."
- **Product of Array Except Self** - "The alternative is total product divided by each element: one pass, much
  simpler. But division is banned and it breaks on zeros. Prefix/suffix costs a second pass and care about ordering,
  and buys immunity to zeros."
- **Valid Sudoku** - "The alternative is three separate passes reusing one set: same O(n^2) time, but O(n) space
  instead of O(n^2). I chose one pass with 3n sets, trading space for a single traversal."

Each names the other approach, admits what it is better at, then decides. That is the whole move.

## Scoring (used by sync and mock)

Each step: 2 = done well unprompted, 1 = done after a nudge or partially, 0 = skipped.
Steps 1, 2, 5, and 7 are the ones interviewers weight most. A 14 is a strong round. Under 9 means process, not
knowledge, is the problem.

## Amazon specifics

- Coding rounds are 45 to 60 minutes and usually open with 15 to 20 minutes of Leadership Principles questions.
  Switching from a story to a problem is a skill; mocks rehearse it.
- The online assessment is two problems in about 70 minutes with long story-style statements. Read twice, extract
  the object, the query, and the constraint before anything else.
- Follow-ups are near certain: "what if the input is a stream", "what if it doesn't fit in memory", "can you do it
  without extra space". Have one alternative ready for every Amazon-tagged problem.
- They care about correctness under edge cases more than micro-optimizations. Step 7 matters.
