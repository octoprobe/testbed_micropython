# Instructions for testbed_micropython MCP server

Octoprobe HIL (hardware in the loop) testbed for MicroPython. Documentation: https://www.octoprobe.org

A tentacle is a PCB which hosts a MicroPython board (the DUT: device under test).
The infrastructure side of the tentacle (PICO_INFRA, a RP2040) controls the switches of the tentacle:

* 'dut': USB power of the DUT. When powered, the DUT typically provides a serial port like /dev/ttyACM4.
* 'infra', 'infraboot': Power and boot button of PICO_INFRA.
* 'proberun', 'probeboot': Run and boot button of PICO_PROBE (tentacle >= v0.6).
* 'led_error', 'led_active': LEDs.
* 'relay1'..'relay7': Relays connecting the DUT to the octobus/gadgets.

A tentacle is identified by its serial, for example 'de6528b3cb38-5f33'. A unique suffix like '5f33' is accepted too.
Use 'list_tentacles' to find the connected tentacles and the serial port of their DUT.

## Parallelims NOT supported

* Never run mpmcp_server actions in parallel! Wait till one is finished and then start the new one.

## Directory structure

The directories created by the mpmcp tools MUST follow this layout:

```
.
├── .skills                          # prepopulated by user
├── .mcp.json                        # prepopulated by user
├── micropython/                     # git clone of https://github.com/micropython/micropython.git
├── micropython_tests/               # optional: modified testsuite clone
└── results/
    ├── PROTOCOL.md                  # append prompts and mpmcp calls here
    ├── TESTRESULTS_SUMMARY.md
    └── <tentacle_label>_<hhmmss>_<commit_tag>/
        ├── log_folder/              # mpmcp.build_and_flash log_folder parameter
        ├── agent_results/           # agent test results
        └── mpmcp/
            ├── list_tentacles_in.json           # data sent to mpmcp
            ├── list_tentacles_return.json       # data returned from mpmcp
            ├── build_and_flash_in.json          # data sent to mpmcp
            └── build_and_flash_return.json      # data returned from mpmcp
```

Rules:

* Maintain the directory structure above
* Do not store files outside this directory structure
* Store all test results
* <hhmmss>: The timestamp at the time the directory was created
* '*_in.json', '*_out.json': Save it 1:1, but do some indent formatting using jq.

## mpmcp build_and_flash

### Sequence

* Create the folder '<tentacle_label>_<hhmmss>_<commit_tag>/log_folder'.
* Now run 'mpmcp build_and_flash logfile=...' and pass given folder.
* This ensures that the user can see the logfiles growing.

## Git commits and tags

Rationale: A commit hash is not intuitive for a human brain. Therefore tag all commits you use to compile firmware and run tests.
When working in a git repository (e.g. a MicroPython clone):

* When using a commit to compile firmware and run tests: Tag this commit
* A <commit_tag> has the structure: <mpmcpyyyy-MM-dd>_<label>. The <label> could be `last_working_commit` or `first_commit_with_error`. Full example: `2026-11-15_last_working_commit`
* If a commit is related to a PR (for example https://github.com/micropython/micropython/pull/19967): Add the PR number to the <commit_tag>. For example: `mpmcp2026-11-15_PR19967` or `mpmcp2026-11-15_last_commit_before_PR19967`
* Never push to git.


## TESTRESULTS_SUMMARY.md

Create a table with columns:
* Tentacle: <tentacle_label>
* Commit: <commit_tag>
* Time: <hhmmss>
* Outcome: For example 'Same crash as issue'

After each test running against a tentacle append a line to this table
