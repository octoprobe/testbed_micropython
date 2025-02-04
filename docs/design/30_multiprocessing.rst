Design: Multiprocessing
=============================

This chapter is about how multiprocessing is implementated.

Design decision: multiprocessing.process
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There is a playground: experiments/multiprocessing_process_queue_batteries.py

The implementation is here: src/testbed/multiprocessing/util_multiprocessing.py

There are many ways how multiprocessing may be done with python. I opted for 'multiprocessing.process.Process()' in a 'spawn' context. The processes communicate with 'multiprocessing.Queue()'.

See

* https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process
* https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Queue

The reason why I did not use https://docs.python.org/3/library/multiprocessing.html#module-multiprocessing.pool was, that there is no timeout for a task in a pool. However, such a timeout is very important for a testenvironment which may be flaky.


Target
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::

   I use the name 'Target' and 'AsyncTarget'.

   This originates from the python implmentation of https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process().

   The second paramter is called 'target' which is the function which has to be called in the remote process.

.. note::

   It is very difficult to debug a program which is spread out over different processes!
   To ease this, I implemented a small wrapper which allows to run the 'target' in a external process or just blocking in the very same process.

   * See: --no-multiprocessing

.. code:: 

    class TargetCtx:
        def start(self, async_target: AsyncTarget) -> None:
            process = self.ctx.Process(
                  name=target_unique_name,
                  target=async_target.target_func,
                  args=target_args_complete,
            )
            async_target.target = Target(
                  multiprocessing=self.multiprocessing,
                  process=process,
                  timeout_s=async_target.timeout_s,
            )

            if self.multiprocessing:
                  #
                  # Start the process which then calles 'target'
                  #
                  process.start()
            else:
                  # Call the 'target' function directly
                  async_target.target_func(*target_args_complete)


The important code is `if self.multiprocessing`.


Sequence diagram
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. mermaid::

   sequenceDiagram
      participant tr as Testrunner
      participant b as TestBartender/BuildBartender
      participant tx as TargetCtx
      participant f as TestFunc/BuildFunc
      tr->>b: testrun = testrun_next()
      b->>tx: run(AsyncResult(testrun))
      tx->>+f: f(unique_id)
      f->>-tx: Event(unique_id)
      tx->>b: done(unique_id)


communication between main and subprocesses
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When a process is started, the target function will be called with paramters.

These parameters are pickled by 'multiprocessing.process' and call on of these functions:

.. code:: 

   # src/testbed/mptest/util_testrunner.py
   def target_run_one_test_async(
      arg1: util_multiprocessing.TargetArg1,
      args: Args,
      ctxtestrun: CtxTestRun,
      testrun: TestRun,
      repo_micropython_tests: pathlib.Path,
   ) -> None:
      ...

   # src/testbed/multiprocessing/firmware_bartender.py
   def target_build_firmware_async(
      arg1: util_multiprocessing.TargetArg1,
      directory_mpbuild_artifacts: pathlib.Path,
      firmwares: FirmwaresTobeBuilt,
      repo_micropython_firmware: pathlib.Path,
   ) -> None:
      ...

Now a process may send events to the main process. All events derive from `EventBase`.

.. code:: 

   @dataclass(repr=True)
   class EventBase:
      target_unique_name: str


   @dataclass(repr=True)
   class EventExit(EventBase):
      logfile: pathlib.Path
      success: bool

      @property
      def logfile_relative(self) -> pathlib.Path:
         return relative_cwd(self.logfile)


   @dataclass(repr=True)
   class EventLog(EventBase):
      msg: str



FirmwareBartender and TestBartender cooperation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The FirmwareBartender

* Start a process which
  * Compiles one firmware after each other
  * Notifies the FirmwareBartender with `EventFirmwareSpec`

The TestBartender

* Waits for
  
  * FirmwareSpecs to be ready
  * Tentacles to be available
  * If a 'TestRun' is available
    * This test will be started
  
  * If the TestBartender has no tests anymore to to, the `mptest` will exit.