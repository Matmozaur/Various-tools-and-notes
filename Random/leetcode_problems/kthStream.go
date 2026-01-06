package main

// import "sort"

// type KthLargest struct {
// 	nums []int
// 	l    int
// 	k    int
// }

// func ConstructorKthLargest(k int, nums []int) KthLargest {
// 	sort.Sort(sort.Reverse(sort.IntSlice(nums)))
// 	if len(nums) > k {
// 		nums = nums[:k]
// 	}
// 	return KthLargest{
// 		nums: nums,
// 		k:    k,
// 		l:    len(nums),
// 	}
// }

// func insert(val, n int, nums []int) []int {
// 	left, right := 0, n
// 	for left < right {
// 		mid := (left + right) / 2
// 		if val <= nums[mid] {
// 			left = mid + 1
// 		} else {
// 			right = mid
// 		}
// 	}
// 	nums = append(nums, 0)
// 	copy(nums[left+1:], nums[left:n])
// 	nums[left] = val
// 	return nums
// }

// func (this *KthLargest) Add(val int) int {
// 	if this.l < this.k {
// 		this.nums = insert(val, this.l, this.nums)
// 		// this.nums = append(this.nums, val)
// 		this.l++
// 		// sort.Sort(sort.Reverse(sort.IntSlice(this.nums)))
// 		return this.nums[this.l-1]

// 	} else if val > this.nums[this.k-1] {
// 		this.nums = insert(val, this.k, this.nums)
// 		return this.nums[this.k-1]
// 	} else {
// 		return this.nums[this.k-1]
// 	}
// }

import "container/heap"

type KthLargest struct {
	k       int
	minHeap *IntHeap
}

func ConstructorKthLargest(k int, nums []int) KthLargest {
	minHeap := &IntHeap{}
	heap.Init(minHeap)
	kthLargest := KthLargest{k: k, minHeap: minHeap}
	for _, num := range nums {
		kthLargest.Add(num)
	}
	return kthLargest
}

func (this *KthLargest) Add(val int) int {
	if this.minHeap.Len() < this.k {
		heap.Push(this.minHeap, val)
	} else if val > (*this.minHeap)[0] {
		heap.Pop(this.minHeap)
		heap.Push(this.minHeap, val)
	}
	return (*this.minHeap)[0]
}

// IntHeap is a min-heap of ints.
type IntHeap []int

func (h IntHeap) Len() int           { return len(h) }
func (h IntHeap) Less(i, j int) bool { return h[i] < h[j] }
func (h IntHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }

func (h *IntHeap) Push(x interface{}) {
	*h = append(*h, x.(int))
}

func (h *IntHeap) Pop() interface{} {
	old := *h
	n := len(old)
	x := old[n-1]
	*h = old[0 : n-1]
	return x
}
