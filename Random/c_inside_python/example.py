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
    for i in range(10**6):
        # Call the C functions
        result = lib.add(i, 7)
    print("Call c each time:", time.time() - start)

    start = time.time()
    for i in range(10**6):
        result = i+7
    print("All in python:", time.time() - start)

    start = time.time()
    lib.add_k_x_times(10**6, 7)
    print("Call c one time:", time.time() - start)
