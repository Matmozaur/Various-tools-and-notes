// example.c
#include <stdio.h>
#include <pthread.h>
#include <stdlib.h>

// Define the number of threads to be created
#define NUM_THREADS 6

int add(int a, int b) {
    return a + b;
}

void add_k_x_times(int n, int k) {
    for (int i = 0; i < n; i++) {
        int a = i + k;
    }
}


typedef struct {
    int start;   // Starting index for this thread
    int end;     // Ending index for this thread
    int k;       // Value of k
} ThreadData;

// Thread function to perform the computation
void* add_k_x_times_thread(void* arg) {
    ThreadData* data = (ThreadData*)arg;

    for (int i = data->start; i < data->end; i++) {
        int a = i + data->k;
    }

    return NULL;
}

void add_k_x_times_parallel(int n, int k) {
    pthread_t threads[NUM_THREADS];
    ThreadData thread_data[NUM_THREADS];

    int chunk_size = n / NUM_THREADS; // Divide the work among threads

    for (int t = 0; t < NUM_THREADS; t++) {
        // Calculate start and end indices for each thread
        thread_data[t].start = t * chunk_size;
        thread_data[t].end = (t == NUM_THREADS - 1) ? n : (t + 1) * chunk_size;
        thread_data[t].k = k;

        // Create the thread
        pthread_create(&threads[t], NULL, add_k_x_times_thread, &thread_data[t]);
    }

    // Wait for all threads to complete
    for (int t = 0; t < NUM_THREADS; t++) {
        pthread_join(threads[t], NULL);
    }
}

