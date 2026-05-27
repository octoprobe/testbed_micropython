Design: Pull requests
=============================

Workflow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Trigger: https://reports.octoprobe.org/jobs/test_pr

  * reports.octoprobe.org
    * Given: PR 17782
    * `gh`:

        * commit
        * changed file list
    
    * `gh`: Get comment from https://github.com/micropython/micropython/pull/17782

        * commit of last test

    * If commits equal: Stop

    * `mptest changed-file-list` -> ports to be tested
    * Start github action 

  * Github action

    * As https://github.com/octoprobe/testbed_micropython/actions

    * Eventually: Update comment on https://github.com/micropython/micropython/pull/17782
