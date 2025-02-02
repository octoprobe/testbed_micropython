set -euox pipefail

export IDF_VER=v5.2.2
export TAG=build-micropython-esp32
export ORGANISATION=hmaerki
# export ORGANISATION=micropython

git clone --depth 1 --branch $IDF_VER --filter=tree:0 https://github.com/espressif/esp-idf.git

docker build -t $ORGANISATION/$TAG:$IDF_VER \
    --build-arg IDF_CLONE_BRANCH_OR_TAG=v5.2.2 \
    --build-arg IDF_CLONE_SHALLOW=1 \
    --build-arg IDF_INSTALL_TARGETS=all \
    esp-idf/tools/docker

# docker push $ORGANISATION/$TAG:$IDF_VER
