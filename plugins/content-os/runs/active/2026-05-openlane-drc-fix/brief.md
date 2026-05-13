# Writer Context Packet — 2026-05-openlane-drc-fix
## Meta
- **Route:** REWRITE
- **Format:** Single Post
- **Pillar:** Pillar 2 (OpenLane/SKY130)

## Thesis
OpenLane DRC hataları genelde aynı 5 sebebe dayanır. Doğru debugging framework'ü ile çözüm süresi %80 azalır.

## Target Reader
RTL yazmış ama OpenLane flow'da DRC hatasıyla karşılaşmış bir mühendis. Timing analizi yapabiliyor ama DRC violation nasıl debug edileceğini bilmiyor.

## Angle
Herkes DRC hatası görünce panikler. Oysa 5 temel pattern'den biri — tespit et, düzelt, geç.

## Proof Elements
- 20 OpenLane issue analizi
- Kişisel tape-out tecrübesi (3 DRC hatası, hepsi bu 5 pattern)
- Adım adım debugging flowchart

## Constraints
- Tek post formatı (thread değil)
- 10-15 tweet uzunluğunda
- Her pattern için örnek çıktı

## Voice Anchors
- Doğrudan, teknik
- Adım adım anlatım
- Her adımda neden

## Risks
- Aşırı OpenLane-specific jargon
- Genelleme yapma (her DRC aynı değil)

## Rubric Targets
- [x] Saves reader a future task → 2
- [x] Includes proof → 2
- [x] Reusable takeaway → 2
- [x] Specific audience → 2
- [x] Portable → 2
- [x] Strong visual → 0
Target total: 10/12
