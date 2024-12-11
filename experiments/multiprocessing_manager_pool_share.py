# https://docs.python.org/3/library/multiprocessing.html#sharing-state-between-processes


import time
from multiprocessing import Manager, Pool, Queue, TimeoutError, set_start_method


def x(queue: Queue, d, begin_s: float, time_s: float) -> tuple[float, float]:
    time.sleep(time_s)
    msg = f"{time_s}: {time.time()-begin_s:0.1f}s"
    print(msg)
    for _ in range(3):
        queue.put(msg)
        d[time.time()] = msg
    time.sleep(time_s)
    return time_s, time.time() - begin_s


def main():
    # set the fork start method
    set_start_method("spawn")
    # create the manager
    with Manager() as manager:
        # create the shared queue
        queue = manager.Queue()
        d = manager.dict()
        # create the pool of workers
        with Pool(10) as pool:
            begin_s = time.time()
            results = [
                pool.apply_async(func=x, args=(queue, d, begin_s, time_s))
                for time_s in (12, 3, 8, 5, 2)
            ]

            while True:
                if len(results) == 0:
                    print("Done")
                    for k, v in d.items():
                        print(k, v)
                    return

                for r in results:
                    try:
                        g = r.get(timeout=0.001)
                        print(f"Result.get: {g}")
                        results.remove(r)
                        break
                    except TimeoutError:
                        pass

                while not queue.empty():
                    item = queue.get(timeout=0.001)
                    print(f"> got {item}")


# protect the entry point
if __name__ == "__main__":
    main()
