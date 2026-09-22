# Two Pointers

## Before you start
- Comfortable with while loops that move two indices independently, and with `sorted` input.
- You can say why a nested loop over pairs is O(n^2).

## The pattern and its templates
**Two indices that move in a way that never needs to go back.** Each step moves at least one pointer, so total
work is O(n). The invariant: *the answer, if it exists, is still inside the range the pointers bound.*

Two shapes:
1. **Opposite ends, converging.** `l = 0, r = n - 1`. On sorted input, compare `a[l] + a[r]` to the target: too
   small moves `l` right, too big moves `r` left. Valid Palindrome, Two Sum II, 3Sum (fix one, two-pointer the rest),
   Container With Most Water (move the shorter side; the taller side can never do better with a narrower width).
2. **Same direction, one leads.** Slow and fast. Used in the next section (sliding window) and in linked lists
   (cycle detection). Not the focus here.

Trapping Rain Water is the capstone: water at i is `min(maxLeft, maxRight) - height[i]`. With two pointers you
only need to know which side's max is smaller, because that side's water level is already decided.

## How to recognize it
"Sorted array", "pair / triplet with sum", "palindrome", "in place", "O(1) extra space", "container / area between
two lines". If you'd sort first and then scan, it is probably two pointers.

## Classic mistakes
- Moving the wrong pointer in Container With Most Water (move the shorter one, always).
- 3Sum duplicates: skip equal values for the fixed element *and* for both moving pointers after a match.
- Off-by-one when checking `l < r` vs `l <= r`.
- Valid Palindrome: forgetting to skip non-alphanumerics on both sides before comparing.
- Trapping Rain Water: trying to compute both maxes with the brute force O(n) arrays when the interviewer asked
  for O(1) space.

## Complexity you should expect
O(n) time after an optional O(n log n) sort. O(1) extra space is the point; if you used a set or a map, ask
whether it was needed.

## Warm-ups
1. `a = [1, 2, 4, 7, 11, 15]`, target 15. Walk the converging two-pointer by hand and list the (l, r) pairs you
   visit. How many steps at most, and why?
2. In one sentence: in Container With Most Water, why is it safe to move the pointer at the shorter line?

## The problems, in order
| # | Problem | Teaches | Note |
|---|---|---|---|
| 1 | Valid Palindrome | converging pointers with a skip condition | |
| 2 | Two Sum II | converging on sorted input | prerequisite for 3Sum |
| 3 | 3Sum | fix one, two-pointer the rest, duplicate skipping | Amazon asks this often |
| 4 | Container With Most Water | greedy move of the shorter side | Amazon asks this often |
| 5 | Trapping Rain Water | the min-of-maxes insight, then two pointers | Hard, Amazon's most-asked; 20 min cap then hints |
