# USB-powered handheld enclosure proposal — 2026-11-01

The user prefers a USB-C stick or small power bank rather than a loose cell
and connector conversion. This supersedes the loose-cell shopping direction
in `BATTERY_ADAPTER.md`; that investigation is retained as background only.
No batteries, cables or printed parts have been purchased or physically tested.

## Concrete candidates, official source checks

| Model | Envelope / mass | Power | Decision limit |
| --- | --- | --- | --- |
| PGA PG-LBJ30A01BK, JAN 4573540888101 | 23 × 102 × 23 mm, 65 g | 3000 mAh; USB-C 5 V / 2.4 A output, USB-A output also available | Best handle proportions. Official page does not document low-current shutdown threshold or always-on mode. Sustained Dial supply remains unverified. |
| Anker Nano A1653 / black A1653011 | approx. 77 × 37 × 25 mm, 102 g (Japan specification) | 5000 mAh; USB-C 5 V / 3 A; foldable C plug and C socket | Official EU feature table confirms trickle mode. Broader/shorter handle; threshold and unlimited always-on operation are not established. Sustained Dial supply remains unverified. |

PGA official product, reference retail 3280 JPY incl. tax:
https://www.pg-a.co.jp/product-all/pg-lbj30a/jan_4573540888101/

Anker Japan official product, displayed 3990 JPY incl. tax at research time:
https://www.ankerjapan.com/products/a1653

Anker official A1653 feature table, Trickle Charging Mode = Y:
https://www.anker.com/eu-en/usb-c-charging-specs

Neither is a verified Dial-specific accessory. Product 5 V output compatibility
does not prove that its automatic cutoff will keep a static scene running.
Dial official reference current is 88.19 mA at USB 5 V; our actual current
and power-bank shutdown behavior must be measured. Do not add an artificial
load or keep-alive resistor simply to mask an unsuitable bank.
https://docs.m5stack.com/en/core/Dial_v1.1

## Assembly direction

- A two-piece printed sleeve/handle holds the intact power bank housing.
- An upper cradle holds the Dial body and leaves the rotating outer ring free.
- Structural forces pass through the cradle and battery housing, never through
  a USB plug, foldable connector or the Stamp module.
- Connect the bank's output to Dial's USB-C with a short cable routed inside
  the printed adapter. Start with an existing cable before specifying a short
  angled connector; bend radius and connector orientation depend on the chosen bank.
- Allow access to the bank's button, LEDs and charging connector; leave room
  to remove it and avoid fully enclosing it in insulating material.
- The grip can extend below a short battery. Dial screen angle, screw engagement,
  print clearances and cable exit require measurement of the selected hardware.
  No fit-ready STL is claimed yet.

## Before committing the enclosure

Run the selected bank directly on the current firmware first: static scene,
normal rotation, soundscape, and the intended session duration. Check for reset
or power cutoff and comfortable combined mass. Record current at USB 5 V if a
meter is available. Then measure the actual bank envelope/port placement and
build the printed cradle around those measurements.
