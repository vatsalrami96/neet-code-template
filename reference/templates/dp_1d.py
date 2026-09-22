"""1-D DP. Invariant: dp[i] is fully correct before dp[i+1] is computed, and it depends only on smaller indices.
Recipe: define the state in one sentence, write the recurrence, set base cases, pick the order, read the answer.
Bug: an off-by-one in the base case, or defining dp[i] as 'best in prefix' when you need 'best ending at i'."""

def house_robber(nums):
    take = skip = 0                    # best if we take/skip the current house
    for x in nums:
        take, skip = skip + x, max(take, skip)
    return max(take, skip)

def coin_change(coins, amount):
    INF = float('inf')
    dp = [0] + [INF] * amount          # dp[a] = fewest coins to make a
    for a in range(1, amount + 1):
        for c in coins:
            if c <= a and dp[a - c] + 1 < dp[a]:
                dp[a] = dp[a - c] + 1
    return dp[amount] if dp[amount] < INF else -1

def lis_length(nums):
    import bisect
    tails = []                         # tails[k] = smallest tail of an increasing subsequence of length k+1
    for x in nums:
        i = bisect.bisect_left(tails, x)
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return len(tails)
