package main

import (
	"fmt"
	"os"
	"strconv"
)

func add(a, b int) int {
	return a + b
}

func addKXTimes(n, k int) int {
	a := 0
	for i := 0; i < n; i++ {
		a = (a + i) % k
	}
	return a
}

func addKXTimesParallel(n, k int) int {
	const numThreads = 6
	chunkSize := n / numThreads
	results := make(chan int, numThreads)

	for t := 0; t < numThreads; t++ {
		go func(t int) {
			start := t * chunkSize
			end := n
			if t != numThreads-1 {
				end = (t + 1) * chunkSize
			}
			a := 0
			for i := start; i < end; i++ {
				a = (a + i) % k
			}
			results <- a
		}(t)
	}
	total := 0
	for i := 0; i < numThreads; i++ {
		total += <-results
	}
	return total
}

func main() {
	if len(os.Args) < 4 {
		fmt.Println("Usage: main <func> <n> <k>")
		os.Exit(1)
	}
	funcName := os.Args[1]
	n, _ := strconv.Atoi(os.Args[2])
	k, _ := strconv.Atoi(os.Args[3])

	var result int
	if funcName == "add" {
		result = add(n, k)
	} else if funcName == "addKXTimes" {
		result = addKXTimes(n, k)
	} else if funcName == "addKXTimesParallel" {
		result = addKXTimesParallel(n, k)
	} else {
		fmt.Println("Unknown function")
		os.Exit(1)
	}
	fmt.Println(result)
}
