import subprocess
import time

# Build Go binary: go build -o go_inside_python main.go

def run_go(func_name, n, k):
    result = subprocess.run([
        './go_inside_python', func_name, str(n), str(k)
    ], capture_output=True, text=True)
    return int(result.stdout.strip())

start = time.time()
for i in range(10):
    result = run_go('add', i, 7)
print("Call Go each time (/ 1000000):", time.time() - start)

start = time.time()
result = 0
for i in range(10**7):
    result = (result + i) % 7
print("All in python:", time.time() - start)

start = time.time()
x = run_go('addKXTimes', 10**7, 7)
print("Call Go one time:", time.time() - start)

start = time.time()
x = run_go('addKXTimesParallel', 10**7, 7)
print("Call Go one time parallel:", time.time() - start)


start = time.time()
x = run_go('addKXTimes', 10**10, 7)
print("Call Go one time (x1000):", time.time() - start)

start = time.time()
x = run_go('addKXTimesParallel', 10**10, 7)
print("Call Go one time parallel (x1000):", time.time() - start)