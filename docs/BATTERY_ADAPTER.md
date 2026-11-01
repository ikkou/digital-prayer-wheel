# Battery lead adapter for Dial v1.1

The user subsequently chose to explore USB-C power banks and a printed handle.
See `USB_BATTERY_HANDLE.md` for the current recommendation direction. The cell
and repinning notes below are retained research, not the current shopping list.

Status: a specific local-market cell candidate is now identified, but no cell
has been physically fit/polarity/current/runtime tested on this Dial.
The earlier DTP502535(PHR) recommendation is superseded by the candidate below.
There is still no basis for claiming a tested, unmodified plug-in solution.

## Concrete purchase candidate, researched 2026-11-01

- DATA POWER **DTP502035-PU2**, Marutsu M0379-7654, one cell.
- 3.7 V / 300 mAh, built-in protection, Molex 51021-0200 (PicoBlade 1.25 mm 2-pin).
- Retail listing: 1,153 JPY including tax, excluding delivery; listed in stock
  at research time. Retail dimensions 37 × 20 × 5.6 mm (allow this larger envelope).
- https://www.marutsu.co.jp/pc/i/3797654/
- Manufacturer data sheet:
  https://www.marutsu.co.jp/contents/shop/marutsu/datasheet/datapower_DTP502035-PU2.pdf
- Data sheet maximum charge: 150 mA; continuous discharge: 300 mA.
  Dial's TP4057/R17=10k charge path is approximately 100 mA, and the official
  battery operating-current reference is 100 mA at 4 V. These are paper checks,
  not measured peaks or runtime for our firmware.

**Not a buy-and-plug claim:** rotating the manufacturer's page-9 connector
drawing to match M5Stack's official battery-lead photo puts the red and black
leads in opposite positions. Treat this as requiring polarity correction until
the real cell is checked. The physical housing fit is supported by the matching
PicoBlade-style official photo and the Dial-v1.1 distributor specification, not
by an actual insertion test. Distributor explicitly calls its socket Molex
PicoBlade compatible:
https://www.tinytronics.nl/en/platforms-and-systems/m5stack/m5stamp/m5stamp/m5stack-m5dial-v1.1-esp32-s3-smart-rotary-knob-with-1.28-inch-display-and-touchscreen

For this candidate, a PH-to-1.25 mm adapter is unnecessary if the fit is confirmed;
the remaining cable task is correct polarity. Have an experienced assembler
match battery positive to the board's B+ and negative to ground, checking with a
meter before connection. Do not simply insert it because the housing fits.
Do not cut both live cell wires or solder on the pouch. Do not substitute the
similarly named DTP502035(PHR), which has a different connector.

Internal mounting space and cable routing are unverified. A protected rear
enclosure/mount may be needed. No dedicated M5Stack Dial battery kit with
verified plug, polarity and housing was found. Speaker 2 Hat is not required
for the new onboard soundscape and remains withdrawn as a plug-in recommendation.

Evidence images retained in `.tmp/hardware-review/`: `PU2-drawing.png`,
`battery_interface.png`, `connector_drawing_white.png`, `dial_power.png`.

The battery's nominal 3.7 V is already the intended voltage category. The
adapter changes connector shape and wire routing, not voltage. Keep the cell's
existing protection circuit and cable intact.

## Sources and exact limits

Dial official product page:
https://docs.m5stack.com/en/core/Dial_v1.1
Battery-access photo:
https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/products/core/M5Dial/M5PPT.png
Board-side connector mechanical drawing, linked by the manufacturer:
https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/products/core/M5Dial/1.25WT-2P.pdf

The photo shows the battery socket beneath the removable Stamp controller.
The drawing is for the board-mounted 1.25WT-2P; it does not establish a brand
or part number for a mating cable. Do not substitute arbitrary JST-GH, Molex,
or an unspecified “1.25 mm” part solely by pitch. Match the keying, housing,
latch and metal contact arrangement to the official photo/drawing and real
socket before declaring fit.

## Adapter construction

Use a PH 2.0 mm 2-pin mating lead matching the battery's existing plug and a
pre-crimped two-wire plug that actually mates with the Dial socket. Join those
leads into an adapter while BOTH the battery and Dial are disconnected. Insulate
each joint separately with heat-shrink and provide strain relief. Do not cut or
solder the two live wires directly on the battery merely to change the plug.
A supplier can assemble the two-lead harness instead of hand-crimping tiny pins.

Electrical mapping is battery positive → Dial B+/VBAT_IN and battery negative →
Dial GND/B−. The plug's red/black order is not sufficient evidence; verify it
with a multimeter. With the adapter disconnected from the Dial, connect it to
the cell and check that the intended B+ contact reads a positive cell voltage
relative to the intended ground contact. Avoid bridging the adjacent contacts.
Do not give a left/right pin assignment until the actual connector-view
orientation is known. Unplug the cell again before handling/fitting the adapter.

Remove USB/external power before accessing the socket via the official hardware
procedure. After fitting/insulating the assembly and restoring the controller,
wake from battery with WAKE. Firmware GPIO46 HOLD behavior is already deployed.
Physical charging/current/runtime tests remain outstanding. The separate rear
6–36 V terminal is not the lithium battery socket.
