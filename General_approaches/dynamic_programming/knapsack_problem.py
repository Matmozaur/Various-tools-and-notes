# Python program to implement unbounded knapsack problem

def knap_sack(capacity, val, wt):
    # 1D matrix for tabulation.
    dp = [0 for _ in range(capacity + 1)]

    # Calculate maximum profit for each item index and knapsack weight.
    for i in range(len(val)):
        for j in range(1, capacity + 1):
            take = 0
            # check it the new item can be fitted for given capacity
            if j - wt[i] >= 0:
                # fit new item
                take = val[i] + dp[j - wt[i]]

            # score for capacity without the newest item
            no_take = dp[j]

            dp[j] = max(take, no_take)

    return dp[capacity]


if __name__ == "__main__":
    val = [1, 1, 4, 5, 2, 3]
    wt = [2, 1, 4, 2, 3, 6]
    capacity = 3
    print(knap_sack(capacity, val, wt))