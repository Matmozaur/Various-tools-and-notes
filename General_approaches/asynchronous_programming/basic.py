import asyncio
import random

TOTAL_TASKS=10
semaphore = asyncio.Semaphore(3)  # Limit concurrent workers

async def produce_tasks(queue, total_tasks):
    for i in range(total_tasks):
        await asyncio.sleep(random.uniform(0.1, 0.5))
        task_data = f"Task-{i}"
        print(f"[Producer] Produced {task_data}")
        await queue.put(task_data)
    await queue.put(None)  # Sentinel to stop consumer

async def process_task(task_data):
    async with semaphore:
        print(f"[Worker] Started {task_data}")
        await asyncio.sleep(random.uniform(0.5, 2))
        print(f"[Worker] Finished {task_data}")

async def consume_tasks(queue):
    while True:
        task_data = await queue.get()
        if task_data is None:
            print("[Consumer] No more tasks. Shutting down.")
            break
        try:
            await asyncio.wait_for(process_task(task_data), timeout=3)
        except asyncio.TimeoutError:
            print(f"[Timeout] {task_data} took too long and was skipped.")

async def main():
    queue = asyncio.Queue()
    producer = asyncio.create_task(produce_tasks(queue, TOTAL_TASKS))
    consumer = asyncio.create_task(consume_tasks(queue))
    await asyncio.gather(producer, consumer)

if __name__ == "__main__":
    asyncio.run(main())
