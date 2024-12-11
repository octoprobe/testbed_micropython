# https://superfastpython.com/multiprocessing-pool-share-queue/
# https://superfastpython.com/multiprocessing-pool-python/
# https://docs.python.org/3/library/multiprocessing.html#sharing-state-between-processes

# SuperFastPython.com
# example of sharing a queue via a manager
from multiprocessing import Manager, Pool, set_start_method
from random import random
from time import sleep


# task completed in a worker
def task(queue):
    # generate some work
    data = random() * 5
    # block to simulate work
    sleep(data)
    # put it on the queue
    queue.put(data)


# protect the entry point
if __name__ == "__main__":
    # set the fork start method
    set_start_method("spawn")
    # create the manager
    with Manager() as manager:
        # create the shared queue
        queue = manager.Queue()
        # create the pool of workers
        with Pool(10) as pool:
            # create a list of arguments, one for each call
            args = [queue for _ in range(10)]
            # execute the tasks in parallel
            pool.map(task, args)
        # consume all items
        for _ in range(10):
            # get item from queue
            item = queue.get()
            # report item
            print(f"> got {item}")
