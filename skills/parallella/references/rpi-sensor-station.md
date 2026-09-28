# RPi sensor station (par-ctrl)

RPi 3 Model B v2 at 192.168.8.233, hostname par-ctrl, user `pi` (passwordless
sudo; the "unable to resolve host" warning on sudo is harmless). General-purpose
node of the cluster; hosts a weather/sensor station.

## Access pattern
Non-interactive SSH from this host works:
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null pi@192.168.8.233 '<cmd>'
Pipe scripts in the same call: `cat script.py | ssh ... 'cat > ~/lcd_sf/script.py; python3 ~/lcd_sf/script.py'`.

## Sensor inventory (all on this Pi)
| Sensor | Interface | Address / pin | Notes |
|---|---|---|---|
| 16x2 LCD (I2C) | i2c-1: SDA=GPIO2, SCL=GPIO3 | 0x27 | drivers in ~/lcd_sf/LCD1602.py, lcd_show.py |
| DHT11 temp+humidity | GPIO4 = physical pin 7 (data), VCC->3.3V | - | Adafruit_DHT with platform=Raspberry_Pi_2; test: ~/lcd_sf/dht_test.py |
| BMP180 barometer + temp | i2c-1, address 0x77 | shares bus with LCD | driver: ~/lcd_sf/bmp180_test.py (self-contained smbus) |

Wiring rule for new I2C sensors on this Pi: VCC->3.3V, GND, SDA->GPIO2 (pin 3),
SCL->GPIO3 (pin 5); verify with `sudo i2cdetect -y 1`. LCD occupies 0x27,
BMP180 is 0x77.

## BMP180 driver notes
Driver at ~/lcd_sf/bmp180_test.py: pure smbus, no Adafruit deps. Key facts if
regenerating:
- ID check: register 0xD0 must read 0x55.
- Calibration (16-bit big-endian pairs): ac1@0xAA (u16), ac2@0xAC (s16),
  ac3@0xAE (s16), ac4@0xB0 (u16), ac5@0xB2 (u16), ac6@0xB4 (u16), b1@0xB6
  (s16), b2@0xB8 (s16), mb@0xBA, mc@0xBC, md@0xBE (all s16).
- Raw temp: write 0x2E to reg 0xF4, wait ~5 ms, read u16 at 0xF6.
- Raw pressure (oversampling osr 0..3): write 0x34 | (osr<<6) to 0xF4;
  UP = ((MSB@0xF6 << 16) | (LSB@0xF7 << 8) | (reg 0xF8 & 0x3)) >> (8 - osr).
- Compensation: port of the Adafruit BMP085 C++ integer chain. Pitfalls:
  * Use C-style truncating division for every divide in the chain; Python //
    floors and negative intermediates drift.
  * The final result is already Pascals. Do NOT scale it (e.g. /10): a unit
    error shows up as ~93 hPa instead of ~930, which looks like a dead sensor.
  * Verify any port against Adafruit's debug test vectors before field use:
    UT=27898, UP=23843 with ac6=23153 ac5=32757 mc=-8711 md=2868 b1=6190
    b2=4 ac3=-14383 ac2=-72 ac1=408 ac4=32741, osr=0 must give B5=2400
    (temp 15.0 C).
- Verified field behavior: temp within ~1 C of the adjacent DHT11; pressure
  ~930 hPa at this site.

## Site verification anchors
- Sensor station elevation: 2421 ft (~738 m). Standard-atmosphere expectation:
  p = 101325 * (1 - 2.25577e-5 * h_m)^5.25588, which is ~927 hPa at this
  elevation; expect roughly 925-935 hPa depending on weather.
- Cross-check rule: BMP180 temp and DHT11 temp sit side by side and should
  agree within ~1-2 C (DHT11 is only +/-2-5 C). A disagreement means a bad
  read, not calibration drift.

## Open work
- LCD display integration of the pressure reading is not done yet; the driver
  exposes read_pressure_pa() and read_temperature_c().
