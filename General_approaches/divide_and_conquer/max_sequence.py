# Given an array of integers, find the contiguous subarray (containing at least one number) that has the largest sum.

def max_crossing_sum(arr, left, mid, right):
    # Include elements on left of mid
    left_sum = float('-inf')
    total = 0
    for i in range(mid, left - 1, -1):
        total += arr[i]
        left_sum = max(left_sum, total)

    # Include elements on right of mid
    right_sum = float('-inf')
    total = 0
    for i in range(mid + 1, right + 1):
        total += arr[i]
        right_sum = max(right_sum, total)

    # Return sum of elements on left and right of mid
    return left_sum + right_sum

def max_subarray_sum(arr, left, right):
    # Base case: only one element
    if left == right:
        return arr[left]

    mid = (left + right) // 2

    # Find max subarray sum in left half, right half, and crossing the mid
    left_max = max_subarray_sum(arr, left, mid)
    right_max = max_subarray_sum(arr, mid + 1, right)
    cross_max = max_crossing_sum(arr, left, mid, right)

    return max(left_max, right_max, cross_max)

# Example usage
arr = [2, -4, 3, -1, 2, -4, 3]
n = len(arr)
max_sum = max_subarray_sum(arr, 0, n - 1)
print(f"Maximum subarray sum is: {max_sum}")
