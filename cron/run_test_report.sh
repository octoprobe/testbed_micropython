#!/usr/bin/env bash

BRANCH="${1:-master}"
GIT="${2:-https://github.com/micropython/micropython.git}"
REPO=${GIT}${BRANCH}

git fetch --all -p
git reset --hard origin/main

. ~/.profile

DIRECTORY_REPO=$(git rev-parse --show-toplevel)
[[ -d "${DIRECTORY_REPO}/.git" ]] || { echo "ERROR: '${DIRECTORY_REPO}/.git' is not a directory"; exit 1; }

mptest test --testresults=$DIRECTORY_REPO/testresults --micropython-tests="$REPO" --firmware-build="$REPO" --multiprocessing --count=3 --skip-fut=FUT_WLAN --skip-fut=FUT_BLE 
mptest report --testresults=$DIRECTORY_REPO/testresults --email=buhtig.hans.maerki@ergoinfo.ch --email=damien@micropython.org 
