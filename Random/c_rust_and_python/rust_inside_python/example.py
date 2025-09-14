
import ctypes
import time
import os

lib_path = './target/release/librust_inside_python.so'

if not os.path.exists(lib_path):
    raise FileNotFoundError(f"Shared library not found: {lib_path}")

lib = ctypes.CDLL(lib_path)

lib.add.argtypes = (ctypes.c_int, ctypes.c_int)
lib.add.restype = ctypes.c_int

start = time.time()
for i in range(10**7):
    result = lib.add(i, 7)
print("Call Rust each time:", time.time() - start)

start = time.time()
for i in range(10**7):
    result = i+7
print("All in python:", time.time() - start)

start = time.time()
lib.add_k_x_times(10**7, 7)
print("Call Rust one time:", time.time() - start)

start = time.time()
lib.add_k_x_times_parallel(10**7, 7)
print("Call Rust one time parallel:", time.time() - start)

start = time.time()
lib.add_k_x_times(10**10, 7)
print("Call Rust one time (x1000):", time.time() - start)

start = time.time()
lib.add_k_x_times_parallel(10**10, 7)
print("Call Rust one time parallel (x1000):", time.time() - start)
