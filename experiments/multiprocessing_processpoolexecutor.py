import concurrent
import concurrent.futures
import time
from multiprocessing import Queue


def x(q: Queue, begin_s: float, time_s: float) -> float:
    time.sleep(time_s)
    q.put(f"{time_s}: {time.time()-begin_s:0.1f}s")
    return time_s, time.time() - begin_s


def main():
    with concurrent.futures.ProcessPoolExecutor() as e:
        q = Queue()
        begin_s = time.time()
        results = [e.submit(x, q, begin_s, time_s) for time_s in (12, 3, 8, 5, 2)]

        while True:
            print(q.get())

        for f in concurrent.futures.as_completed(results):
            print(f.result())


if __name__ == "__main__":
    main()
