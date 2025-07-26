User Guide
==========

Indended audience: A MicroPython firmware or test developer who wants to use `testbed_micropython`.

Summary
-----------------------

`testbed_micropython` is a wrapper around these tests: https://github.com/micropython/micropython/tree/master/tests/xx.py.

The testbed resposibility is:

* query all connected tentacles
* build the firmware required by the connected tentacles and board-variants
* flash the tentacle if required. Some tentacles have to be flashed multiple times to be able to test board-variants.
* run all tests against these tentacles
* collect all build results / test results

Installation
------------------------

Follow these instructions: https://www.octoprobe.org/testbed_showcase/installation/10_ubuntu.html

Please replace every occurence of `testenv_showcase` with `testenv_micropython`.

Usage scenarios
-----------------------

Usage principles
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A firmware developer typically has the micropython repo checked out and works within that folder.

These 3 companion programs ease the work:

* `mpremote`: Communicate with a board.
* `mpbuild`: Build a firmware using docker containers.
* `mptest`: Test the firmware. `mptest` makes intense use of `mpremote` and `mpbuild`.

Automated Regression Test - full coverage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Goal:
  
  * As much coverage as possible
  * Run fully unattended
  
.. code::

    mptest test --micropython-tests=<git/branch>  --firmware-build=<git/branch>

* `mptest` will:

  * clone/checkout the required branches
  * build the firmware
  * run the tests
  * collect the results.

Automated Regression Test - limited coverage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Goal:

  * As above
  * The testrun should be faster (as a developer might be waiting for the results)
  * The testresult should be limited (as a developer just changed code for one board)

.. code::

    mptest test .. --only-board=RPI_PICO2 --only-test=RUN-TESTS_NET_HOSTED

Working on the firmware: Build and test
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Goal:

  * The developer is working on the C-code and wants to have test feedback fast.

* Workflow:
  
  * The developer has the repo checked out and is working on the code.
  * The current directory is always the micropython git repo.
  * Use `mptest` to compile and test the firmware.
  
.. code::

    # The current directory is the micropython git repo
    mptest test

This now will build/test the firmware against all connected tentacles.

As the git repo is 'dirty' the firmware will ALWAYS be flashed.

.. code::

    # As above, but the tests are taken from another branch
    mptest test --micropython-tests=<git/branch>


Working on a test: Flash once, test many times
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Goal:

  * The developer is improving the tests and wants to have test feedback fast.
  * As build/flash is slow, this step should only be done once.

* Workflow:
  
  * The developer has the repo checked out and is working on the test code.
  * The current directory is always the micropthon git repo.
  * Preparation: Build the firmware and flash the tentacles - this is slow!
  
.. code::

    # Preparation: Compile firmware and flash the tentacles
    mptest flash --firmware-build=<git/branch>

This will take a few minutes.

.. code::

    # Run the tests
    mptest test --flash-skip

This is fast - the tests will be started immediately!
