# Error


## Precondition

16 port RSH hub
11 tentacles connected
`op power --off dut`

```bash
op query --verbose
tentacle 1-1.3.1: e464144813421830 /dev/ttyACM1
tentacle 1-1.3.2: e464144813541133 /dev/ttyACM4
tentacle 1-1.3.3.1: e46414481354472b /dev/ttyACM9
tentacle 1-1.3.3.2: e46340474b592d2d /dev/ttyACM11
tentacle 1-1.3.3.3: e4641448130f2f2c /dev/ttyACM13
usb hub 1-1.3.3.4
tentacle 1-1.3.4.1: e464144813460c30 /dev/ttyACM10
tentacle 1-1.3.4.2: e46340474b174429 /dev/ttyACM12
tentacle 1-1.3.4.3: e46340474b4c2731 /dev/ttyACM14
tentacle 1-1.4.3: e46414481355552b /dev/ttyACM2
tentacle 1-1.4.4: e4641448132a5f2a /dev/ttyACM5
```

## Stimuli: Connect tentacle 3c2a

### A

`op power --off dut`

Connect

```bash
[  664.466957] usb 1-1.1: new high-speed USB device number 49 using xhci_hcd
[  664.556187] usb 1-1.1: New USB device found, idVendor=0424, idProduct=2514, bcdDevice= b.b3
[  664.556207] usb 1-1.1: New USB device strings: Mfr=0, Product=0, SerialNumber=0
[  664.562850] hub 1-1.1:1.0: USB hub found
[  664.562960] hub 1-1.1:1.0: 4 ports detected
[  664.850388] usb 1-1.1.1: new full-speed USB device number 50 using xhci_hcd
[  664.940439] usb 1-1.1.1: New USB device found, idVendor=2e8a, idProduct=0005, bcdDevice= 1.00
[  664.940445] usb 1-1.1.1: New USB device strings: Mfr=1, Product=2, SerialNumber=3
[  664.940447] usb 1-1.1.1: Product: Board in FS mode
[  664.940449] usb 1-1.1.1: Manufacturer: MicroPython
[  664.940450] usb 1-1.1.1: SerialNumber: e464144813113c2a
[  664.954268] cdc_acm 1-1.1.1:1.0: ttyACM0: USB ACM device
```

### B

`op power --on dut`

Connect 

```bash
[  149.907030] usb 1-1.1: new high-speed USB device number 47 using xhci_hcd
[  149.996372] usb 1-1.1: New USB device found, idVendor=0424, idProduct=2514, bcdDevice= b.b3
[  149.996391] usb 1-1.1: New USB device strings: Mfr=0, Product=0, SerialNumber=0
[  150.001020] hub 1-1.1:1.0: USB hub found
[  150.001094] hub 1-1.1:1.0: 4 ports detected
[  150.291438] usb 1-1.1.1: new full-speed USB device number 48 using xhci_hcd
[  150.381296] usb 1-1.1.1: New USB device found, idVendor=2e8a, idProduct=0005, bcdDevice= 1.00
[  150.381302] usb 1-1.1.1: New USB device strings: Mfr=1, Product=2, SerialNumber=3
[  150.381304] usb 1-1.1.1: Product: Board in FS mode
[  150.381306] usb 1-1.1.1: Manufacturer: MicroPython
[  150.381308] usb 1-1.1.1: SerialNumber: e464144813113c2a
[  150.382947] usb 1-1.1.1: Not enough bandwidth for new device state.
[  150.382970] usb 1-1.1.1: can't set config #1, error -28
```

## Stimuli: duts on off

```bash
op power --off dut
lsusb -v 2>&1 | grep missing | wc -l
```
36

```bash
op power --on dut
lsusb -v 2>&1 | grep missing | wc -l
```
47


# Analysis

```bash
lsusb -t
/:  Bus 001.Port 001: Dev 001, Class=root_hub, Driver=xhci_hcd/12p, 480M
    |__ Port 001: Dev 002, If 0, Class=Hub, Driver=hub/4p, 480M
        |__ Port 001: Dev 062, If 0, Class=Hub, Driver=hub/4p, 480M
            |__ Port 001: Dev 063, 12M
        |__ Port 003: Dev 004, If 0, Class=Hub, Driver=hub/4p, 480M
            |__ Port 001: Dev 008, If 0, Class=Hub, Driver=hub/4p, 480M
                |__ Port 001: Dev 012, If 0, Class=Communications, Driver=cdc_acm, 12M
                |__ Port 001: Dev 012, If 1, Class=CDC Data, Driver=cdc_acm, 12M
            |__ Port 002: Dev 011, If 0, Class=Hub, Driver=hub/4p, 480M
                |__ Port 001: Dev 018, If 0, Class=Communications, Driver=cdc_acm, 12M
                |__ Port 001: Dev 018, If 1, Class=CDC Data, Driver=cdc_acm, 12M
            |__ Port 003: Dev 015, If 0, Class=Hub, Driver=hub/4p, 480M
                |__ Port 001: Dev 023, If 0, Class=Hub, Driver=hub/4p, 480M
                    |__ Port 001: Dev 028, If 0, Class=Communications, Driver=cdc_acm, 12M
                    |__ Port 001: Dev 028, If 1, Class=CDC Data, Driver=cdc_acm, 12M
                |__ Port 002: Dev 027, If 0, Class=Hub, Driver=hub/4p, 480M
                    |__ Port 001: Dev 033, If 0, Class=Communications, Driver=cdc_acm, 12M
                    |__ Port 001: Dev 033, If 1, Class=CDC Data, Driver=cdc_acm, 12M
                |__ Port 003: Dev 031, If 0, Class=Hub, Driver=hub/4p, 480M
                    |__ Port 001: Dev 038, If 0, Class=Communications, Driver=cdc_acm, 12M
                    |__ Port 001: Dev 038, If 1, Class=CDC Data, Driver=cdc_acm, 12M
                |__ Port 004: Dev 037, If 0, Class=Hub, Driver=hub/4p, 480M
                    |__ Port 001: Dev 043, 12M
            |__ Port 004: Dev 020, If 0, Class=Hub, Driver=hub/4p, 480M
                |__ Port 001: Dev 025, If 0, Class=Hub, Driver=hub/4p, 480M
                    |__ Port 001: Dev 030, If 0, Class=Communications, Driver=cdc_acm, 12M
                    |__ Port 001: Dev 030, If 1, Class=CDC Data, Driver=cdc_acm, 12M
                |__ Port 002: Dev 029, If 0, Class=Hub, Driver=hub/4p, 480M
                    |__ Port 001: Dev 036, If 0, Class=Communications, Driver=cdc_acm, 12M
                    |__ Port 001: Dev 036, If 1, Class=CDC Data, Driver=cdc_acm, 12M
                |__ Port 003: Dev 034, If 0, Class=Hub, Driver=hub/4p, 480M
                    |__ Port 001: Dev 040, If 0, Class=Communications, Driver=cdc_acm, 12M
                    |__ Port 001: Dev 040, If 1, Class=CDC Data, Driver=cdc_acm, 12M
        |__ Port 004: Dev 006, If 0, Class=Hub, Driver=hub/4p, 480M
            |__ Port 003: Dev 010, If 0, Class=Hub, Driver=hub/4p, 480M
                |__ Port 001: Dev 016, If 0, Class=Communications, Driver=cdc_acm, 12M
                |__ Port 001: Dev 016, If 1, Class=CDC Data, Driver=cdc_acm, 12M
            |__ Port 004: Dev 014, If 0, Class=Hub, Driver=hub/4p, 480M
                |__ Port 001: Dev 021, If 0, Class=Communications, Driver=cdc_acm, 12M
                |__ Port 001: Dev 021, If 1, Class=CDC Data, Driver=cdc_acm, 12M
    |__ Port 003: Dev 046, If 0, Class=Human Interface Device, Driver=usbhid, 1.5M
    |__ Port 003: Dev 046, If 1, Class=Human Interface Device, Driver=usbhid, 1.5M
    |__ Port 007: Dev 005, If 0, Class=Wireless, Driver=btusb, 12M
    |__ Port 007: Dev 005, If 1, Class=Wireless, Driver=btusb, 12M
    |__ Port 008: Dev 009, If 0, Class=Video, Driver=uvcvideo, 480M
    |__ Port 008: Dev 009, If 1, Class=Video, Driver=uvcvideo, 480M
    |__ Port 009: Dev 013, If 0, Class=Vendor Specific Class, Driver=[none], 12M
    |__ Port 010: Dev 019, If 0, Class=Human Interface Device, Driver=usbhid, 12M
    |__ Port 010: Dev 019, If 1, Class=Human Interface Device, Driver=usbhid, 12M
/:  Bus 002.Port 001: Dev 001, Class=root_hub, Driver=xhci_hcd/6p, 5000M
```

The hub is connected to just USB 2 port

```bash
hwinfo --usb-ctrl
21: PCI 14.0: 0c03 USB Controller (XHCI)                        
  [Created at pci.386]
  Unique ID: MZfG.WSu8w7OLTgB
  SysFS ID: /devices/pci0000:00/0000:00:14.0
  SysFS BusID: 0000:00:14.0
  Hardware Class: usb controller
  Model: "Intel Sunrise Point-LP USB 3.0 xHCI Controller"
  Vendor: pci 0x8086 "Intel Corporation"
  Device: pci 0x9d2f "Sunrise Point-LP USB 3.0 xHCI Controller"
  SubVendor: pci 0x17aa "Lenovo"
  SubDevice: pci 0x2237 
  Revision: 0x21
  Driver: "xhci_hcd"
  Driver Modules: "xhci_pci"
  Memory Range: 0xf1320000-0xf132ffff (rw,non-prefetchable)
  IRQ: 126 (12366 events)
  Module Alias: "pci:v00008086d00009D2Fsv000017AAsd00002237bc0Csc03i30"
  Driver Info #0:
    Driver Status: xhci_pci is active
    Driver Activation Cmd: "modprobe xhci_pci"
  Config Status: cfg=new, avail=yes, need=no, active=unknown
```

```bash
hwinfo --usb

# Deleted all but hubs
08: USB 00.0: 10a00 Hub
  [Created at usb.122]
  Unique ID: k4bc.2DFUsyrieMD
  SysFS ID: /devices/pci0000:00/0000:00:14.0/usb1/1-0:1.0
  SysFS BusID: 1-0:1.0
  Hardware Class: hub
  Model: "Linux Foundation 2.0 root hub"
  Hotplug: USB
  Vendor: usb 0x1d6b "Linux Foundation"
  Device: usb 0x0002 "2.0 root hub"
  Revision: "6.11"
  Serial ID: "0000:00:14.0"
  Driver: "hub"
  Speed: 480 Mbps
  Module Alias: "usb:v1D6Bp0002d0611dc09dsc00dp01ic09isc00ip00in00"
  Config Status: cfg=new, avail=yes, need=no, active=unknown

12: USB 00.0: 10a00 Hub
  [Created at usb.122]
  Unique ID: pBe4.xYNhIwdOaa6
  SysFS ID: /devices/pci0000:00/0000:00:14.0/usb2/2-0:1.0
  SysFS BusID: 2-0:1.0
  Hardware Class: hub
  Model: "Linux Foundation 3.0 root hub"
  Hotplug: USB
  Vendor: usb 0x1d6b "Linux Foundation"
  Device: usb 0x0003 "3.0 root hub"
  Revision: "6.11"
  Serial ID: "0000:00:14.0"
  Driver: "hub"
  Module Alias: "usb:v1D6Bp0003d0611dc09dsc00dp03ic09isc00ip00in00"
  Config Status: cfg=new, avail=yes, need=no, active=unknown
```

```bash
lsusb -t
/:  Bus 001.Port 001: Dev 001, Class=root_hub, Driver=xhci_hcd/12p, 480M
    |__ Port 003: Dev 046, If 0, Class=Human Interface Device, Driver=usbhid, 1.5M
    |__ Port 003: Dev 046, If 1, Class=Human Interface Device, Driver=usbhid, 1.5M
    |__ Port 007: Dev 005, If 0, Class=Wireless, Driver=btusb, 12M
    |__ Port 007: Dev 005, If 1, Class=Wireless, Driver=btusb, 12M
    |__ Port 008: Dev 009, If 0, Class=Video, Driver=uvcvideo, 480M
    |__ Port 008: Dev 009, If 1, Class=Video, Driver=uvcvideo, 480M
    |__ Port 009: Dev 013, If 0, Class=Vendor Specific Class, Driver=[none], 12M
    |__ Port 010: Dev 019, If 0, Class=Human Interface Device, Driver=usbhid, 12M
    |__ Port 010: Dev 019, If 1, Class=Human Interface Device, Driver=usbhid, 12M
/:  Bus 002.Port 001: Dev 001, Class=root_hub, Driver=xhci_hcd/6p, 5000M
```

With RSH 16 port hub connected. 

Why did it connect to USB2?

```bash
lsusb -t
/:  Bus 001.Port 001: Dev 001, Class=root_hub, Driver=xhci_hcd/12p, 480M
    |__ Port 001: Dev 098, If 0, Class=Hub, Driver=hub/4p, 480M
        |__ Port 001: Dev 099, If 0, Class=Hub, Driver=hub/4p, 480M
            |__ Port 001: Dev 101, If 0, Class=Communications, Driver=cdc_acm, 12M
            |__ Port 001: Dev 101, If 1, Class=CDC Data, Driver=cdc_acm, 12M
        |__ Port 003: Dev 109, If 0, Class=Hub, Driver=hub/4p, 480M
            |__ Port 001: Dev 110, If 0, Class=Hub, Driver=hub/4p, 480M
                |__ Port 001: Dev 113, If 0, Class=Communications, Driver=cdc_acm, 12M
                |__ Port 001: Dev 113, If 1, Class=CDC Data, Driver=cdc_acm, 12M
                |__ Port 003: Dev 116, If 0, Class=Communications, Driver=cdc_acm, 12M
                |__ Port 003: Dev 116, If 1, Class=CDC Data, Driver=cdc_acm, 12M
                |__ Port 003: Dev 116, If 2, Class=Vendor Specific Class, Driver=[none], 12M
            |__ Port 002: Dev 111, If 0, Class=Hub, Driver=hub/4p, 480M
                |__ Port 001: Dev 115, If 0, Class=Communications, Driver=cdc_acm, 12M
                |__ Port 001: Dev 115, If 1, Class=CDC Data, Driver=cdc_acm, 12M
                |__ Port 003: Dev 118, If 0, Class=Communications, Driver=cdc_acm, 480M
                |__ Port 003: Dev 118, If 1, Class=CDC Data, Driver=cdc_acm, 480M
            |__ Port 003: Dev 112, If 0, Class=Hub, Driver=hub/4p, 480M
                |__ Port 001: Dev 117, If 0, Class=Hub, Driver=hub/4p, 480M
                    |__ Port 001: Dev 121, If 0, Class=Communications, Driver=cdc_acm, 12M
                    |__ Port 001: Dev 121, If 1, Class=CDC Data, Driver=cdc_acm, 12M
                    |__ Port 003: Dev 125, If 0, Class=Vendor Specific Class, Driver=cp210x, 12M
                |__ Port 002: Dev 120, If 0, Class=Hub, Driver=hub/4p, 480M
                    |__ Port 001: Dev 126, If 0, Class=Communications, Driver=cdc_acm, 12M
                    |__ Port 001: Dev 126, If 1, Class=CDC Data, Driver=cdc_acm, 12M
                    |__ Port 003: Dev 007, If 0, Class=Vendor Specific Class, Driver=ch341, 12M
                |__ Port 003: Dev 123, If 0, Class=Hub, Driver=hub/4p, 480M
                    |__ Port 001: Dev 006, If 0, Class=Communications, Driver=cdc_acm, 12M
                    |__ Port 001: Dev 006, If 1, Class=CDC Data, Driver=cdc_acm, 12M
                    |__ Port 003: Dev 012, 12M
                |__ Port 004: Dev 002, If 0, Class=Hub, Driver=hub/4p, 480M
                    |__ Port 001: Dev 010, 12M
                    |__ Port 003: Dev 015, 12M
            |__ Port 004: Dev 114, If 0, Class=Hub, Driver=hub/4p, 480M
                |__ Port 001: Dev 119, If 0, Class=Hub, Driver=hub/4p, 480M
                    |__ Port 001: Dev 124, If 0, Class=Communications, Driver=cdc_acm, 12M
                    |__ Port 001: Dev 124, If 1, Class=CDC Data, Driver=cdc_acm, 12M
                    |__ Port 003: Dev 004, If 0, Class=Vendor Specific Class, Driver=cp210x, 12M
                |__ Port 002: Dev 122, If 0, Class=Hub, Driver=hub/4p, 480M
                    |__ Port 001: Dev 003, If 0, Class=Communications, Driver=cdc_acm, 12M
                    |__ Port 001: Dev 003, If 1, Class=CDC Data, Driver=cdc_acm, 12M
                    |__ Port 003: Dev 011, 12M
                |__ Port 003: Dev 127, If 0, Class=Hub, Driver=hub/4p, 480M
                    |__ Port 001: Dev 008, If 0, Class=Communications, Driver=cdc_acm, 12M
                    |__ Port 001: Dev 008, If 1, Class=CDC Data, Driver=cdc_acm, 12M
                    |__ Port 003: Dev 014, 12M
        |__ Port 004: Dev 102, If 0, Class=Hub, Driver=hub/4p, 480M
            |__ Port 003: Dev 103, If 0, Class=Hub, Driver=hub/4p, 480M
                |__ Port 001: Dev 105, If 0, Class=Communications, Driver=cdc_acm, 12M
                |__ Port 001: Dev 105, If 1, Class=CDC Data, Driver=cdc_acm, 12M
                |__ Port 003: Dev 107, If 0, Class=Communications, Driver=cdc_acm, 12M
                |__ Port 003: Dev 107, If 1, Class=CDC Data, Driver=cdc_acm, 12M
            |__ Port 004: Dev 104, If 0, Class=Hub, Driver=hub/4p, 480M
                |__ Port 001: Dev 106, If 0, Class=Communications, Driver=cdc_acm, 12M
                |__ Port 001: Dev 106, If 1, Class=CDC Data, Driver=cdc_acm, 12M
                |__ Port 003: Dev 108, If 0, Class=Communications, Driver=cdc_acm, 12M
                |__ Port 003: Dev 108, If 1, Class=CDC Data, Driver=cdc_acm, 12M
    |__ Port 003: Dev 087, If 0, Class=Human Interface Device, Driver=usbhid, 1.5M
    |__ Port 003: Dev 087, If 1, Class=Human Interface Device, Driver=usbhid, 1.5M
    |__ Port 007: Dev 005, If 0, Class=Wireless, Driver=btusb, 12M
    |__ Port 007: Dev 005, If 1, Class=Wireless, Driver=btusb, 12M
    |__ Port 008: Dev 009, If 0, Class=Video, Driver=uvcvideo, 480M
    |__ Port 008: Dev 009, If 1, Class=Video, Driver=uvcvideo, 480M
    |__ Port 009: Dev 013, If 0, Class=Vendor Specific Class, Driver=[none], 12M
    |__ Port 010: Dev 019, If 0, Class=Human Interface Device, Driver=usbhid, 12M
    |__ Port 010: Dev 019, If 1, Class=Human Interface Device, Driver=usbhid, 12M
/:  Bus 002.Port 001: Dev 001, Class=root_hub, Driver=xhci_hcd/6p, 5000M
```
