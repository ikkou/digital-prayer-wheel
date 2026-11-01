# Audio storage and hardware candidates — 2026-11-01

## Withdrawn onboard experiment (historical notes below)

The user rejected buzzer BGM on 2026-11-01. The synth, setting and playback path
have been removed; no BGM is active or offered in the current firmware.
Only short startup/confirmation/full-turn cues remain. The following description
records the superseded experiment and must not be read as current controls.
The replacement request is visual progression: see `FEVER.md`.

The withdrawn SOUNDSCAPE / RITUAL mode synthesized a sparse original six-note
phrase on the internal buzzer, with no stored recording and no external parts.
Default OFF. Long hold opens Settings; ring selects SOUNDSCAPE; tap toggles;
long hold returns to the wheel. SOUND / MUTED silences cues and ambience.
Both choices persist in NVS only on a user change.

The current revision uses one M5Unified virtual channel, its immutable sine
table and the Dial's 1-bit buzzer backend. Notes are 1047/1568/1175/1397/1047/1319
Hz, 20-ms attack and 700-ms quadratic decay, with 6.5-second spacing.
The original low-register two-voice trial was physically reported as noisy;
it was rejected and replaced, not treated as a successful sonic result.
The 12-o'clock notification keeps its original pitch
and duration on its own channel; ambience ducks immediately for 180 ms and
recovers over 200 ms. No delay, audio file reads or per-note heap allocation
is added to the application update path. This is a chime-like soundscape;
bass, realistic singing bowls and recorded music fidelity are not promised
from the small buzzer. Physical listening is required before calling it finished.

`include/SoundscapeModel.h` owns the hardware-independent schedule/envelope;
`src/Audio.cpp` adapts it to M5Unified. The 93-check host suite covers enable,
mute/disable, decay, cue ducking/recovery, scheduling stalls, millis rollover
and bidirectional audio-menu navigation, plus the existing rotation/render tests.
The calibrated 64-count ring mapping is now read-only in the exhibition menu;
the migration restores 64 once after an accidental 128-count selection during
the sound trial. SOUND and SOUNDSCAPE are the only selectable settings.

For purchase decisions, start with the concrete cell candidate and polarity
limits in `BATTERY_ADAPTER.md`. The earlier external audio/storage investigation
below is retained for a future fidelity upgrade; it is not a requirement for
the implemented soundscape.

Research/proposal only: no audio decoder, partition change or hardware wiring
has been implemented; the reviewed CLASSIC image pack remains unchanged.

## Capacity

The 8 MiB flash currently reserves 4 MiB for one app, which uses 517,433 bytes.
The current 0x3F0000-byte visual region has 442,094 bytes free after the
3,686,674-byte DPW1 image package. That is a partition budget, not the physical
limit of all spare flash.

Reducing the app reservation to 2 MiB would leave 6,225,920 bytes for data;
after the unchanged images, 2,539,246 bytes remain before audio metadata and
alignment. A practical separate audio partition could reserve about 2.49 MB.
The app must be rebuilt/size-checked after adding audio; current size alone is
not proof that every decoder will fit. No dual-app OTA is enabled currently.
Changing the layout requires relocating/reflashing assets and updating the
hard-coded asset writer offset; it must not be applied to an old package offset.

Examples (computed storage only):
- 30 s, mono, 32 kHz, signed 16-bit PCM: 1,920,000 bytes plus WAV header.
- 60 s, MP3 at 64 kbit/s: about 480,000 bytes plus tags.
- 5 min at 64 kbit/s: about 2,400,000 bytes plus tags.

A short seamless PCM loop is the first candidate: no compressed decoder is
needed and M5Unified already accepts PCM/WAV. Read/queue bounded chunks from
flash without loading the whole file into the no-PSRAM device. MP3 is an option
for longer material but needs a decoder, buffering and concurrent draw/audio
performance measurements. Existing image compression/quality need not change.

## Speaker candidate — conditional; not a plug-in Dial accessory

M5Stack Hat SPK2 / M5StickCPLUS Speaker 2 Hat (U055-B): MAX98357 I2S amplifier
plus 1 W speaker, 24 x 18.6 x 13.7 mm, specified supply 4.5–5.5 V.
https://docs.m5stack.com/en/hat/Hat_SPK2
https://shop.m5stack.com/products/m5stickcplus-speaker-2-hat-max98357
Japan listing (946 JPY shown when checked):
https://www.switch-science.com/products/8864

This is a StickC Hat, not a plug-in Dial accessory. There is no place to insert
it directly into Dial. Two Grove breakouts and a Hat header adapter would be
needed for three I2S signal GPIOs plus the proper power/ground supply.

Further source review found a material documentation inconsistency: the
specification lists 4.5–5.5 V, while the official Hat schematic connects MAX98357
VDD to P1 pin 7, labelled 3V3, and leaves the 5VOUT/5VIN pins unconnected. Do not
use the earlier generic “5 V and ground” description as a wiring instruction.
This candidate is withdrawn as a confirmed purchase/wiring recommendation until
an actual board revision and the appropriate power path have been checked.
https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/580/Sch_Hat_SPK2.pdf

Schematic signal labels (not physical-view orientation): P1 pin 3 G26=BCLK,
pin 4 G36/G25=SDATA, pin 5 G0=LRCLK, pin 1=GND. Those G numbers describe the
StickC header, not Dial's signal assignments. The Dial's PORT.A GPIO13/15
and PORT.B GPIO2/1 could provide three remapped I2S signals, but no wiring
has been assembled or tested. Never connect Dial GPIO26 or GPIO0 just because
a StickC example uses those numbers.

The official Dial v1.1-linked schematic shows a SY7088 boost path to +5VOUT,
which feeds the Grove ports. This is evidence for battery-powered 5 V output,
not a measurement of guaranteed speaker current or ripple at full volume.
https://docs.m5stack.com/en/core/Dial_v1.1
https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/499/Sch_M5Dial.pdf
The reviewed power-page image is in `.tmp/hardware-review/dial_power.png`.

## Battery

No verified plug-in, Dial-specific M5Stack-branded loose battery was found.
The M002 750 mAh Module Battery is intended for the M-BUS Core stack and is not
a direct Dial accessory:
https://docs.m5stack.com/en/module/battery

A conditional, non-M5Stack cell candidate is Data Power DTP502535(PHR), 3.7 V
400 mAh, protected, PH 2-pin connector, 25 x 36 x 5 mm; Sengoku lists 1,210 JPY:
https://www.sengoku.co.jp/mod/sgk_cart/detail.php?code=EEHD-4YZL
The vendor specifies 400 mA maximum charge and 800 mA continuous discharge.
Its PH 2.0 mm plug DOES NOT fit Dial's 1.25 mm 2-pin socket. A correctly keyed
adapter and polarity check are required; final connector series/part number,
mechanical mounting and compatibility with the actual board's charge current
must be settled before treating this as a finalized purchase/wiring list.
The schematic shows TP4057 with a 10 kOhm PROG resistor; a numeric charge-current
claim requires the applicable chip datasheet and actual-board confirmation.
No battery-only runtime or combined speaker current has been measured.

Optional M5Stack external power controller: Unit TimerPWR U189, with charging,
5 V boost and current monitoring, but battery is separate and it adds a unit
and wiring; not required merely because a battery is being added to Dial.
https://docs.m5stack.com/en/unit/Unit_TimerPWR
https://shop.m5stack.com/products/timer-power-unit-with-oled-display-ina3221

## Long-file alternative

Unit AudioPlayer U197 has an N9301 decoder, microSD up to 32 GB, UART control,
and a 3.5 mm output. Dial's PORT.B GPIO1/2 can be assigned UART in firmware;
this is a proposed mapping, not a tested plug-in combination. The unit has no
built-in speaker: an amplified speaker path is still necessary. It can remove
long-file storage/decoding from Dial but adds size and components.
https://docs.m5stack.com/en/unit/Unit_AudioPlayer
https://shop.m5stack.com/products/audio-player-unit-n9301
