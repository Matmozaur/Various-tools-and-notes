// example.c
#include <stdio.h>
#include <pthread.h>
#include <stdlib.h>

// Define the number of threads to be created
#define NUM_THREADS 6

int add(int a, int b) {
    return a + b;
}


int add_k_x_times(int n, int k) {
    int a = 0;
    for (int i = 0; i < n; i++) {
        a = (a + i) % k;
    }
    return a;
}


typedef struct {
    int start;   // Starting index for this thread
    int end;     // Ending index for this thread
    int k;       // Value of k
} ThreadData;

// Thread function to perform the computation
void* add_k_x_times_thread(void* arg) {
    ThreadData* data = (ThreadData*)arg;

    int a = 0;
    for (int i = data->start; i < data->end; i++) {
        a = (a + i) % data->k;
    }

    int* result = malloc(sizeof(int));
    *result = a;
    return result;
}

// Parallel version: divides work into chunks, sums results
int add_k_x_times_parallel(int n, int k) {
    pthread_t threads[NUM_THREADS];
    ThreadData thread_data[NUM_THREADS];
    int chunk_size = n / NUM_THREADS;
    int total = 0;

    for (int t = 0; t < NUM_THREADS; t++) {
        thread_data[t].start = t * chunk_size;
        thread_data[t].end = (t == NUM_THREADS - 1) ? n : (t + 1) * chunk_size;
        thread_data[t].k = k;
        pthread_create(&threads[t], NULL, add_k_x_times_thread, &thread_data[t]);
    }

    for (int t = 0; t < NUM_THREADS; t++) {
        int* result;
        pthread_join(threads[t], (void**)&result);
        total += *result;
        free(result);
    }
    return total;
}

