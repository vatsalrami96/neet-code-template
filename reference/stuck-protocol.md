# Stuck protocol

When stuck for five minutes, stop staring and run this list top to bottom. Hint level 1 names which move applies.

1. **Re-read the constraints.** The bound tells you the complexity, and the complexity narrows the tools
   (see the table in `interview-process.md`). "n up to 10^5" rules out O(n^2) and points at sort, heap, hash, two
   pointers, sliding window, or binary search.
2. **Solve a smaller version.** n = 1, n = 2, n = 3 by hand. Watch what you do. Your hand procedure is often the
   algorithm.
3. **Solve the easier variant.** 2-D to 1-D. "Any subarray" to "subarray ending here". "K of them" to "one of them".
   Unweighted before weighted. Then lift the answer back.
4. **Sort it and look again.** Sorting costs n log n and often turns the problem into two pointers, greedy, or
   binary search. Ask what sorting would make adjacent.
5. **Ask what you need to know at each step.** If at index i you need "the max so far", "the last smaller element",
   "how many seen", "the best ending here", that missing fact names the data structure: running variable, monotonic
   stack, hash map counter, DP array.
6. **Work backwards from the answer.** What is the last decision? What must have been true just before it? This is
   how DP recurrences and reverse-BFS appear.
7. **Turn it into a yes-or-no check.** "Can we do it with value X?" If that check is monotonic in X, binary search
   on X. Koko, Ship Packages, Split Array all fall to this.
8. **Draw the state graph.** Nodes are states, edges are moves. If the answer is "fewest moves", it is BFS. If it is
   "does a path exist", DFS or union-find. If states repeat, memoize.
9. **Try the greedy and try to break it.** Propose the obvious greedy choice, then hunt for a counterexample for two
   minutes. If none, argue the exchange: swapping any other choice for the greedy one never hurts.
10. **Name the pattern out loud.** Say the section names: two pointers, sliding window, prefix sum, monotonic stack,
    heap, BFS, DFS, backtracking, DP, binary search on answer, union-find, trie, intervals. One of them will feel
    close. Start from its template.

If all ten fail after 20 minutes on a Medium or Hard, take hint level 2. That is not failure; the log says you
tried the protocol, and the re-solve in three days is where it sticks.
