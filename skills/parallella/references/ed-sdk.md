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
