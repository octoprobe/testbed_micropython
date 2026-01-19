#!/usr/bin/env bash

BRANCH="${1:-master}"
GIT="${2:-https://github.com/micropython/micropython.git}"
REPO=${GIT}${BRANCH}

git fetch --all -p
git reset --hard origin/main

. ~/.profile

mptest test --micropython-tests="$REPO" --firmware-build="$REPO" --no-multiprocessing
mptest report --testresults=./testresults
