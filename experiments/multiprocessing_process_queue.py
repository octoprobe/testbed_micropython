# https://docs.python.org/3/library/multiprocessing.html#sharing-state-between-processes


import multiprocessing
import time


def x(
    name: str, queue: multiprocessing.Queue, begin_s: float, time_s: float
) -> tuple[float, float]:
    time.sleep(time_s)
    msg = f"{time_s}: {time.time()-begin_s:0.1f}s"
    print(f"Queue put({msg}")
    queue.put(msg)
    time.sleep(1.0)
    return time_s, time.time() - begin_s


def main():
    full_begin_s = time.time()
    ctx = multiprocessing.get_context("spawn")
    # with Manager() as manager:
    if True:
        # d = manager.dict()
        queue = ctx.Queue()
        begin_s = time.time()
        procs: list[multiprocessing.Process] = []
        for time_s in (10, 3, 6, 5, 2):
            name = f"My-Process-{time_s:0.1f}s"
            p = ctx.Process(
                target=x,
                name=name,
                args=(name, queue, begin_s, time_s),
            )
            procs.append(p)

        for p in procs:
            p.start()

        while True:
            if len(procs) == 0:
                print("Done")
                print(f"Full duration {time.time()-full_begin_s:0.1f}s")
                return

            duration_timeout_s = time.time() - full_begin_s
            timeout = duration_timeout_s > 8.0
            for p in procs:
                if p.is_alive():
                    if timeout:
                        print(f"Killing {p.name}")
                        p.kill()
                    else:
                        continue

                p.join()
                procs.remove(p)
                print(f"join({p.name})")
                break

            while not queue.empty():
                msg = queue.get()
                print(f"Queue get({msg}")

            time.sleep(0.001)


# protect the entry point
if __name__ == "__main__":
    main()
