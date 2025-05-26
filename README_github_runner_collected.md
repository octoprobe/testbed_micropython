# Github selfhosted runner

Links:
* https://youtu.be/SASoUr9X0QA?si=2C7SYQ-xysAD0daL
* https://youtu.be/lD0t-UgKfEo?si=wXZ3oIgaFJUACeJ5

* https://github.com/myoung34/docker-github-actions-runner
* https://github.com/docker/github-actions
* https://github.com/actions/actions-runner-controller
* https://github.com/actions/runner-images
* https://github.com/actions/runner

Github actions
  * https://github.com/marketplace/actions/pytest-coverage-comment
  * https://github.com/MishaKav/pytest-coverage-comment
  * https://github.com/marketplace/actions/run-pytest

## Prepare github

https://github.com/hmaerki/experiment_microoctopus/settings/actions/runners/new


## Prepare runner

```bash
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64-2.321.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.321.0/actions-runner-linux-x64-2.321.0.tar.gz
echo "ba46ba7ce3a4d7236b16fbe44419fb453bc08f866b24f04d549ec89f1722a29e  actions-runner-linux-x64-2.321.0.tar.gz" | shasum -a 256 -c
tar xzf ./actions-runner-linux-x64-2.321.0.tar.gz

./config.sh --url https://github.com/octoprobe/testbed_micropython_runner --token xxx
./run.sh
```

## Config the runner

```text
Group: Default (should be octoprobe)
Name of runner: ch-wetzikon-1
labels: octoprobe,testbed_micropython
work folder: _work
```
