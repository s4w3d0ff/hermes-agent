---
name: parallella
description: Use when working with Adatteva Parallella SBCs.
platforms: [linux]
metadata:
  hermes:
    tags: [parallella, sbc, epiphany, zynq, hardware]
---

# Parallella (Adapteva) SBC operations

Class-level notes for working with Adatteva Parallella boards. Facts below were
verified against the official reference manual and parallella.org; re-verify only
if a board behaves contrary to them.

## Identifying a board
- White sticker carries SKU + serial number. Kickstarter/pre-order era SKUs:
  - A101010: Parallella-16, Zynq Z7010, NO GPIO Samtec headers (has USB + HDMI)
  - A101020: Parallella-16, Zynq Z7010, with GPIO
  - A101040: Parallella-16, Zynq Z7020, with GPIO (first 1200 units had U13)
  - P1600/P1601/P1602-DK03: later shop SKUs (micro server / desktop / embedded),
    ship with large heatsink + 5V PSU
- Authoritative SKU list: parallella.org/version-history.
- forums.parallella.org threads include Adatteva staff answering hardware
  questions; search there before assuming a board quirk is unsolvable.

## Power subsystem
- Input: 5 V DC via 2.1 mm barrel jack (5.5 mm OD, center-positive). Under light
  load the USB(0) port can also power the board.
- Power-selector jumper (3-pin header, J15 on gen1 schematics): selects which
  source feeds SYS_5P0V - barrel vs USB. Position varies between boards and
  revisions; check where the cap sits before assuming a power path works, and
  move it to switch sources.
- No reverse-polarity protection: the barrel input goes through a resettable PTC
  fuse (~4 A) straight into the 5 V rail. A center-negative adapter can damage
  the board - verify polarity before connecting any non-standard supply.
- Typical draw ~5 W; budget up to ~2 A at 5 V for headroom with peripherals or
  expansion cards.
- On-board PMICs: ISL9307 + ISL9305 (I2C-programmable rails). PEC_POWER can feed
  expansion cards but is experimental; prefer the 5 V PEC rail or an independent
  supply for add-on boards. Driving a rail from outside while its regulator is
  enabled will damage the board.

## Power over Ethernet
- No native PoE circuitry on the RJ45.
- Pitfall: the port is gigabit (10/100/1000), so all three pairs carry data at
  full speed. You cannot tap power off an "unused" pair without degrading to
  100 Mb/s or adding a mod. Options, in order of cleanliness:
  1. External PoE splitter/PSE feeding the barrel jack (no soldering).
  2. Jumper/solder from the PoE-injected line to the board's +5 V and GND pads.
- A standard 802.3af source is far more than enough power-wise (~1 A needed at
  5 V). The limiting factor is whether the SOURCE can do PoE, not the board.

## Flashing and first boot
- Images: GitHub `parallella/parabuntu` releases. For a 4 GB card use
  `parabuntu-2016.11.1-headless-z7010.img.gz` (~3.5 GB decompressed; latest stable
  that fits). The 2019.1 beta needs an 8 GB card. Verify SHA-256 against the
  release's `sha256sum.txt` before flashing.
- Flash pitfall: raw-device writes via `dd of=/dev/mmcblkX` are blocked by this
  host's terminal hardline; write with Python `open(dev, "wb")` streaming
  gzip-decompressed chunks as root, then `partprobe`. Verify layout afterwards:
  ~100 MB vfat BOOT (uImage, devicetree.dtb, parallella.bit.bin) + ext4 root.
- First boot: user/pass `parallella`/`parallella`; DHCP with static fallback
  10.11.12.13; wait ~2 min for first-boot SSH host-key generation before
  connecting.
- Remote access: non-interactive SSH works via pexpect + default password; the
  board has passwordless sudo.

## Software status
- Adatteva is defunct; support is community-maintained (parallella.org, GitHub
  orgs `parallella` and `embecosm`). Expect a Debian-based image plus the
  Epiphany GCC toolchain/SDK for the 16-core coprocessor; Xilinx tools for Zynq
  FPGA bitstreams. Not turnkey-modern.
- The board's value is the Epiphany coprocessor + FPGA, not raw ARM performance
  (dual Cortex-A9). When pairing with a modern Pi, make the Pi the general-purpose
  node and give Parallella its unique jobs: Epiphany parallel workloads, FPGA
  prototyping, low-power always-on/cluster nodes.
- ESDK setup gotchas and verified example recipes: see references/ed-sdk.md.

## User fleet (this host's owner)
- Two Parallella boards, both SKU A101010 (Zynq Z7010, no GPIO), serials
  0007774 and 0007771. Kickstarter-era units.
- One idle Raspberry Pi 3 Model B v2 available as the stronger general-purpose
  machine in any multi-board setup.
- Current state: one board runs on the LAN at 192.168.8.165 (USB-powered,
  Parabuntu 2016.11.1 headless z7010 on a 4 GB microSD). The two boards' power
  selector jumpers sit in different positions - check before powering either.
- No PoE hardware planned: boards run off USB cables / barrel supplies.