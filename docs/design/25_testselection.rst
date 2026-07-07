Design: TestSelection
=============================

Overview
--------

``get_testrun_specs()`` builds the list of :class:`TestRunSpec` objects that will
actually be executed in a test run.  It is called from
:class:`TestRunner.init()` with the query assembled from command-line flags and
returns a :class:`TestRunSpecs` (a typed list of :class:`TestRunSpec`).

Sources involved
----------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Source file
     - Role
   * - ``mptest/cli.py``
     - Typer CLI – parses command-line flags and creates :class:`ArgsQuery`
   * - ``mptest/util_baseclasses.py``
     - Defines :class:`ArgsQuery`
   * - ``mptest/util_testrunner.py``
     - Contains ``_TESTRUN_SPECS``, ``DICT_TESTRUN_SPECS``, and ``get_testrun_specs()``
   * - ``testrunspecs/util_testarg.py``
     - Defines :class:`TestArg` – parses the ``LABEL:command-args`` syntax
   * - ``testcollection/baseclasses_run.py``
     - Defines :class:`TestRunSpecs`
   * - ``testcollection/testrun_specs.py``
     - Defines :class:`TestRunSpec`

Static test inventory
---------------------

All known tests are registered in the module-level list ``_TESTRUN_SPECS`` in
``util_testrunner.py``::

    _TESTRUN_SPECS = [
        run_multinet.TESTRUNSPEC_RUNTESTS_MULTBLUETOOTH,
        run_multinet.TESTRUNSPEC_RUNTESTS_MULTINET,
        run_perftest.TESTRUNSPEC_PERFTEST,
        runtests_net_inet.TESTRUNSPEC_RUNTESTS_NET_HOSTED,
        runtests_net_inet.TESTRUNSPEC_RUNTESTS_NET_INET,
        runtests.TESTRUNSPEC_RUNTESTS_STANDARD,
        runtests.TESTRUNSPEC_RUNTESTS_STANDARD_VIA_MPY,
        runtests.TESTRUNSPEC_RUNTESTS_STANDARD_NATIVE,
        runtests.TESTRUNSPEC_RUNTESTS_EXTMOD_HARDWARE,
        runtests.TESTRUNSPEC_RUNTESTS_EXTMOD_HARDWARE_NATIVE,
        run_natmodtests.TESTRUNSPEC_RUN_NATMODTESTS,
        run_flash_format.TESTRUNSPEC_RUN_FLASH_FORMAT,
    ]

Each :class:`TestRunSpec` carries a ``label`` (e.g. ``RUN-TESTS_STANDARD``), a
``required_fut`` (:class:`EnumFut`), and the ``command`` to execute.  The dict
``DICT_TESTRUN_SPECS`` maps every label to its spec and is used for validation.

Run ``mptest list-tests`` to print the current inventory at any time.

Input parameters (``ArgsQuery``)
---------------------------------

:class:`ArgsQuery` is the data class that carries all filter criteria.  It is
constructed by ``ArgsQuery.factory()`` from the CLI flags listed below and then
passed to ``get_testrun_specs(query=...)``.

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - CLI flag (``mptest test``)
     - ``ArgsQuery`` field
     - Effect inside ``get_testrun_specs()``
   * - ``--only-test``
     - ``only_test: set[str]``
     - Keep only specs whose ``label`` is in the set.  Supports optional
       command-argument overrides (see below).
   * - ``--skip-test``
     - ``skip_test: set[str]``
     - Remove specs whose ``label`` is in the set.  Mutually exclusive with
       ``--only-test``.
   * - ``--only-fut``
     - ``only_fut: set[EnumFut]``
     - Keep only specs whose ``required_fut`` is in the set.
   * - ``--skip-fut``
     - ``skip_fut: set[EnumFut]``
     - Remove specs whose ``required_fut`` is in the set.  Mutually exclusive
       with ``--only-fut``.

``--only-test`` and ``--skip-test`` cannot be combined.
``--only-fut`` and ``--skip-fut`` cannot be combined.

Shell autocompletion for ``--only-test`` is provided by
``complete_only_test()``, which calls ``get_testrun_specs()`` without a query to
enumerate all registered labels.

Filtering logic
---------------

``get_testrun_specs()`` applies the filters in the following order:

1. Start with all specs from ``_TESTRUN_SPECS``.
2. **only_test** – if non-empty, keep only specs with a matching ``label``.

   * Each entry is parsed as a :class:`TestArg` with the syntax
     ``LABEL`` or ``LABEL:command args``.
   * If *any* entry carries extra arguments (``LABEL:...`` form), a new
     :class:`TestRunSpec` is constructed via ``dataclasses.replace()`` with
     the overridden ``command``.  In this mode ``--only-fut`` / ``--skip-fut``
     may not be combined, and only a single ``--only-test`` entry is allowed.

3. **skip_test** – if non-empty, remove specs with a matching ``label``.
4. **skip_fut** – if non-empty, remove specs whose ``required_fut`` is in the
   set.
5. **only_fut** – if non-empty, keep only specs whose ``required_fut`` is in
   the set.

The result is wrapped in :class:`TestRunSpecs` and returned.

.. mermaid::

    flowchart TD
        A[_TESTRUN_SPECS\nall registered specs] --> B{only_test\nnon-empty?}
        B -- yes, plain labels --> C[keep matching specs]
        B -- yes, with args --> D[replace command\nin matching spec]
        B -- no --> E[keep all]
        C --> F{skip_test\nnon-empty?}
        D --> G[return TestRunSpecs]
        E --> F
        F -- yes --> H[remove matching specs]
        F -- no --> I[keep all]
        H --> J{skip_fut\nnon-empty?}
        I --> J
        J -- yes --> K[remove matching specs]
        J -- no --> L[keep all]
        K --> M{only_fut\nnon-empty?}
        L --> M
        M -- yes --> N[keep matching specs]
        M -- no --> O[keep all]
        N --> P[return TestRunSpecs]
        O --> P

Examples
--------

Run a single test group::

    mptest test --only-test=RUN-TESTS_STANDARD

Run a test group with custom arguments (overrides the registered command)::

    mptest test '--only-test=RUN-TESTS_STANDARD:run-tests.py --test-dirs=micropython'

Skip a slow test::

    mptest test --skip-test=RUN-TESTS_EXTMOD_HARDWARE

Run only tests that exercise WLAN::

    mptest test --only-fut=FUT_WLAN_STA

Skip all Bluetooth tests::

    mptest test --skip-fut=FUT_BT_BLUETOOTH

