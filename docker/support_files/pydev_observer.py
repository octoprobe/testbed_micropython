import time

import pyudev

context = pyudev.Context()
monitor = pyudev.Monitor.from_netlink(context)
# monitor.filter_by("block")


def log_event(action, device):
    print(f"{action} - {device}")


observer = pyudev.MonitorObserver(monitor, log_event)
observer.start()
print("pyudev is now active for 10s")
time.sleep(10.0)
