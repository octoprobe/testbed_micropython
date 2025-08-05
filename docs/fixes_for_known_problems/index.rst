Fix for known problems
===============================


DUT rpi_pico: Remotely flash
--------------------------------

This will bring the PICO into boot mode and.

.. code-block:: bash

    # Force discover all tentacles
    op query --poweron
    export TENTACLE=5f2c
    # Power off DUT
    op power --serials=$TENTACLE --off dut
    # Press boot button
    op exec-infra --serials=$TENTACLE 'set_relays([(1, True)])'
    # Power on DUT
    op power --serials=$TENTACLE --on dut
    # Release boot button
    op exec-infra --serials=$TENTACLE 'set_relays([(1, False)])'

If automount is enabled, the filesystem will appear, if not:

.. code-block:: bash

    sudo mount /dev/sda1 /tmp/x


If you prefer to use `picotool`:

.. code-block:: bash

    sudo dmesg --follow
    [492022.916948] usb 1-3.1.4.3: new full-speed USB device number 89 using xhci_hcd
    [492023.002413] usb 1-3.1.4.3: New USB device found, idVendor=2e8a, idProduct=0003, bcdDevice= 1.00
    [492023.002432] usb 1-3.1.4.3: New USB device strings: Mfr=1, Product=2, SerialNumber=3
    [492023.002473] usb 1-3.1.4.3: Product: RP2 Boot
    [492023.002484] usb 1-3.1.4.3: Manufacturer: Raspberry Pi
    [492023.002494] usb 1-3.1.4.3: SerialNumber: E0C9125B0D9B

    picotool erase --all --bus 1 --address 89
    or
    wget https://github.com/dwelch67/raspberrypi-pico/blob/main/flash_nuke.uf2
    picotool load flash_nuke.uf2 --bus 1 --address 89

DUT rpi_pico: format crashed filesystem
----------------------------------------

.. code-block:: python

    import vfs, rp2
    vfs.VfsLfs2.mkfs(rp2.Flash(), progsize=256)

DUT pyboard: format crashed filesystem
----------------------------------------

See: https://docs.micropython.org/en/latest/reference/filesystem.html

.. code-block:: python

    import vfs, pyb, os
    vfs.umount('/flash')
    vfs.VfsLfs2.mkfs(pyb.Flash(start=0))
    vfs.mount(pyb.Flash(start=0), '/flash')
    os.chdir('/flash')


DUT NUCLEO_WB55: Remotely flash bluetooth stack
---------------------------------------------------

This will bring the NUCLEO_WB55 into boot mode.

.. code-block:: bash

    # Force discover all tentacles
    op query --poweron
    export TENTACLE=2f2c
    # Power off DUT
    op power --serials=$TENTACLE --off dut
    # Press boot button
    op exec-infra --serials=$TENTACLE 'set_relays([(1, True)])'
    # Power on DUT
    op power --serials=$TENTACLE --on dut
    # Release boot button
    op exec-infra --serials=$TENTACLE 'set_relays([(1, False)])'

Flash bluetooth stack

.. code-block:: bash

    dfu-util -a 0 -D micropy_nucleo_wb55.dfu

Read bluetooth stack version

.. code-block:: bash

    # Before flashing
    >>> import stm
    >>> stm.rfcore_fw_version(0)
    (0, 5, 3, 0, 0)
    >>> stm.rfcore_fw_version(1)
    (0, 5, 1, 0, 0)

    # After flashing
    >>> stm.rfcore_fw_version(0)
    (1, 1, 0, 0, 0)
    >>> stm.rfcore_fw_version(1)
    (1, 10, 0, 0, 1)

DUT NUCLEO_WB55: format crashed filesystem
------------------------------------------

.. code-block:: python

    import vfs, pyb
    vfs.VfsFat.mkfs(pyb.Flash(start=0))
