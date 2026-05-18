# Workboard — İçerik Üretim Sırası

> Bu dosya, yapılacak içerik objelerini öncelik sırasına göre listeler.
> Güncellenir: her yeni içerik eklendiğinde veya öncelik değiştiğinde.

---

## Öncelik Sırası

| # | Slug | State | Pillar | Not |
|---|------|-------|--------|-----|
| 1 | *(günlük tech news)* | captured | **Pillar 6 — Günlük Tech News** | Cron job ile otomatik oluşturulacak |
| 2 | *(haftalık AI savaşları)* | captured | **Pillar 1 — AI Systems Architecture** | Her Pazartesi planlanır |
| 3 | *(haftalık OSS raporu)* | captured | **Pillar 6 — Günlük Tech News** | Her Cuma planlanır |

---

## Yapılacaklar

- [ ] **Günlük cron job kurulumu** — sabah 08:00'de tech news çek + tweet thread hazırla
- [ ] **Haftalık AI özeti** — Pazartesi 09:00 cron
- [ ] **İlk manuel test** — elle bir run başlat, pipeline'ı test et

---

## Açıklama

Artık havuza iki tür içerik giriyor:

**Orijinal içerikler** (Pillar 1-5):
- AI Systems, Multi-Agent, Production Infra, Cognitive Eng, AI-Native Product
- İnsan tarafından başlatılır, uzun format

**Haber içerikleri** (Pillar 6):
- Günlük teknoloji haber tweet thread'leri
- Cron job tarafından otomatik başlatılır
- Bükülük sıralı, kısa format (8-10 tweet)

---

*Son güncelleme: 2026-05-16 — Pillar 6 eklendi, news workflow yapılandırıldı.*
