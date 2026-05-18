# CodeVoyage Concept — Günlük AI Bülteni

> **Marka:** CodeVoyage
> **Hesap:** @codevoygee (Twitter/X)
> **Kanal:** Buffer üzerinden draft → manuel yayın
> **Konsept Tarihi:** 17 Mayıs 2026

---

## 🎯 Core Positioning

**"AI-native sistem mühendisliği yolculuğunda günlük rehber."**

CodeVoyage, @codevoygee Twitter hesabı üzerinden her gün AI & Teknoloji dünyasındaki en önemli gelişmeleri **sistem mühendisi gözüyle** yorumlayan bir günlük bülten serisidir.

---

## 🎨 Görsel ve Format Kimliği

### Thread Yapısı (8 Tweet, Standart)

```
Tweet 1:   📰 CodeVoyage Günlük Bülteni • GGA.AAAA.YYYY
           [🔴KRİTİK] En önemli haber hook + neden şimdi?
Tweet 2-3: Teknik derinlik — mimari fark, benchmark, metrik
           Tradeoff veya sektörel etki analizi
Tweet 4:   [🟠YÜKSEK] İkinci haber
           Ne oldu + neden önemli + teknik yorum
Tweet 5-6: Detay analiz — rakip karşılaştırması
           Mühendis yorumu + tradeoff + somut karşılaştırma
Tweet 7:   🟢 Kısa Haberler (2-3 haber tek tweet'te)
           • Haber 1 — kısa yorum
           • Haber 2 — kısa yorum
           • Haber 3 — kısa yorum
Tweet 8:   📌 Bugünün Büyük Resmi
           Genel trend/öngörü + en az 1 somut öngörü
```

### Emoji Sistemi (Tutarlı)

| Emoji | Anlamı | Kullanım |
|-------|--------|---------|
| 📰 | Bülten başlığı | Her thread'in 1. tweet'i |
| 🔴 | KRİTİK haber | Sektör değiştiren gelişmeler |
| 🟠 | YÜKSEK haber | Önemli gelişmeler |
| 🟢 | ORTA haber / Kısa Haberler bölümü | Dikkate değer gelişmeler |
| 📌 | Kapanış / Bugünün Büyük Resmi | Her thread'in son tweet'i |

### Dil ve Ton

| Özellik | Kural |
|---------|-------|
| **Dil** | Türkçe (teknik terimler İngilizce korunur) |
| **Seviye** | Backend bilen mühendis → AI Systems Architect |
| **Ton** | Objektif, veriye dayalı, yapıcı eleştirel |
| **Yoğunluk** | Her tweet en az 1 somut bilgi + 1 yorum |
| **Hype** | Sıfır tolerans — "devrim", "çığır açan", "game changer" yasak |

---

## 🏗️ Sistem Pipeline'ı

### Zamanlama
- **Her gün:** 08:00 TSİ (05:00 UTC)
- **Platform:** Hermes Agent cron job
- **Yayın:** Buffer draft → manuel kontrol → Twitter

### Akış (6 Adım)

```
Adım 1: Haber Toplama     → 5 kategori × 2 web_search (max 10 çağrı)
Adım 2: Bükülük Skorlama  → 4 seviye (KRİTİK/YÜKSEK/ORTA/DÜŞÜK)
Adım 3: Content-OS Run    → new_run → generate_brief → update_state
Adım 4: Draft Üretimi     → generate_draft (veya manuel write_file fallback)
Adım 5: Kalite Kontrol    → scan_slop → score → verification
Adım 6: Buffer Gönderimi  → buffer_send → özet rapor
```

### Buffer Free Tier Uyumu

| Buffer Free Tier Özellik | CodeVoyage Kullanımı |
|--------------------------|---------------------|
| **1 kanal** | @codevoygee (Twitter) ✅ |
| **Sınırsız draft** | Her gün 8 tweet draft olarak ✅ |
| **Scheduling** | Kullanıcı Buffer UI'dan schedule eder ✅ |
| **Rate limit** | Tolere edilebilir seviyede ✅ |

---

## 📋 Haber Seçim Kriterleri

### Odak Alanları (Öncelik Sırası)

1. **AI/ML Model Duyuruları** — Yeni model, architecture breakthrough, benchmark
2. **AI Infrastructure** — Inference platform, MLOps, serving, orchestration
3. **Açık Kaynak Ekosistemi** — Yeni framework, GitHub trending, community
4. **Girişim & Funding** — >$50M funding, acquisition, exit
5. **Developer Tools** — IDE, framework, library, yeni tool
6. **Chip/Donanım** — AI accelerator, NVIDIA/AMD, yeni chip
7. **Regülasyon & Policy** — AI regulation, safety, governance

### Bükülük Skalası

| Puan | Seviye | Kriter | Tweet Sayısı |
|------|--------|--------|-------------|
| 4 | 🔴 KRİTİK | Yeni model paradigm, sektör değiştiren, >$1B | 6-10 |
| 3 | 🟠 YÜKSEK | Major release, >$100M funding, breakthrough | 4-6 |
| 2 | 🟢 ORTA | Feature update, eng blog, normal funding | 2-3 |
| 1 | ⚪ DÜŞÜK | Minor release, spekülasyon → ATLA | 0 |

### Filtreleme Kuralları

- Her haber **en az 1** kriteri karşılamalı
- DÜŞÜK haberleri **asla** kullanma
- Aynı gün aynı haber tekrarı yapma
- Spekülasyon içeren haberleri DÜŞÜK işaretle ve atla
- Sadece link + başlık paylaşımı yasak — her habere yorum ekle

---

## ✅ Başarı Metrikleri

| Metrik | Hedef |
|--------|-------|
| Impressions/gün | >5K |
| Bookmark/thread | >50 |
| Engagement rate | >%3 |
| Buffer'a gönderim | 8/8 tweet başarılı |

---

## 📚 Referans

- **Cron Job:** "CodeVoyage Günlük AI Bülteni → Buffer" (job_id: 7835da2a86da)
- **Schedule:** Her gün 05:00 UTC (08:00 TSİ)
- **Platform:** Hermes Agent + Content-OS v2.5.0 + Buffer API
- **Content Pillar:** [Pillar 6 — Günlük AI & Tech News](pillars.md)
- **Voice Profile:** [Voice Profile](voice-profile.md)
- **Source Watchlist:** [Source Watchlist](source-watchlist.md)
