import ctypes
import time

# Prepare lib: gcc -shared -o libexample.so -fPIC example.c

if __name__ == '__main__':
    # Load the shared library
    # On Linux
    lib = ctypes.CDLL('./libexample.so')

    # Define argument and return types for the `add` function - optional
    lib.add.argtypes = (ctypes.c_int, ctypes.c_int)
    lib.add.restype = ctypes.c_int

    start = time.time()
    for i in range(10**7):
        # Call the C functions
        result = lib.add(i, 7)
    print("Call c each time:", time.time() - start)

    start = time.time()
    result = 0
    for i in range(10**7):
        result = (result + i) % 7
    print("All in python:", time.time() - start)

    start = time.time()
    x = lib.add_k_x_times(10**7, 7)
    print("Call c one time:", time.time() - start)

    start = time.time()
    lib.add_k_x_times_parallel(10**7, 7)
    print("Call c one time parallel:", time.time() - start)

    start = time.time()
    lib.add_k_x_times(10**10, 7)
    print("Call c one time (x1000):", time.time() - start)

    start = time.time()
    lib.add_k_x_times_parallel(10**10, 7)
    print("Call c one time parallel (x1000):", time.time() - start)
