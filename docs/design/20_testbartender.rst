Design: TestBartender
=============================

Archtictural decision for lazy test evaluation
-----------------------------------------------

pytest does testcollection at the beginning.

We decided to do lazy testcollection.

* The test duration might differ a lot - between a few seconds and 10 minutes.
* The goal is, to have the overall time of the tests as small as possible.

Influencing the test process / freedom in the choice of tentacles

* There might be redundant tentacles to speed up critical path.
* For tests requireing two tentacles, for example WLAN STA vs WLAN AP, we may pick tentacles which are ready just now.

Classes involved in testcollection
----------------------------------------

The TestBartender and the testcollection is quite complex.

The sources are in this package: src/testbed/testcollection
The sources of the test specs are in this package: src/testbed/testrunspecs

There is some unit testing here: <testbed_micropython>/tests/test_collection.py


TestRunSpec
^^^^^^^^^^^^^^^^^

A `TestRunSpec` is used to specify a test in the micropython directory which may be called in a test run.

The method `generate()` will generate the next `TestRun` - for example a call to 'run-perfbench.py'.

The method `generate()` might be seen as a bartender which hands out a burger or asks for money depending on the actual needs.

.. mermaid::

    classDiagram
        class TestRunSpec{
            generate(available_tentacles, available_firmwares) -> TestRun
        }
        TestRunSpec *-- TestRunSpecs



.. code:: 

    TESTRUNSPEC_PERFTEST = TestRunSpec("run-perfbench.py", TestRunPerfTest)
    TESTRUNSPEC_RUNTESTS_MULTINET = TestRunSpec("run-multitests.py", TestRunMultitestMultinet)
    TESTRUNSPEC_RUNTESTS_STANDARD = TestRunSpec("run-tests.py", TestRunRunTests)

    specs = [
        multinet.TESTRUNSPEC_RUNTESTS_MULTBLUETOOTH,
        multinet.TESTRUNSPEC_RUNTESTS_MULTINET,
        perftest.TESTRUNSPEC_PERFTEST,
        runtests_net_inet.TESTRUNSPEC_RUNTESTS_NET_HOSTED,
        runtests_net_inet.TESTRUNSPEC_RUNTESTS_NET_INET,
        runtests.TESTRUNSPEC_RUNTESTS_STANDARD,
        runtests.TESTRUNSPEC_RUNTESTS_EXTMOD_HARDWARE,
    ]

TestRun
^^^^^^^^^^^^^^^^^

A `TestRun` will

* create a directory `<repo>/results/RUN-TESTS_EXTMOD_HARDWARE[5f2c-RPI_PICO_W]`
* start a process which

  * Lock the associated tentacles 
  * initalizes the associated tentacles
  * flashes the boards if needed
  * starts the test, for example 'run-perfbench.py'
  * Release the associated tentacles
  
The `TestRun` knows the associated `TestRunSpec` which will provide information needed to run the test.

.. mermaid::
    classDiagram
        class TestRun{
            testid 'RUN-TESTS_EXTMOD_HARDWARE[5f2c-RPI_PICO_W]'
            assigned tentacles
            assigned firmwares
            test()
        }
        class TestRunPerfTest{
            test()
        }
        class TestRunRunTests{
            test()
        }
        class TestRunMultitestBase{
            test()
        }
        TestRun <|-- TestRunPerfTest
        TestRun <|-- TestRunRunTests
        TestRun <|-- TestRunMultitestBase


`TestRunSpecs` generating `TestRun`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. mermaid::

    classDiagram
        class TestRunSpec{
            generate(available_tentacles, available_firmwares) -> TestRun
        }
        class TestRunSpecs{
            generate(available_tentacles, available_firmwares) -> TestRun
        }
        class TestRun{
            +testid Example: RUN-TESTS_EXTMOD_HARDWARE[5f2c-RPI_PICO_W]
            +assigned tentacles
            +assigned firmwares
            -test()
        }
        class TestRunPerfTest{
            -test()
        }
        class TestRunRunTests{
            -test()
        }
        class TestRunMultitestBase{
            -test()
        }
        TestRun <|-- TestRunPerfTest
        TestRun <|-- TestRunRunTests
        TestRun <|-- TestRunMultitestBase
        TestRun --> TestRunSpec
        TestRunSpec *-- TestRunSpecs


The `TestBartender` calls `TestRunSpecs.generate()` to get a new `TestRun`.

* Generate will loop over all `TestRunSpecs.generate()`.
* This will be a possible long list of possible 'TestRun's.
* Not the 'TestRun's are ordered by priority.
* The one with the highest priority is selected.
* This 'TestRun' now will be started - flow see above.

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
