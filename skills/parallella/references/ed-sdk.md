# Epiphany ESDK (2016.11) on Parabuntu

Toolchain ships at `/opt/adapteva/esdk` (symlink to `esdk.2016.11`).

## Environment setup
- `setup.sh` silently no-ops unless EPIPHANY_HOME is set first:
  ```sh
  export EPIPHANY_HOME=/opt/adapteva/esdk
  . $EPIPHANY_HOME/setup.sh
  ```
  Without the export it only prints "Please set the EPIPHANY_HOME..." and exports
  nothing, so `e-gcc` is missing from PATH with no error.
- The compiler in this SDK vintage is `e-gcc`; there is NO `e-cc` binary (older
  docs/examples may reference it).
- Host-side programs link `-le-hal -le-loader`; device side compiles with
  `e-gcc ... -T $EPIPHANY_HDF ... -le-lib`.

## Examples (pre-cloned on the board)
- `/home/parallella/epiphany-examples` - official Adapteva set (`cpu/`, `dma/`,
  `io/`, `emesh/`, ...).
- `/home/parallella/parallella-examples` - community set (mandelbrot, eprime2,
  game-of-life, vfft, nbody_mpi, ...).
- Build with the example's own `./build.sh` or `make`. Run scripts may call
  `sudo -E` and need EPIPHANY_HDF; they work as-is since sudo is passwordless.

## Verified working (16-core mesh confirmed)
- `cpu/basic_math`: prints per-op cycle counts on the mesh (add/sub/mul = 5,
  div = 47, powf ~175k). Fastest end-to-end smoke test of host -> e-loader ->
  cores.
- `mandelbrot`: full render in ~20 s; the SREC deprecation warning is harmless.
- `eprime2 <N>`: one task per core, prints a line per core (4x4 grid) plus
  totals. N=1e8 took ~3 m 30 s with host CPU time near zero - proof the work ran
  on the mesh, not the ARM side.

## Mesh facts
- SKU A101010 = 4x4 Epiphany-III grid (16 cores); `platform.hdf` reports
  EMEM_SIZE 0x02000000. Confirm core count from per-core output lines rather
  than trusting a single sysfs field.

## Verified memory map (parallella1, 2016.11, live-probed 2026-10-02)

A9 physical (Zynq-7010, kernel at physical 0x0, 1GB DDR):

| A9 physical | contents |
|---|---|
| 0x00000000-0x0A00000+ | **running Linux kernel** (zImage entry stub at 0x0; kallsyms `_stext`=0x0). Do not write here except what e-loader does (see danger note). |
| 0x00000000-0x3DFFFFFF | DDR (960MB usable per `/proc/device-tree/memory` reg `[0x0, 0x3e000000]`) |
| **0x3E000000-0x3F000000** | **EZ shared DRAM window (A9 side of the EZ's external memory)** |
| **0x40000000+ (PL)** | **DANGER: reads to unmapped PL targets hang the A9 in an uninterruptible bus-wait. `timeout` cannot kill a stuck page fault. Board needs a power cycle. Never probe PL addresses without a known-good slave.** |

EZ side (per core, from ESDK ref manual Fig 1.2 + fast.ldf/internal.ldf):

| EZ address | contents |
|---|---|
| 0x00000-0x7FFF | local SRAM 32KB (4 x 8KB banks: 0/0x2000/0x4000/0x6000) |
| 0xF0000-0xF8FFF | memory-mapped core registers |
| 0x80800000+ | GLOBAL space: core (chip row 32-39, col 8-15) at `0x80000000\|(row<<26)\|(col<<20)\|off`. Parallella's 16 cores = chip (32,8)-(39,15); group (0,0)-(3,3) in e-loader terms. First core = 0x80800000. |
| **0x8E000000-0x8FFFFFFF** | external/shared DRAM (32MB default emem) |

**The offset rule (marker-verified): EZ addr = A9 addr + 0x50000000** for the
A9's DDR, i.e. A9 0x3e000000 == EZ 0x8e000000. The EZ's DRAM port can see the
whole 1GB of A9 DDR (A9 0x0 == EZ 0x50000000) - this is why e-loader's image,
written to A9 0x0 (PAL's `sram_base=0` mapping), is fetchable and executable
by the cores.

Working 16-core proof (`e-loader -s t8 0 0 4 4`): each core decoded its
`coreid` register (`row=(id>>6)&0x3f`, `col=id&0x3f`, subtract (32,8) for group
corenum=row*4+col) and wrote 1000+corenum to EZ 0x8e002000+corenum*4 =
A9 0x3e002000+corenum*4. Result: **16/16 slots correct (0x3e8..0x3f7)**.

## Pitfalls (all hit in practice)
- **e-read / e-write for core-local memory are UNRELIABLE on this image.**
  Proven: `e-write 0 0 0x3000 0xABCD0001` reports success, but neither
  e-read nor raw /dev/mem at A9 0x3000 shows the value, and e-read vs raw at
  the same address return different data. PAL's chip table gives
  `sram_base=0` (E64G401), so its core-local mapping lands in A9 kernel
  memory; its read and write paths are mutually inconsistent. Use the shared
  DRAM window for all A9<->EZ data exchange; use e-server + e-gdb if you must
  inspect core-local state.
- **e-loader writes each core's image to A9 0x0 + (id<<20)** (id =
  (row<<6)|col for the group) = A9 kernel/DDR offsets 0x4000000, 0x8000000,
  0xC000000, ... for a 4x4 group. It overwrites ~16MB of live kernel memory
  scattered in low DDR. Boards survive it in practice, but it is a latent
  crash source under memory pressure.
- **Inter-core addressing from the EZ side needs the global form**
  (0x80800000+base): a plain local offset (e.g. `0x2000`) writes the core's
  OWN SRAM, not a neighbor's. `e_get_global_address()` in e-lib does this.
- **`e-hw-rev` prints "Unknown generation"** on this image - the EZ responds
  on the bus but the revision register is not what PAL expects. Not an error
  condition; execution works anyway.
- Board's `platform.hdf` (bsps/parallella64): chip E64G401, EMEM base
  0x8e000000 (EZ side). The XML `host_base=0x3e000000` field is never used by
  e-hal (dead field) - the A9-side window only works because the Zynq decoder
  wires 0x3e000000+ to the EZ DRAM port.
- ESDK copy on board: `/home/parallella/esdk` (board's /opt/adapteva can be a
  stale ext4 phantom on these images; verify with `md5sum` after transfers -
  this board has dropped/corrupted files in /tmp before).
