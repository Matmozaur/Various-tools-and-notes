import time
from basic import add_k_x_times


if __name__ == '__main__':
    start = time.time()
    for i in range(10**7):
        result = i+7
    print("All in python:", time.time() - start)

    start = time.time()
    add_k_x_times(10**8, 7)
    print("Cython lib:", time.time() - start)
