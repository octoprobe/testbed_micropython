Design: TestRunSpec
=============================

Overview
--------

A :class:`TestRunSpec` is a **static, immutable description** of one test
group.  It answers the question *"which command should be run, on which class
of tentacle, and how?"*.

Each spec is a singleton constant defined in the ``testrunspecs/`` package::

    TESTRUNSPEC_RUNTESTS_STANDARD = TestRunSpec(
        label="RUN-TESTS_STANDARD",
        label_intuitive="run-tests.py",
        command=["run-tests.py"],
        required_fut=EnumFut.FUT_MCU_ONLY,
        requires_reference_tentacle=False,
        testrun_class=TestRunRunTests,
        timeout_s=3660.0,
        ...
    )

All singletons are registered in ``_TESTRUN_SPECS`` inside
``util_testrunner.py`` and selected at startup by ``get_testrun_specs()``.

During a test run the :class:`TestRunSpec` also becomes **mutable in one
regard**: its ``tsvs_todo`` list shrinks as individual :class:`TestRun`
instances are completed.

Key fields
----------

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Field
     - Type
     - Purpose
   * - ``label``
     - ``str``
     - Unique identifier, e.g. ``RUN-TESTS_EXTMOD_HARDWARE``.  Used by
       ``--only-test`` / ``--skip-test`` on the command line.
   * - ``label_intuitive``
     - ``str``
     - Human-readable shorthand shown in reports, e.g. ``run-tests.py --via-mpy``.
   * - ``command``
     - ``list[str]``
     - The executable and its fixed arguments, e.g.
       ``["run-tests.py", "--test-dirs=extmod_hardware"]``.
   * - ``required_fut``
     - ``EnumFut``
     - The *Feature Under Test* that a tentacle must declare in its inventory
       to be eligible, e.g. ``FUT_MCU_ONLY``, ``FUT_WLAN_STA``.
   * - ``requires_reference_tentacle``
     - ``bool``
     - When ``True`` a second tentacle is needed (e.g. WLAN-AP), and the
       ``tentacle_reference`` from ``Args.reference_board`` is passed to every
       :class:`TestRun`.
   * - ``testrun_class``
     - ``type[TestRun]``
     - The concrete subclass instantiated when a tentacle is ready.
   * - ``tsvs_todo``
     - ``TentacleSpecVariants``
     - The remaining board-variants still to be tested.  Populated by
       ``assign_tentacles()`` and shrinks as tests complete.
   * - ``timeout_s``
     - ``float``
     - Hard wall-clock limit for one :class:`TestRun` of this spec.
   * - ``priority``
     - ``int``
     - Scheduling hint (higher = run earlier).

Relationship to tentacle types
-------------------------------

The chain from hardware inventory down to an individual test execution goes
through four distinct classes.

.. mermaid::

    classDiagram
        direction TB

        class TentacleSpecMicropython {
            board: str
            futs: set[EnumFut]
            build_variants: list[str]
        }
        note for TentacleSpecMicropython "Static per-board description\nlived in tentacles_inventory.py"

        class TentacleSpecVariant {
            tentacle: TentacleMicropython
            variant: str
            role: TestRole
        }
        note for TentacleSpecVariant "One (board, variant, role) tuple\ncreated at assign_tentacles() time"

        class TentacleSpecVariants {
            list[TentacleSpecVariant]
        }
        note for TentacleSpecVariants "The todo-list of a TestRunSpec"

        class TestRunSpec {
            label: str
            required_fut: EnumFut
            tsvs_todo: TentacleSpecVariants
            generate() -> TestRun
        }

        class TestRun {
            testrun_spec: TestRunSpec
            tentacle_variant: TentacleSpecVariant
            tentacle_reference: TentacleMicropython | None
        }
        note for TestRun "One concrete execution\n(one board-variant on one tentacle)"

        TentacleSpecMicropython "1" --> "0..*" TentacleSpecVariant : expanded into
        TentacleSpecVariant "0..*" --* TentacleSpecVariants : contained in
        TentacleSpecVariants "1" --* TestRunSpec : tsvs_todo
        TestRunSpec "1" --> "0..*" TestRun : generate()
        TentacleSpecVariant "1" --* TestRun : tentacle_variant

``TentacleSpecMicropython`` — the static board description
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Defined once per physical board type in the tentacle inventory.  It holds the
board name, the set of supported FUTs, and the ``build_variants`` tag which
lists the firmware variants the board can run (e.g. ``["", "RISCV"]`` for the
RP2350).

``TentacleSpecVariant`` — one (tentacle, variant, role) tuple
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Created at runtime by ``tentacle_spec_2_tsvs()`` when ``assign_tentacles()``
expands each tentacle according to its ``build_variants``.  For a RP2350 this
yields two entries: ``RPI_PICO2("")`` and ``RPI_PICO2("RISCV")``.

When a test requires two tentacles (e.g. WLAN STA ↔ AP), two
:class:`TentacleSpecVariant` objects are created for the same tentacle, one
with ``role=ROLE_INSTANCE0`` and one with ``role=ROLE_INSTANCE1``.

``TentacleSpecVariants`` — the todo-list
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A typed ``list[TentacleSpecVariant]``.  It is stored as
``TestRunSpec.tsvs_todo`` and acts as the scheduler's work queue for that
spec.  Every time a :class:`TestRun` finishes, ``mark_as_done()`` removes the
corresponding entry.  When the list is empty, this spec is fully done.

``TestRun`` — one concrete execution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Produced by ``TestRunSpec.generate()`` when a tentacle is available *and* its
firmware has been built.  It carries:

* ``testrun_spec`` — back-reference to the owning spec
* ``tentacle_variant`` — which physical board and variant to test
* ``tentacle_reference`` — optional second tentacle for multi-device tests

``TestRun.test()`` (overridden per subclass) contains the actual subprocess
call to e.g. ``run-tests.py``.

Lifecycle of ``tsvs_todo``
--------------------------

.. code-block::

    assign_tentacles()          # fills tsvs_todo from ConnectedTentacles
          |
          v
    generate()                  # yields TestRun for each ready (tentacle, variant)
          |
          v
    TestRun executes
          |
          v
    mark_as_done()              # removes the TentacleSpecVariant from tsvs_todo
          |
          v
    tsvs_todo empty → spec done

``assign_tentacles()`` is called once after ``get_testrun_specs()`` resolves
the active set.  ``generate()`` is called repeatedly by the
:class:`TestBartender` scheduler – it only yields a :class:`TestRun` if the
required firmware is already built and the tentacle is not busy.
