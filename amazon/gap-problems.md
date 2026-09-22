# Amazon gap problems

Twelve problems Amazon asks often that the NeetCode 150 does not cover well. They live in `plan/problems.json`
under section `99-amazon-gap` and are scheduled after the 150. Source: LeetCode company tag, six-month list,
pulled 2026-09-17. Score is Amazon frequency (0 to 100).

| # | Problem | Score | Why it is here |
|---|---|---|---|
| 560 | Subarray Sum Equals K | 68 | prefix sum + hash map, the most common "not in 150" ask |
| 767 | Reorganize String | 71 | greedy with a heap, string reconstruction |
| 236 | Lowest Common Ancestor of a Binary Tree | 61 | the general-tree version; 150 only has the BST one |
| 904 | Fruit Into Baskets | 67 | sliding window with at most K distinct |
| 735 | Asteroid Collision | 59 | stack simulation, Amazon favorite |
| 1011 | Capacity To Ship Packages Within D Days | 60 | binary search on the answer |
| 31 | Next Permutation | 58 | array manipulation, frequently asked cold |
| 394 | Decode String | 45 | stack-based string parsing |
| 380 | Insert Delete GetRandom O(1) | 45 | design with array + hash map |
| 460 | LFU Cache | 30 | design, the LRU follow-up |
| 1268 | Search Suggestions System | 26 | trie or sort + binary search, classic Amazon |
| 3413 | Maximum Coins From K Consecutive Bags | 80 | recent OA-style problem, long statement, sliding window |

Beyond these, in maintenance mode, continue down the Amazon six-month list sorted by frequency.
