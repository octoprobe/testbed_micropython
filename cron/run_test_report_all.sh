#!/usr/bin/env bash

git fetch --all -p
git reset --hard origin/main

. ~/.profile

mptest test --micropython-tests=https://github.com/micropython/micropython.git~17782 --firmware-build=https://github.com/micropython/micropython.git~17782 --no-multiprocessing
mptest report --testresults=./testresults

mptest test --micropython-tests=https://github.com/micropython/micropython.git@master --firmware-build=https://github.com/micropython/micropython.git@master --no-multiprocessing
mptest report --testresults=./testresults

