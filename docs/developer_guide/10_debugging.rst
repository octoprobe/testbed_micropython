Debugging
=========

* --multiprocessing
* TestBartender


Firmware flashing is flaky
--------------------------------

This is the fastest way to flash the firmware

.. code:: 

    mptest.cli test --flash-force --only-test=RUN-TESTS_EXTMOD_HARDWARE --only-board=LOLIN_C3_MINI

If only the questioned tentacle is connected, this is even faster:

.. code:: 

    mptest.cli flash
