set -x

while true; do
    op power --on dut
    sleep 1
    op power --off dut
    sleep 1
done
