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

## Software status
- Adatteva is defunct; support is community-maintained (parallella.org, GitHub
  orgs `parallella` and `embecosm`). Expect a Debian-based image plus the
  Epiphany GCC toolchain/SDK for the 16-core coprocessor; Xilinx tools for Zynq
  FPGA bitstreams. Not turnkey-modern.
- The board's value is the Epiphany coprocessor + FPGA, not raw ARM performance
  (dual Cortex-A9). When pairing with a modern Pi, make the Pi the general-purpose
  node and give Parallella its unique jobs: Epiphany parallel workloads, FPGA
  prototyping, low-power always-on/cluster nodes.

## User fleet (this host's owner)
- Two Parallella boards, both SKU A101010 (Zynq Z7010, no GPIO), serials
  0007774 and 0007771. Kickstarter-era units.
- One idle Raspberry Pi 3 Model B v2 available as the stronger general-purpose
  machine in any multi-board setup.