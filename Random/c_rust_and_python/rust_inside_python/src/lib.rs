
#[no_mangle]
pub extern "C" fn add(a: i32, b: i32) -> i32 {
    a + b
}

#[no_mangle]
pub extern "C" fn add_k_x_times(n: i32, k: i32) -> i32 {
    let mut a: i32 = 0;
    for i in 0..n {
        a = (a + i) % k;
    }
    a
}

// For parallel version, you can use rayon or threads (not shown for brevity)

#[no_mangle]
pub extern "C" fn add_k_x_times_parallel(n: i32, k: i32) -> i32 {
    use std::thread;
    const NUM_THREADS: i32 = 6;
    let chunk_size = n / NUM_THREADS;
    let mut handles = Vec::new();

    for t in 0..NUM_THREADS {
        let start = t * chunk_size;
        let end = if t == NUM_THREADS - 1 { n } else { (t + 1) * chunk_size };
        let k = k;
        handles.push(thread::spawn(move || {
            let mut a = 0;
            for i in start..end {
                a = (a + i) % k;
            }
            a
        }));
    }
    let mut total = 0;
    for handle in handles {
        total += handle.join().unwrap();
    }
    total
}
