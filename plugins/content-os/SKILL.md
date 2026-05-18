---
name: content-os
description: "AI-Augmented Content Production System: structured workflow from signal → idea → brief → draft → verify → publish → feedback. Based on Shann³'s Content OS — 5M impressions in 2 weeks, 100K bookmarks in 2 months. Full implementation: 4 workflows, 107 slop patterns (3 tiers + bonus), 2-model setup, Hermes-native commands."
version: 2.4.0
category: productivity
author: "Adapted from Shann³ (@shannholmberg) — espressioai / LunarStrategy"
tags: [content, production, social-media, twitter, bookmarkable, AI-writing, content-system, workflow, quality-control, agentic, bookmarkable-content]
triggers:
  - "içerik sistemi kur"
  - "content OS"
  - "AI içerik üretim sistemi"
  - "content production"
  - "içerik moat"
  - "bookmarkable content"
  - "X/Twitter içerik stratejisi"
  - "AI-augmented content workflow"
  - "içerik üret"
  - "thread yaz"
  - "post fikri üret"
  - "içerik pipeline"
  - "content moat oluştur"
  - "impression artış"
  - "bookmark stratejisi"
allowed_toolsets: [web, terminal, file, delegation, xurl, session_search, cronjob]
---

> ⚠️ **MIGRATED to Prodinamik Engine**
> This skill now delegates to the `prodinamik` tool. Use `prodinamik action=...` instead.
> See skill `prodinamik-engine` for full documentation.
> Original plugin code archived at `plugins/archive/`.

### Migration Examples

| Old Command | New Command |
|-------------|-------------|
| `content_os_manager action=new_run` | `prodinamik action=run profile=content` |
| `/content new` | `/run content new` |

---

# Content OS v2 — AI-Augmented Content Production System

> **Hermes Agent Native Implementation.** Full system: 4 workflows, 4 production prompts, 107 slop patterns (3 tiers + bonus), 2-model setup, Hermes-native slash commands, and a 1-2 hour V1 setup.
> **Kaynak:** Shann³ (@shannholmberg) — 5M impressions (2 hafta), 11M views + 100K bookmarks (2 ay).
> **Kullanıcı:** Türkçe yanıt tercih eder. Adım adım açıklama beklentisi yüksek. Kapsamlı/exhaustive kontrol ister.

---

## 👤 Kullanıcı Tercihleri

> Bu bölüm, kullanıcının sabit tercihlerini içerir. Tüm komutlar ve açıklamalar bu tercihlere uygun olmalıdır.

| Tercih | Değer |
|--------|-------|
| **Dil** | Türkçe yanıt tercih edilir |
| **Açıklama düzeyi** | Yüzeysel özet DEĞİL — adım adım, örneklerle zenginleştirilmiş detaylı açıklama |
| **Kontrol beklentisi** | "Tekrar kontrol et" veya "eksiksiz kontrol et" dendiğinde full verification workflow çalıştır; yüzeysel check DEĞİL |
| **Verification standard** | Tüm dosyaları oku, tüm anahtarları karşılaştır, tüm içerik alanlarını araştırma JSON'larıyla karşılaştır; sonuçları tablo ile sun |
| **Skill kullanımı** | Skill mevcutsa YÜKLE — kullanmaya gerek olmadığını düşünme bile |
| **Hata yaklaşımı** | Hatayı düzelt, skill'i güncelle, çözümü kaydet |

---

---

## 📌 Sistemin Özü — Tek Sayfada

```
╔══════════════════════════════════════════════════════════════════╗
║                     CONTENT OS — SİSTEM HARİTASI                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  TEK HEDEF: Bookmarkable Content                                 ║
║  Bookmark = Okuyucunun gelecekte ihtiyaç duyacağını düşünerek   ║
║  verdiği oy — algoritmanın değil OKUYUCUNUN oyu.                ║
║                                                                  ║
║  KRİTİK KURAL:                                                  ║
║  ┌──────────────────────────────────────────────────────────┐    ║
║  │ Asla düzenlemeden yayınlama. Her taslağı elle bitir.    │    ║
║  │ Sistem = Hızlandırıcı, OTOPİLOT DEĞİL.                 │    ║
║  │ Otomasyon olarak kullanılırsa → SİSTEM ÇÜRÜR            │    ║
║  └──────────────────────────────────────────────────────────┘    ║
║                                                                  ║
║  SONUÇ:                                                         ║
║  Sistemi kullanan kişi yazdı (not: AI wrote this)               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

ÇALIŞMA ŞEKLİ:
  Signal Layer + Knowledge Graph
         │
         ▼
  ┌──────────────┐
  │  Idea Gate    │ ──► 4 ROTA: ORIGINAL / REPURPOSE / REWRITE / RESEARCH+IDEATE
  └──────┬───────┘
         │ brief hazırla
         ▼
  ┌──────────────┐
  │  Run Folder   │ ──► 1 FOLDER = 1 İÇERİK OBJESİ
  │  (her post   │     idea.md → brief.md → draft-package.md
  │   için 1)    │     → verifier → review → scheduled → published
  └──────────────┘
         │
         ▼
  ┌──────────────┐
  │  Feedback     │ ──► 24s (immediate) + 72s (pattern) loop
│  │  Loop         │     → Üslup kuralları, hooks/, proof/ güncellenir
  └──────────────┘
```

---

## 🚀 Hermes Native Komutları

Bu skill yüklendiğinde aşağıdaki iş akışları doğrudan kullanılabilir:

### İçerik Üretim Komutları

```
/run content new [idea]        — Yeni içerik objesi başlat (idea verilirse brief ile başla)
/run content brief [post]       — Verilen post/topic için brief.md oluştur
/run content draft [slug]       — brief.md oku, draft-package.md üret
/run content verify [slug]      — Taslağı rubric + slop kontrol et
/run content post [slug]        — Onaylı taslağı X'e gönder (xurl ile)
/run content postmortem [slug] — Yayınlanmış post'un metriklerini analiz et (72s sonra)
/run content feedback [slug]   — Yayın sonrası feedback topla (24s + 72s)
/run content score [draft]     — Bookmarkability rubric puanla (0-12)
/run content audit             — Tüm runs/ klasörünü kontrol et, eksik dosyaları raporla
```

### Sistem Kurulum Komutları

```
/run content setup            — Etkileşimli V1 kurulum sihirbazı (1-2 saat)
/run content scaffold         — Sadece klasör yapısını oluştur (dosyaları doldurmaz)
/run content seeds            — İlk 10 fikri inbox'a koy (demo amaçlı)
/run content extract-brand    — Ham notlardan brand foundation çıkar (prompt tetikleyici)
```

> **Not:** `/run content audit` komutu hem İçerik Üretim hem Sistem Kurulum bölümünde geçerlidir — çalıştırıldığında tüm Content OS yapısını (runs/, stores/, strategy/, voice/) kontrol eder.

### İçerik Stratejisi Komutları

```
/run content signal            — Sinyal katmanını tara, yeni fikirleri inbox'a ekle
/run content ideas             — Tüm fikirleri listele (inbox + ideas/)
/run content hooks             — Hook bank'ı göster/güncelle
/run content proof             — Proof bank'ı göster/güncelle
/run content backlog           — Workboard'daki bekleyen içerikleri göster
/run content archive           — Tamamlanmış run folder'ları listele
/run content metrics           — Tüm yayınlanmış post'ların metriklerini topla
/run content archive-do [slug] — Run folder'ı active'dan archive'a taşı; state=learned zorunlu, runs/archive/ klasörüne kopyalar, active/ klasöründen siler
/run content state [slug]        — content-object.md state'ini oku + güncelle (state machine tablosu otomatik güncellenir)
/run content archive             — Tamamlanmış run folder'ları listele
```

### Kullanım Örnekleri

```
# 1) Sıfırdan içerik sistemi kur
/run content setup

# 2) Yeni fikirle içerik üret (hızlı yol)
Yapay zeka ile kod üretimi hakkında bir thread yaz
→ Hermes: Idea gate'e gir, brief.md oluştur, draft üret, rubric kontrol et

# 3) Mevcut bir fikri geliştir
/run content brief "verilog pipeline optimization"
/run content draft 2026-05-verilog-pipeline

# 4) Yayınlanmış post'unu analiz et
/run content feedback 2026-05-verilog-pipeline
(Metrikleri sor, 24s ve 72s raporlarını iste, learnings çıkar)

# 5) Sistemin tamamını kontrol et
/run content audit
```

---

## 📋 Bookmarkable Format Kontrol Listesi

**Her taslak yayınlanmadan önce şu formatlardan en az birine benzemeli.** Benzemiyorsa → yayınlanmamalı.

| # | Format | Açıklama | Örnek Kullanım |
|---|--------|----------|----------------|
| 1 | **Checklist** | Yapılacaklar listesi | "X yaparken dikkat etmeniz gereken 7 şey" |
| 2 | **Blueprint** | Mimari plan / sistem şeması | "Tamamen düzenlenmiş bir CI/CD pipeline'ı" |
| 3 | **Folder/Directory Structure** | Dosya/dizin yapısı | "İşte benim 10.000 satırlık projemi yönetme şeklim" |
| 4 | **Template** | Doldurulabilir şablon | "İşte her proje için kullandığım brief şablonu" |
| 5 | **Framework** | Kavram çerçevesi | "Karar verirken kullandığım 3-katmanlı çerçeve" |
| 6 | **Step-by-Step Workflow** | Adım adım iş akışı | "Fikirden yayınlanmış post'a 13 adımda" |
| 7 | **Proof Screenshot + Takeaway** | Kanıt (sayı/SS) + çıkarılacak ders | Metrik içeren ekran görüntüsü + analiz |
| 8 | **Before/After** | Önce/sonra karşılaştırması | "Eski yaklaşımım vs. şimdiki yaklaşımım" |
| 9 | **Reusable Mental Model** | Tekrar kullanılabilir düşünce kalıbı | "Üçgen karar modeli" gibi adlandırılmış kalıp |

---

## 🏗️ Sistem Mimarisi — Tam Diyagram

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                         CONTENT OS v2 — TAM MİMARİ                        ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  ┌─────────────────── HARİCİ: SİNYAL KATMANI ──────────────────────┐    ║
║  │                                                                  │    ║
║  │  X bookmarks   RSS feeds   Podcast transkriptları               │    ║
║  │  Rakip postları   DM'ler   Yanıtlar   Makaleler                │    ║
║  │  Keşfedilen kalıplar                                       │    ║
║  │                                                                  │    ║
║  │  Rotalar: ───────────► REWRITE      (dış kaynak → kendi ses)   │    ║
║  │              ───────────► RESEARCH+IDEATE (taram → fikir listesi) │    ║
║  │                                                                  │    ║
║  └────────────────────────────┬──────────────────────────────────────┘    ║
║                               │                                           ║
║  ┌─────────────────── DAHİLİ: BİLGİ ÇİZELGESİ ──────────────────┐    ║
║  │                                                                  │    ║
║  │  Kişisel OS   Notlar   Günlükler   Sesli notlar                │    ║
║  │  Yayınlanmış içerik arşivi   Konuşmalar   Görüşmeler         │    ║
║  │                                                                  │    ║
║  │  Rotalar: ───────────► ORIGINAL     (kendi fikrim → post)      │    ║
║  │              ───────────► REPURPOSE  (mevcut içerik → yeni)   │    ║
║  │                                                                  │    ║
║  └────────────────────────────┬──────────────────────────────────────┘    ║
║                               │                                           ║
║                               ▼                                           ║
║  ┌───────────────────────────────────────────────────────────────┐    ║
║  │              ÜRETİM LİDERİ (Production Leader)               │    ║
║  │                                                                │    ║
║  │   1. Run folder açar (runs/active/{slug}/)                    │    ║
║  │   2. Idea gate kararını kaydeder (idea.md)                   │    ║
║  │   3. Brief yazdırır (brief.md)                               │    ║
║  │   4. Writer agentı çağırır (draft üretir)                    │    ║
║  │   5. Verifier agentı çağırır (rubric + slop)                 │    ║
║  │   6. İnsan onay bekler                                         │    ║
║  │   7. Scheduler'a teslim eder                                  │    ║
║  │   8. Feedback toplar ve öğrenilenleri kaydeder                 │    ║
║  │                                                                │    ║
║  └────────────────────────────┬────────────────────────────────────┘    ║
║                               │                                         ║
║                               ▼                                         ║
║  ┌───────────────────────────────────────────────────────────────┐    ║
║  │         RUN FOLDER — Her içerik objesi için 1 adet           │    ║
║  │                                                                │    ║
║  │  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐    │    ║
║  │  │content-     │  │   brief.md  │  │ draft-package.md  │    │    ║
║  │  │object.md    │──│  (writer    │──│ (taslak +         │    │    ║
║  │  │(ID, state,  │  │  context    │  │  verifier çıktısı)│    │    ║
║  │  │ format)     │  │  packet)    │  │                   │    │    ║
║  │  └─────────────┘  └─────────────┘  └─────────┬─────────┘    │    ║
║  │                                                │              │    ║
║  │  ┌─────────────┐  ┌─────────────┐            │              │    ║
║  │  │ feedback.md  │  │  idea.md    │◄───────────┘              │    ║
║  │  │ (24s + 72s  │  │  (route +  │                           │    ║
║  │  │  learnings)  │  │  rationale)│                           │    ║
║  │  └─────────────┘  └─────────────┘                           │    ║
║  │                                                                │    ║
║  │  Yaşam Döngüsü:                                               │    ║
║  │  captured → idea_review → brief_ready → drafting               │    ║
║  │  → verification → draft_review → approved                     │    ║
║  │  → scheduler_ready → scheduled → published                    │    ║
║  │  → feedback_24h → feedback_72h → LEARNED                     │    ║
║  │  → archived                                                   │    ║
║  │                                                                │    ║
║  └────────────────────────────────────────────────────────────────┘    ║
║                                                                          ║
║  ┌───────────────────────────────────────────────────────────────┐    ║
║  │                    STRATEGY + VOICE + STORES                    │    ║
║  │                                                                │    ║
║  │  strategy/        positioning.md, audience.md, pillars.md,       │    ║
║  │                   source-watchlist.md                          │    ║
║  │                   ⭐ İNSAN TARAFINDAN DÜZENLENEN TEK KATMAN    │    ║
║  │                                                                │    ║
║  │  voice/          voice-profile.md (5 kural + 5 yasak + refs)   │    ║
║  │                  master-avoid-slop.md (107 kalıp, 3 seviye + bonus)      │
║  │                                                                │    ║
║  │  stores/         inbox.md, workboard.md, ideas/, hooks/,       │    ║
║  │                  proof/, feedback/                            │    ║
║  │                                                                │    ║
║  │  modules/        writer/SKILL.md, references/, templates/       │    ║
║  │                                                                │    ║
║  │  workflows/      idea-to-published.md, verifier-checklist.md,    │    ║
║  │                  scheduler-handoff.md, feedback-loop.md         │    ║
║  │                                                                │    ║
║  └────────────────────────────────────────────────────────────────┘    ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## 🚪 Dört Rotalama Kapısı (Idea Gate)

**Her fikir için yazmadan önce kesin bir rota kararı verilir.** Karar, `idea.md`'de belgelenir.

```
FIKIR GİRİŞİ
     │
     ├───► "Bu fikir nereden geldi?"
     │
     ▼
┌────────────────────────────┐
│  DAHİLİ Mİ?               │
│  (kişisel deneyim, not,   │
│   günlük, sesli not,      │
│   görüşme, düşünce)        │
│                            │
│  Yeni fikir mi?            │──► ORIGINAL
│  Mevcut içerik var mı?     │──► REPURPOSE
└────────────────────────────┘
     │
     ├───► "Dışarıdan geldi mi?"
     │    (makale, tweet, transkript,
     │     podcast, rakip içerik)
     │
     │    Bir şeyi çevirmek mi?  │──► REWRITE
     │    Keşif/fikir üretimi mi? │──► RESEARCH+IDEATE
     │
     ▼
```

| Rota | Kaynak | Brief Bağımlılığı | Özellik |
|------|--------|-------------------|---------|
| **ORIGINAL** | Dahili: Kişisel OS, notlar, günlükler, sesli notlar, bir süredir düşündüğün fikirler | positioning + proof bank + pillars | Dış kaynak YOK. Yüksek zevk yatırımı gerekir. En değerli içerik tipi. |
| **REPURPOSE** | Dahili: Mevcut yayınlanmış içerik | Yayınlanmış içerik arşivi | Seri türevleri, makaleden thread, hit post'a self-QRT, blog'dan X post'u |
| **REWRITE** | Harici: Sinyal katmanı (değerli tweet, makale, podcast transkripti, framework) | avoid-slop doc + üslup kuralları | Kendi POV ve üslubunla çevir. Açıkça belirt: ne korunacak, kime atıf verilecek. |
| **RESEARCH+IDEATE** | Keşif + dahili karışımı | Yok (stores/ideas/'a geri besleme) | Konuyu araştır, kalıpları incele. **Çıktı: post DEĞİL, fikir listesi.** |

---

## 📁 Klasör Yapısı — Tam Detay

```
/content-os/                              ← Bu dizin ana Content OS root'udur.
│                                          ← Araç: Notion / Obsidian / Git / Drive
│
├── strategy/                             ⭐ İNSAN TARAFINDAN DÜZENLENEN TEK KATMAN
│   │
│   ├── positioning.md                   ← 3-5 satır. Bir yabancı post'larından
│   │                                      sonra pozisyonlama satırını tekrarlayabilmeli.
│   │                                      Örnek: "ASIC tasarımında pratik ve teoriyi
│   │                                      birleştiren mühendis."
│   │
│   ├── audience.md                       ← 3-5 satır. BİR KİŞİ, segment DEĞİL.
│   │                                      Örnek: "RISC-V + NPU pipeline'ı tasarlayan,
│   │                                      OpenLane deneyimi olan, 2-5 yıllık
│   │                                      mühendis. Karar vermek için zamanı yok."
│   │
│   ├── pillars.md                        ← 3-4 konu. "Fikir sahibi olma hakkını
│   │                                      kazandığım alanlar." Sadece bu konularda
│   │                                      içerik üretilir.
│   │                                      Örnek:
│   │                                      1. RISC-V tabanlı ASIC tasarımı
│   │                                      2. OpenLane / SKY130 ile tape-out
│   │                                      3. Edge AI inference optimizasyonu
│   │                                      4. Tarım/güvenlik için AI destekli cihazlar
│   │
│   └── source-watchlist.md               ← İzlenen kaynaklar (her satırda bir URL veya
│                                          platform:kullanıcı). Haftalık tarama için.
│
├── voice/                                ← Ses ve kalite kontrolü
│   │
│   ├── voice-profile.md                  ← Üslup profili. 5 kural + 5 yasak + 2-3 referans.
│   │                                      Her Writer/Verifier çağrısından önce yüklenir.
│   │
│   └── master-avoid-slop.md              ← 107 AI slop kalıbı, 3 şiddet seviyesi + bonus
│                                          Tam liste: references/avoid-slop-patterns.md
│
├── stores/                               ← Ham malzeme deposu
│   │
│   ├── inbox.md                          ← Ham fikirler. 10 tane tut.
│   │                                      Yarısı gerçek DM/görüşmeden gelmeli.
│   │                                      Yapı: her fikir = ### Fikir [N] + kaynak + tarih
│   │
│   ├── workboard.md                      ← Yapılacak işler. İçerik objesi olarak
│   │                                      öncelik sırası ve durum takibi.
│   │
│   ├── ideas/                            ← Olgunlaşmış fikirler. Inbox'tan buraya taşınır.
│   │                                      Her fikir: {slug}.md → rota, thesis, angle
│   │
│   ├── hooks/                            ← Dikkat çekici açılış koleksiyonu.
│   │                                      Her hook: format: "[hook]" + why_it_works
│   │
│   ├── proof/                            ← Somut kanıtlar. 10 adet minimum.
│   │                                      Her kanıt: {slug}.md → tip, içerik, kullanım
│   │                                      Türleri: metrik, isim, proje, araç, metod
│   │
│   └── feedback/                         ← Yayınlanmış post'ların feedback döngüsü.
│       ├── 24h-template.md               ← 24 saat sonrası için şablon
│       └── 72h-template.md               ← 72 saat sonrası için şablon
│
├── runs/                                 ⭐ HER İÇERİK OBJESİ = BİR RUN FOLDER
│   │
│   ├── active/                          ← Çalışan içerik objeleri
│   │   └── {YYYY-MM-slug}/              ← Örnek: 2026-05-risc-v-pipeline/
│   │       │
│   │       ├── content-object.md         ← İçerik objesi ana dosyası.
│   │       │                            ID, state, format, pillar, created, deadline
│   │       │
│   │       ├── idea.md                   ← Idea gate kararı.
│   │       │                            rota + gerekçe + hangi kaynaktan geldiği
│   │       │
│   │       ├── brief.md                  ← Writer context packet.
│   │       │                            ⭐ EN KRİTİK DOSYA. 400-900 token hedefi.
│   │       │
│   │       ├── draft-package.md          ← Writer agent çıktısı.
│   │       │                            draft + rubric_self_assessment + avoid_slop_pass
│   │       │                            + open_loops_flagged + voice_check
│   │       │
│   │       ├── verifier-report.md        ← Verifier agent çıktısı.
│   │       │                            brief_check + rubric_scoring + avoid_slop_findings
│   │       │                            + VERDICT + required_fixes
│   │       │
│   │       └── feedback.md               ← Yayın sonrası.
│   │                                    24s + 72s learnings + pattern_to_capture
│   │
│   └── archive/                          ← Tamamlanmış içerikler
│       └── {YYYY-MM-slug}/               ← active/'dan taşınır
│           └── (tüm dosyalar korunur)
│
├── modules/                              ← Writer agent yapılandırması
│   └── writer/
│       ├── SKILL.md                      ← Writer agent prompt + kurallar
│       ├── references/                   ← Referans materyaller
│       │   ├── example-briefs/          ← Farklı formatlar için örnek brief'ler
│       │   │   ├── thread-brief.md
│       │   │   ├── single-post-brief.md
│       │   │   ├── article-brief.md
│       │   │   └── carousel-brief.md
│       │   └── best-posts/              ← En iyi performans gösteren post'lar
│       └── templates/                   ← Brief şablonları
│           ├── brief-template.md
│           └── feedback-template.md
│
└── workflows/                            ← Playbook'lar
    ├── idea-to-published-post.md         ← Ana workflow (13 aşama)
    ├── verifier-checklist.md            ← Verifier için adım adım kontrol listesi
    ├── scheduler-handoff.md             ← Planlayıcıya teslim prosedürü
    └── feedback-loop.md                 ← 24s/72s feedback mekanizması
```

---

## 📝 Writer Context Packet (Brief) — Tam Şablon

> **En çok hata yapılan yer.** Çoğu kişi tüm marka dokümanını + 15 KOL profilini + viral sinyalleri her taslak prompt'una boca ediyor. Model güvenli bulanık yazıyor. **400-900 token hedefi tuttur.**

### Brief Şablonu

```markdown
# Writer Context Packet — {POST SLUG}
## Meta
- **Oluşturan:** {insan veya agent}
- **Tarih:** {YYYY-MM-DD}
- **Rota:** {ORIGINAL | REPURPOSE | REWRITE | RESEARCH+IDEATE}
- **Format:** {Single Post | Thread (N tweet) | Article | Carousel | Diğer}
- **Pilar:** {pillars.md'deki konu}

## Thesis
{TEK cümle — bu post neyi kanıtlamalı? Okuyucu ne anlamalı?}

## Target Reader
{TAM olarak kim? Rol + durum + stake. Bir cümle, tek kişi.}
Örnek: "ASIC tape-out deneyimi olmayan ama RISC-V tasarımı
yapan 3 yıllık mühendis. İlk tape-out kararı öncesinde."

## Angle (Beklenmedik Çerçeve)
{Normal beklenenden farklı olan açı. "Herkes X diyor, ama gerçekte Y."}

## Proof Elements (Kullanılabilir)
- Metrikler: {somut sayılar}
- Hikayeler: {gerçek deneyimler}
- Projeler: {isimler, sonuçlar}
- Araçlar: {kullanılan teknolojiler}
⚠️ Sadece kullanmaya yetkili olduğun kanıtları listele

## Constraints
- **Format:** {X format kuralları}
- **Uzunluk:** {karakter/tweet sayısı}
- **Ton:** {resmi / rahat / teknik / samimi}
- **Yasaklı ifadeler:** {explicit olarak listele}
- **Görsel:** {var mı? / yoksa metin açıklaması ver}
- **X/Twitter numaralandırma:** ⚠️ **Draft'ta "T1/8", "1/", "①" gibi prefix KULLANILABİLİR, ama X'te YAYINLARKEN KALDIRILIR.** X thread'inde rakam göstergesi X'in kendi UI'ında görünür — ek prefix gereksiz ve karakter yer.
  - ✅ Yayınlanabilir: "İlk tape-out'ta timing violation ile 3 ay uğraştım."
  - ❌ X'te GEREKSİZ: "T1/8: İlk tape-out'ta timing violation ile 3 ay uğraştım."
  - Draft'ta numaralandırma OK, yayınlarken kaldır.

## Voice Anchors
{Bana (markaya) benzeyen 2-3 örnek cümle.}
Örnek: "OpenLane'de ilk tape-out deneyimim 6 ay sürdü.
İki hafta değil. Bunu baştan bilseydim..."

## Risks (Slop / Cringe Tuzağı)
{Ne bu post'u "AI yazdı" hissi verir? Bunu yazmaktan kaçın.}

## Open Loops
{Modelin bilmediği şeyler. Açıkça belirt, yazar işaretlesin.}
- Bilmiyorum: {konu}
- Tahmin etmem gerekiyor: {alan}

## Rubric Targets
Bu post'u kaç puanla hedefliyorsun?
- [ ] Saves reader a task → hedef: {1/2}
- [ ] Includes proof → hedef: {1/2}
- [ ] Reusable takeaway → hedef: {1/2}
- [ ] Specific audience → hedef: {1/2}
- [ ] Portable (no-author) → hedef: {1/2}
- [ ] Strong visual → hedef: {1/2}
Hedef toplam: ___/12
```

---

## 📊 Bookmarkability Rubric — Detaylı Puanlama Kılavuzu

**Her taslak: 0-1-2 puan × 6 kriter = 12 puan. Eşik: 8/12**

### Puanlama Kriterleri

| # | Kriter | 0 puan — HAYIR | 1 puan — KISMEN | 2 puan — EVET |
|---|--------|----------------|-----------------|---------------|
| 1 | **Gelecek görev tasarrufu** — Bu post, okuyucunun gelecekte yapacağı bir araştırmayı/denemeyi/öğrenmeyi kısaltıyor mu? | Sadece bilgi veriyor, eylem yok | Biraz faydalı ama net değil | Evet — okuyucu bu postu bookmark'layıp gelecekte başvuracak |
| 2 | **Kanıt** — Somut veri var mı? (sayı, SS, isimli örnek, proje sonucu) | Sadece iddialar | Zayıf referans, detaysız | Somut: "X projesinde Y sonucu", "4/10 kişi bunu yaptı" |
| 3 | **Tekrar kullanılabilir takeaway** — Okuyucu bu bilgiyi tekrar kullanabilir mi? | Tek seferlik içgörü | Kısmen, ama açıkça yapılandırılmamış | Evet: şablon, checklist, framework, mental model aktif olarak sunulmuş |
| 4 | **Hedef kitle + iş tanımı** — Kim bu post için yazıldı, ne yapması bekleniyor? | "herkes için", "mühendisler için" gibi genel | Kısmen tanımlanmış ama belirsiz | Net: isimlendirilmiş persona + spesifik iş-tanımı |
| 5 | **Taşınabilirlik (yazarsız uygulanabilirlik)** — Ben olmadan okuyucu bunu uygulayabilir mi? | Talimat eksik, sadece benim deneyimimle anlaşılır | Çoğunlukla uygulanabilir ama boşluklar var | Birebir: adım adım veya şablon, bana ihtiyaç yok |
| 6 | **Görsel gücü** — Etkili bir görsel veya metinsel yapı var mı? | Sadece düz metin, görsel yok | Zayıf/grafik yok, genel resim | Etkili: metrik içeren SS, özel diyagram, önce/sonra karşılaştırması |

### Karar Matrisi

```
┌─────────────────────────────────────────────────────┐
│  TOPLAM SKOR                                        │
├─────────────────────────────────────────────────────┤
│  0-5   → ❌ REDDET — büyük revizyon veya          │
│               farklı yaklaşım gerekli               │
│                                                     │
│  6-7   → ⚠️ REVİZYON — önemli revizyon gerekli   │
│               HANGİ satırların düzeltileceğini      │
│               belirt                                 │
│                                                     │
│  8-9   → ✅ KÜÇÜK DÜZELTME İLE YAYINLA          │
│                                                     │
│  10-12 → ✅ HAZIR — doğrudan planla               │
└─────────────────────────────────────────────────────┘
```

> **Kural:** 8 puan altı → taslağı **ÇÖPE değil, BRIEF'e geri gönder.** Çoğu "kötü" taslak, rubric'in bir satırını atlamış iyi taslaktır. O satırı düzelt → tekrar puanla → yayınla.

### Rubric Puanlama Örneği

```
Post: "RISC-V Pipeline Tasarımında 7 Kritik Hata"

Kriter 1 (Gelecek görev): 2/2
→ "İlk tasarımda bu 7 hatadan kaçınmak = 6 ay tasarruf"

Kriter 2 (Kanıt): 2/2
→ "Hata #3: SKY130'daki timing violation, 4. iterasyonda
  düzeldi. OpenROAD raporu: setup slack = -0.08ns"

Kriter 3 (Takeaway): 2/2
→ "Checklist formatında: [ ] X yapıldı mı? [ ] Y kontrol edildi mi?"

Kriter 4 (Hedef kitle): 1/2
→ "RISC-V mühendisleri" dedim ama pipeline deneyimi
  olan/olmayan ayrımını yapmadım"

Kriter 5 (Taşınabilirlik): 2/2
→ "Bu 7 maddeyi herhangi bir RISC-V tasarımında
  kontrol listesi olarak kullanabilirsiniz"

Kriter 6 (Görsel): 1/2
→ "Timing diagram yok, sadece metin"

TOPLAM: 10/12 ✅ YAYINLA
```

---

## 🚫 Avoid-Slop Dokümanı — Özet

Tam liste: `references/avoid-slop-patterns.md` (107 kalıp, 3 seviye + bonus)

### Tier 1 — Kritik (Sıfır Tolerans, Derhal Düzelt)

| # | Kalıp | Tetikleyici Kelimeler | Örnek |
|---|-------|----------------------|-------|
| 1 | Promosyon dili | groundbreaking, game-changing, revolutionary | → Somut sonuçla değiştir |
| 2 | Önem atfetme abartısı | pivotal moment, testament to | → Spesifik gözlemle değiştir |
| 3 | Belirsiz atıf | experts believe, studies show | → Kaynak belirt veya kaldır |
| 4 | Sahte etkinlik | the system compounds, the data tells us | → Birinci tekil şahıs anlatıma geç |
| 5 | Retorik kurulum | The question is whether... | → Doğrudan iddia ile değiştir |
| 6 | Staccato parçalama | no X. no Y. no Z. | → Paragraf olarak yeniden yaz |
| 7 | Tire aşırı kullanımı | -- her yerde | Hedef: sıfır. Virgül/nokta ile değiştir |
| 8 | Dolgu zarfları | actually, literally, quietly | → Çıkar veya güçlendirici olarak kullan |

### Tier 2 & 3 — Önemli ve Orta

**Tier 2 (Yüksek):** 8 kalıp. 3+ tespit = REVISE, 5+ = REJECT.
(Promosyon değil ama gürültü. "In order to", "-ing padding", signposting gibi.)

**Tier 3 (Orta):** 8+ kalıp. Bağlamda değerlendir. 15+ = REJECT, 18+ = kesin REJECT.
(Passive voice, elegant variation, cliché metaphors gibi.)

Detaylar için: `references/avoid-slop-patterns.md`

**Hızlı audit komutları:**
```
SEARCH: groundbreaking | game-changing | revolutionary
SEARCH: pivotal | testament | significant step
SEARCH: experts believe | studies show
SEARCH: the question is whether | at its core
SEARCH: actually | literally | quietly
SEARCH: -- (em dash sayısı → hedef: 0-1)
```

---

## 🤖 Üretim Prompts'ları — Özet

Tam prompt metinleri: `references/production-prompts.md`

### 4 Üretim Prompt'u Özeti

| # | Prompt | Amaç | Çıktı |
|---|--------|------|-------|
| 1 | **Research Agent** | Sinyal katmanını tarar | `stores/inbox`'a structured signal entries |
| 2 | **Writer Agent** | brief.md + üslup kuralları → taslak | `draft-package.md` (taslak + self-assessment + slop check + open loops) |
| 3 | **Verifier Agent** | Taslağı rubric + slop karşılar | `verifier-report.md` (satır bazlı bulgular + VERDICT) |
| 4 | **Postmortem Prompt ⭐** | Yayınlanmış post'ı analiz eder | Tam satırları işaret ederek neyin çalıştığını bulur |

### Postmortem Prompt — Önemi

Bu en yüksek getirili prompt'tur. **Her yayınlanmış post'tan sonra çalıştırılmalı.**

Kurallar:
- ❌ "Güçlü hook" → KABUL EDİLMEZ
- ❌ "Harika içgörü" → KABUL EDİLMEZ
- ❌ "İyi format" → KABUL EDİLMEZ
- ✅ "Şu cümle: '...' — bookmark sayısının %40'ını tek başına oluşturdu"
- ✅ "Şu kalıp: 'X yaparken Y yapmayı unutmayın' — okuyucular bunu doğrudan uyguladı"

---

## 🏎️ İki Model Kurulumu — Detaylı

### Mimari Seçenekleri

```
SEÇENEK A: İKİ MODEL (Yüksek Hacim — Önerilen)
═══════════════════════════════════════════════════════
┌──────────────────────────────────────────────────┐
│            Orchestrator Model                     │
│  • Rotalama kararları                            │
│  • Workflow kontrolü                              │
│  • Verifier koordinasyonu                         │
│  • Scheduler handoff                               │
│                                                   │
│  [Her çağrıda: brief.md + voice rules YOK]       │
└────────────────────┬─────────────────────────────┘
                     │ "Bu fikir için brief hazırla"
                     │ "Taslağı doğrula"
                     ▼
┌──────────────────────────────────────────────────┐
│              Writer Model                         │
│  • Zevk, ritim, sıkıştırma                       │
│  • Ses kalitesi                                  │
│  • Gerçek taslak üretimi                         │
│                                                   │
│  [Her çağrıda: brief.md + voice-profile.md        │
│   + master-avoid-slop.md YÜKLÜ]                  │
└──────────────────────────────────────────────────┘

SEÇENEK B: TEK MODEL + SKILL GRAFİĞİ (Düşük Hacim)
═══════════════════════════════════════════════════════
Aynı model tüm 4 prompt'u sırayla çalıştırır.
Context window disiplini daha kritik.
Content OS SKILL.md procedürel bellek sağlar.
```

### Model Önerileri

| Model | Kullanım Alanı | Açıklama |
|-------|---------------|---------|
| **Claude Opus 4 / Sonnet 4** | Writer | En iyi ses kalitesi, zevk, ritim |
| **GPT-5.5 / o4** | Writer + Orchestrator | Hızlı, tutarlı, iyi context management |
| **Gemini 2.5** | Orchestrator | Mantıksal kararlar, workflow kontrolü |
| **DeepSeek R1** | Research + Ideate | Keşif ve fikir üretimi |

---

## 📦 Hermes Entegrasyonu — Cronjob + Delegation

### Otomatik Signal Taraması (Cronjob)

```yaml
# Her gün sabah 08:00'de sinyal taraması
name: content-os-signal-scan
schedule: "0 8 * * *"
prompt: |
  Content OS signal scan çalıştır.
  1. X bookmarks'ları kontrol et (son 24s)
  2. RSS feeds'leri tara
  3. Yeni signal entry'leri /content-os/stores/inbox.md'ye ekle
  4. inbox.md'deki fikirleri değerlendir (en az 3 yeni fikir ekle)
  5. Toplam fikir sayısı 10'u geçtiyse en eski 2'yi archive'a taşı
skills: [content-os]
deliver: local
```

### Weekly Content Review (Cronjob)

```yaml
# Her Pazar 20:00'de haftalık metrik özeti
name: content-os-weekly-review
schedule: "0 20 * * 0"
prompt: |
  Content OS haftalık metrikleri topla.
  1. runs/active/ ve runs/archive/'daki tüm feedback.md'leri oku
  2. Toplam bookmark/impression oranını hesapla
  3. En iyi 3 post'u belirle (bookmark oranına göre)
  4. En düşük 2 post'u analiz et (ne eksikti?)
  5. Sonuçları stores/feedback/weekly-review-{YYYY-MM-DD}.md'ye yaz
  6. voice-profile.md'yi güncelle (varsa new learnings)
skills: [content-os]
deliver: local
```

### Delegation Pattern — Parallel Content Production

```python
# Aynı anda 3 farklı içerik objesi üret
delegate_task(
    tasks=[
        {
            "goal": "ORIGINAL route ile RISC-V pipeline thread üret",
            "context": "Slug: 2026-05-riscv-pipeline | Rota: ORIGINAL | Format: Thread (8 tweet) | Pilar: ASIC design | Proof: SKY130 timing data, OpenROAD raporu",
            "toolsets": ["file", "web"]
        },
        {
            "goal": "REPURPOSE route ile önceki blog post'tan X thread üret",
            "context": "Slug: 2026-05-blog-to-thread | Kaynak: ~/blog/risc-v-tapeout-guide.md | Format: Thread (6 tweet) | Yeni angle: ilk kez tape-out yapanlar için pratik checklist",
            "toolsets": ["file"]
        },
        {
            "goal": "RESEARCH+IDEATE route ile edge AI inference optimizasyonu araştır",
            "context": "Slug: 2026-05-edge-ai-research | Konu: RISC-V + NPU inference optimization | Çıktı: 5 fikir listesi → ideas/ klasörüne",
            "toolsets": ["web", "file"]
        }
    ],
    role="orchestrator"
)
```

---

## 🔧 V1 Kurulum — Adım Adım (1-2 Saat)

### Adım 1: Klasör İskeleti Kur (5 dakika)

```bash
mkdir -p /content-os/{strategy,voice,stores/{ideas,hooks,proof,feedback},runs/{active,archive},modules/writer/{references/example-briefs,references/best-posts,templates},workflows}
```

### Adım 2: Strategy Katmanını Doldur (30 dakika)

**`strategy/positioning.md`** — 3-5 satır, tekrar edilebilir cümle:
> "Ben [ne yaparım] için [kimin için] yapan [kim]. [Farkım ne]."

**`strategy/audience.md`** — 3-5 satır, TEK KİŞİ:
> "Bir [rol] düşün. [durum]. [stake]. [yapması gereken karar]. [engeli ne]."

**`strategy/pillars.md`** — 3-4 konu:
> "Fikir sahibi olma hakkını kazandığım alanlar. Sadece bunlarda içerik üretilir."

**`strategy/source-watchlist.md`** — İzlenen kaynaklar

### Adım 3: Voice Profile Yaz (30 dakika)

**`voice/voice-profile.md`** şablonu:
```
ÜSLUP KURALLARIM (her zaman uyulur):
1. [Kural 1]
2. [Kural 2]
3. [Kural 3]
4. [Kural 4]
5. [Kural 5]

YASAKLI KALIPLARI (asla kullanılmaz):
1. [Yasak 1]
2. [Yasak 2]
3. [Yasak 3]
4. [Yasak 4]
5. [Yasak 5]

REFERANS POST'LARIM (en iyi dönemimden):
1. [URL veya metin + neden iyi]
2. [URL veya metin + neden iyi]
3. [URL veya metin + neden iyi]
```

**`voice/master-avoid-slop.md`** — references/avoid-slop-patterns.md'deki Tier 1'deki 8 kalıpla başla. Sonra her postmortem'den sonra güncelle.

### Adım 4: Proof Bank Oluştur (15 dakika)

`stores/proof/` içine 10 somut kanıt. Her biri:
- **Metrik:** "X yaptığımda Y sonucu aldım"
- **İsim:** "X kişi bu yaklaşımı kullandı, sonuç: Y"
- **Proje:** "X projesinde Y aracını kullandım, avantajı: Z"
- **Araç:** "X aracı tam olarak Y işi yapıyor, alternatif: Z"
- **Metod:** "X metodu Y problemi çözüyor, neden: Z"

### Adım 5: Inbox'a 10 Fikir Koy (10 dakika)

> ⚠️ Yarısı gerçek olmalı — bu ayki DM'lerden, görüşmelerden, düşüncelerden gelmiş. Sadece oturup uydurma.

### Adım 6: İlk Run Folder'ı Aç +闭环 (15 dakika)

1. `runs/active/2026-05-demo/` oluştur
2. `content-object.md` → ID, state, format, pillar
3. `idea.md` → rota + gerekçe
4. `brief.md` → yukarıdaki şablona göre doldur
5. **Writer'a ver** → `draft-package.md` al
6. **Verifier'a ver** → `verifier-report.md` al
7. **İnsan onay** → geçerse planla, geçmezse düzeltme talimatı ver
8. Yayınla → `feedback.md` yaz → arşivle

---

## ⚠️ Kritik Tuzaklar (Pitfalls)

| # | Tuzak | Neden | Çözüm |
|---|-------|-------|-------|
| 1 | **Otomasyon = Çürüme** | AI autopilota bırakılırsa ses kaybolur | Her taslak elle bitirilir. AI draft üretir, insan onaylar. |
| 2 | **Devasa context dump** | Tüm marka dokümanı brief'e konur | 400-900 token, post-spesifik paket. Büyük context = bulanık çıktı. |
| 3 | **8/12 altını çöpe atmak** | "Kötü taslak" algısı | Çöpe değil brief'e geri gönder. Atlanan satırı düzelt. |
| 4 | **Proof bank'ı boş bırakmak** | İçerik somut kanıttan yoksun | Her ay en az 3 yeni kanıt ekle. Proof = moat'un. |
| 5 | **Bookmark yerine beğeni hedeflemek** | Yanlış metrik = yanlış optimizasyon | Bookmark = okuyucunun oyu. Beğeni/retweet algoritmik. |
| 6 | **Tüm rotaları eşit kullanmak** | ORIGINAL en değerli içerik | ORIGINAL ağırlıklı üretim yap. REPURPOSE kazan-kazan. |
| 7 | **Feedback loop'u atlamak** | Sistem kendini iyileştiremez | Her yayınlanmış post → 24s + 72s analiz → learnings çıkarılır. |
| 8 | **Aynı açıları tekrar kullanmak** | Ses kalıplaşır, okuyucu sıkılır | Her brief'te "angle" zorunlu. Beklenmedik çerçeve şart. |

---

## 📊 Referans Dosyaları

Tam içerikler için `skill_view(name='content-os', file_path='...')` kullan:

| Dosya | İçerik |
|-------|--------|
| `references/production-prompts.md` | 4 üretim prompt'u (Research, Writer, Verifier, Postmortem) + Brand Foundation Extraction + Voice Profile |
| `references/audit-technique.md` | **Audit/dogrulama teknigi:** terminal vs execute_code — neden terminal daha guvenilir, dogru/yanlis pattern'ler |
| `references/avoid-slop-patterns.md` | 107 kalip, 3 Siddet seviyesi + bonus, her biri icin concrete rewrite ornekleri |
| `references/rubric-template.md` | Doldurulabilir Bookmarkability Rubric şablonu |
| `references/skill-audit-checklist.md` | **Skill eksiksizlik kontrolü** — 5 katmanlı systematic audit metodolojisi (✅ her "eksiksiz kontrol" isteğinde uygula) |
| `scripts/setup-content-os.sh` | Otomatik V1 kurulum scripti |
| `workflows/idea-to-published-post.md` | 13 aşamalı ana playbook |
| `workflows/verifier-checklist.md` | Verifier için adım adım kontrol listesi |
| `workflows/scheduler-handoff.md` | Planlayıcıya teslim prosedürü |
| `workflows/feedback-loop.md` | 24s/72s feedback mekanizması |
| `workflows/archiveling.md` | Run folder'ı active'dan archive'a taşıma prosedürü, /run content archive-do komutu |

---

## 🔗 Kaynaklar ve Attributions

- **Ana Kaynak:** Shann³ (@shannholmberg), [Content OS](https://postiz.com/blog/ai-content-system-5m-impressions)
- **LunarStrategy:** @LunarStrategy — Content OS ajans deploy'u
- **Kullanıcı Tercihleri:**
  - Türkçe yanıt tercih edilir
  - Adım adım açıklama beklentisi yüksek
  - Kapsamlı/exhaustive kontrol ister
