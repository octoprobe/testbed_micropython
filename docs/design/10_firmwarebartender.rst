Design: FirmwareBartender
=============================

Buildflow
--------------------

The FirmwareBartender
 * Evaluates which firmwares have to be compiled
 * Orders the firmware for priority
 * If required: Calls `git clone/checkout`
 * If required: Calls `git clean`
 * Builds one firmware after the other
   * Informs TestBartender about the firmwares which have become ready

Multiprocessing
---------------------

The firmware shall be built while tests are running.

Therefore, the FirmwareBartender delegates the build to a subprocesses.

.. mermaid::

   sequenceDiagram
      participant m as main()
      participant f as FirmwareBartender
      participant b as Build Process
      participant s as Filesystem
      m->>f: connected tentacles
      f-->>+b: firmware-variant list
      b->>+s: RPI_PICO2
      s-->>-b: done
      b-->>f: EventFirmwareSpec(RPI_PICO2)
      b->>+s: TEENSY40
      s-->>-b: done
      b-->>f: EventFirmwareSpec(TEENSY40)
      b->>+s: RPI_PICO2-RISCV
      s-->>-b: done
      b-->>f: EventFirmwareSpec(RPI_PICO2-RISCV)
      b-->>-f: EventExitFirmware()
