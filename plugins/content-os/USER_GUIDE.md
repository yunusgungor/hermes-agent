# Content OS v2.4.0 — Kapsamlı Kullanıcı Kılavuzu

> **AI-Augmented Content Production System**
> Başlangıçtan ileri seviyeye, tüm detaylarıyla Content OS
>
> **Plugin:** `/usr/local/lib/hermes-agent/plugins/content-os/`
> **Kaynak:** Shann³ (@shannholmberg) — 5M impressions / 100K bookmarks

---

## 📋 İçindekiler

1. [Giriş — Content OS Nedir?](#1-giris--content-os-nedir)
2. [Temel Kavramlar](#2-temel-kavramlar)
3. [Kurulum ve Yapılandırma](#3-kurulum-ve-yapilandirma)
4. [Başlangıç Seviyesi](#4-baslangic-seviyesi)
5. [Orta Seviye — Pipeline Derinlemesine](#5-orta-seviye--pipeline-derinlemesine)
6. [İleri Seviye](#6-ileri-seviye)
7. [Tam Referans](#7-tam-referans)
8. [Workflow Playbook](#8-workflow-playbook)
9. [Sorun Giderme](#9-sorun-giderme)
10. [En İyi Uygulamalar](#10-en-iyi-uygulamalar)

---

## 1. Giriş — Content OS Nedir?

Content OS, içerik üretimini **sistematik bir pipeline** haline getiren AI-Augmented üretim sistemidir. Shann³'ün 5M impression / 100K bookmark başarısıyla kanıtlanmış metodolojisinin Hermes Agent plugin implementasyonudur.

### 1.1 Felsefe

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   Content OS bir OTOPİLOT değil, HIZLANDIRICI'dır.              ║
║                                                                  ║
║   ▌ Sistem fikir üretir, taslak hazırlar, kalite kontrol         ║
║   ▌  yapar. Ama YAYINLAMA KARARI her zaman SİZE aittir.        ║
║                                                                  ║
║   ▌ "Never publish without editing" — Shann³                    ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

### 1.2 Ne İşe Yarar?

| Yetenek | Açıklama |
|---------|----------|
| **İçerik Fikri Yönetimi** | Fikirleri yakala, rotala, önceliklendir |
| **LLM Destekli Üretim** | Brief, draft, verification için LLM kullanımı |
| **Kalite Kontrol** | 107 slop pattern (3 tier + bonus) + 12-puan rubric ile otomatik denetim |
| **State Yönetimi** | 14-state lifecycle ile her içeriğin durumunu takip et |
| **Ses Profili** | Kişisel üslubu koru, AI slop'undan kaçın |
| **Cross-Run Learning** | Önceki run'lardan öğren, sistemi güncelle |
| **Signal Processing** | Dış kaynaklardan içerik sinyallerini topla |

### 1.3 Mimaride Neler Var?

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTENT OS PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────┐  │
│  │ SIGNAL   │──▶│ IDEA     │──▶│ WRITER   │──▶│ VERIFIER    │  │
│  │ LAYER    │   │ GATE     │   │ AGENT    │   │ AGENT       │  │
│  │ (X/RSS)  │   │ (4-route)│   │ (brief+  │   │ (rubric+    │  │
│  │          │   │          │   │  draft)  │   │  slop)      │  │
│  └──────────┘   └──────────┘   └──────────┘   └──────┬───────┘  │
│                                                        │        │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐            │        │
│  │ PUBLISH  │◀──│ SCHEDULE │◀──│ APPROVAL │◀───────────┘        │
│  │          │   │          │   │ (human)  │                      │
│  └────┬─────┘   └──────────┘   └──────────┘                      │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                     │
│  │ FEEDBACK │──▶│ LEARNED  │──▶│ ARCHIVE  │                     │
│  │ 24h/72h  │   │          │   │          │                     │
│  └──────────┘   └──────────┘   └──────────┘                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Temel Kavramlar

### 2.1 Run Nedir?

**Run** = Bir içerik objesinin tüm yaşam döngüsünü temsil eden klasör.

Her run şu dosyaları içerebilir:

```
runs/active/{slug}/
├── content-object.md     # ⭐ Run meta bilgisi (ID, state, route, format, pillar)
├── idea.md               # Fikir tanımı + rota kararı
├── context.md            # Bağlam (kanıt, hook'lar, voice)
├── brief.md              # Writer Context Packet (LLM veya manuel)
├── draft-package.md      # Draft (LLM veya manuel)
├── verifier-report.md    # Verifier raporu (LLM)
└── feedback.md           # Yayın sonrası analiz
```

### 2.2 14-State Lifecycle

Her içerik objesi 14 state'ten geçer:

```
                         ┌──────────────────────┐
                         │      captured        │
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                   ┌─────│     idea_review      │◄────┐
                   │     └──────────┬───────────┘     │
                   │                │                 │
                   │     ┌──────────▼───────────┐     │
                   │     │     brief_ready      │     │
                   │     └──────────┬───────────┘     │
                   │                │                 │
                   │     ┌──────────▼───────────┐     │
                   │     │      drafting        │     │
                   │     └──────────┬───────────┘     │
                   │                │                 │
                   │     ┌──────────▼───────────┐     │
                   │     │    verification      │     │
                   │     └──────────┬───────────┘     │
                   │                │                 │
                   │     ┌──────────▼───────────┐     │
                   │     │    draft_review      ├─────┘
                   │     └──────────┬───────────┘
                   │                │
                   │     ┌──────────▼───────────┐
                   │     │      approved        │
                   │     └──────────┬───────────┘
                   │                │
                   │     ┌──────────▼───────────┐
                   │     │   scheduler_ready    │
                   │     └──────────┬───────────┘
                   │                │
                   │     ┌──────────▼───────────┐
                   │     │     scheduled        │
                   │     └──────────┬───────────┘
                   │                │
                   │     ┌──────────▼───────────┐
                   │     │     published        │
                   │     └──────────┬───────────┘
                   │                │
                   │     ┌──────────▼───────────┐
                   │     │   feedback_24h       │
                   │     └──────────┬───────────┘
                   │                │
                   │     ┌──────────▼───────────┐
                   │     │   feedback_72h       │
                   │     └──────────┬───────────┘
                   │                │
                   │     ┌──────────▼───────────┐
                   │     │      learned         │
                   │     └──────────┬───────────┘
                   │                │
                   │     ┌──────────▼───────────┐
                   │     │      archived        │  ← Terminal state
                   │     └──────────────────────┘
```

**Geçerli Transition'lar:**

| Mevcut State | Gidilebilecek State'ler |
|-------------|------------------------|
| captured | idea_review |
| idea_review | **brief_ready**, captured |
| brief_ready | drafting |
| drafting | verification |
| verification | draft_review |
| draft_review | **approved**, brief_ready, captured |
| approved | scheduler_ready |
| scheduler_ready | scheduled |
| scheduled | published |
| published | feedback_24h |
| feedback_24h | feedback_72h |
| feedback_72h | learned |
| learned | archived |
| archived | *(terminal — çıkış yok)* |

### 2.3 4-Route Idea Gate

Her fikir 4 rotadan birine atanır:

```
                    ┌─────────────────────────────┐
                    │        IDEA GATE            │
                    │  "Bu fikir nereden geldi?"  │
                    └─────────────┬───────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
   ┌─────────────┐       ┌──────────────┐       ┌──────────────┐
   │  ORIGINAL   │       │  REPURPOSE   │       │   REWRITE    │
   │             │       │              │       │              │
   │ Kişisel     │       │ Mevcut       │       │ Dış kaynak   │
   │ deneyim/    │       │ içeriği      │       │ ilhamı       │
   │ düşünce     │       │ geliştirme   │       │ (makale,     │
   │             │       │              │       │  podcast)    │
   └─────────────┘       └──────────────┘       └──────────────┘
                                                    │
                                                    ▼
                                          ┌──────────────────┐
                                          │ RESEARCH+IDEATE  │
                                          │                  │
                                          │ Çıktı POST değil │
                                          │ fikir listesidir │
                                          └──────────────────┘
```

| Rota | source_hint | Ne Zaman? | Değer |
|------|------------|-----------|-------|
| **ORIGINAL** | `internal` | "Bunu bizzat yaşadım" | En yüksek — kimse senden iyi yazamaz |
| **REPURPOSE** | `existing` | "Önceki post'umu genişletiyorum" | Yüksek — kanıtlanmış konu |
| **REWRITE** | `external` | "Bir makaleden ilham aldım" | Orta — kaynak atfı gerekli |
| **RESEARCH+IDEATE** | `research` | "Bir konuyu araştırıp fikir üreteceğim" | Düşük — çıktı post değil fikir listesi |

### 2.4 Slop Pattern Sistemi

**Slop = AI'nın ürettiği, yapay hissedilen, değersiz içerik kalıpları.**

Content OS 107 regex pattern ile 4 kategoride slop tespit eder:

| Tier | Adet | Eşik (REVISE) | Eşik (REJECT) | Açıklama |
|------|------|--------------|--------------|----------|
| 🔴 **Tier 1** | 32 | ≥1 pattern | ≥3 pattern | Sıfır tolerans. Promosyon dili, abartı, belirsiz atıf |
| 🟡 **Tier 2** | 32 | ≥3 pattern | ≥5 pattern | Copula avoidance, -ing padding, filler phrases |
| 🟢 **Tier 3** | 33 | ≥8 pattern | ≥15 pattern | Passive voice, cliché metaphors, temporal vagueness |
| ⚪ **Bonus** | 10 | Kontekst bazlı | — | Faux authority, vibes over data, thread-bait, clickbait |

Toplam: **107 pattern** (blog spec: 54+, expansion: 107)

### 2.5 12-Point Bookmarkability Rubric

Her draft 6 kriter üzerinden 0-2 puan alır (toplam 12, geçer not: 8):

```
╔══════════════════════════════════════════════════════════════════╗
║                     BOOKMARKABILITY RUBRIC                       ║
╠══════════════════════════════════════════════════════════════════╣
║  0 = Başarısız    1 = Kısmen    2 = Tam                          ║
╠══════════════════════════════════════════════════════════════════╣
║  ▌ 1. Saves reader a future task      [0/1/2]                    ║
║  ▌ 2. Includes proof                  [0/1/2]                    ║
║  ▌ 3. Reusable takeaway               [0/1/2]                    ║
║  ▌ 4. Specific audience + job         [0/1/2]                    ║
║  ▌ 5. Portable (no-author)            [0/1/2]                    ║
║  ▌ 6. Strong visual                   [0/1/2]                    ║
╠══════════════════════════════════════════════════════════════════╣
║  TOTAL:                    ___/12                                 ║
║  THRESHOLD:                8/12                                   ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 3. Kurulum ve Yapılandırma

### 3.1 Plugin'in Yüklenmesi

Content OS, Hermes Agent'in **built-in plugin**'idir. Elle kurulum gerekmez:

```bash
# Plugin'in yüklü olduğunu doğrula
ls /usr/local/lib/hermes-agent/plugins/content-os/

# Output:
# __init__.py  content_os_core.py  cli.py  plugin.yaml  SKILL.md
# strategy/  voice/  stores/  runs/  modules/  workflows/  references/  scripts/
```

### 3.2 İlk Kurulum

```bash
# 1. Dizin yapısını oluştur
hermes content setup

# Output:
# ✅ Content OS v2.4.0 structure initialized.

# 2. Sistem sağlık kontrolü
hermes content audit

# Output:
# ✅ Content OS v2.4.0 Audit: 0 active, 0 archived. Structure OK.
# ⚠️ Missing strategy file: positioning.md (user must create)
# ⚠️ Missing strategy file: audience.md (user must create)
# ⚠️ Missing strategy file: pillars.md (user must create)
```

### 3.3 Strateji Dosyalarını Doldurma

Üç strateji dosyası **sizin tarafınızdan** doldurulmalıdır:

```bash
# Örnek positioning.md
cat > strategy/positioning.md << 'EOF'
# Positioning

> Tek cümle — bir yabancı post'larımdan sonra bunu tekrarlayabilmeli.

---

"RISC-V tabanlı ASIC tasarımında teoriyi pratiğe dönüştüren mühendis."
EOF

# Örnek audience.md
cat > strategy/audience.md << 'EOF'
# Audience

> Tek kişi. Segment değil.

---

Bir mühendis: RISC-V tasarlıyor, 2-5 yıl deneyimli,
ilk tape-out kararı öncesinde. Timing analizi yapıyor
ama sistematik bir yaklaşım arıyor.
EOF

# Örnek pillars.md
cat > strategy/pillars.md << 'EOF'
# Content Pillars

## Pillar 1: RISC-V Tabanlı ASIC Tasarımı
## Pillar 2: OpenLane/SKY130 ile Tape-Out
## Pillar 3: Edge AI Inference Optimizasyonu
## Pillar 4: Açık Kaynak Donanım Sistem Mühendisliği
EOF
```

### 3.4 Voice Profili Oluşturma

Voice profili = Üslup kurallarınız. Bu dosya **tüm LLM üretimlerinde** referans alınır:

```bash
cat > voice/voice-profile.md << 'VOICEEOF'
# Voice Profile

## Üslup Kurallarım (Her Zaman Uygulanır)

**1. Somut rakam, soyut laf yerine.**
Her cümlede en az bir somut veri.

**2. İlk şahıs ama ego değil.**
"Ben yaptım" diyorum ama "bana bakın" demiyorum.

**3. Teknik terimi açıklamadan kullanma.**
Her terim yanında kısa açıklama.

**4. Paragraf = bir fikir.**
Her paragraf tek bir fikri savunur.

**5. Sonuç cümlesiz bitirme.**
Her paragrafın sonunda bir köprü veya kapanış.

## Yasaklı Kalıplarım (Asla Kullanılmaz)

1. "Groundbreaking / Devrim niteliğinde" — yasak
2. "Aslında / Literally" — yasak
3. "Her mühendis / Herkes" — yasak
4. "Sistem otomatik olarak" — yasak
5. Soru sorup cevabı kendim verme — yasak
VOICEEOF
```

### 3.5 İçerik Depolarını Doldurma

```bash
# Fikirler
cat > stores/ideas/ornek-fikir.md << 'EOF'
# Fikir: SKY130 Tape-Out Checklist
**Kaynak:** Kendi deneyim
**Rota:** ORIGINAL
İlk tape-out'ta timing budget hesaplamadan RTL yazdım.
3 ay geri gittim. Şimdi checklist ile başlıyorum.
EOF

# Hook Pattern'leri
cat > stores/hooks/basarili-hook.md << 'EOF'
# Hook: Somut Rakamla Açılış
Pattern: Rakamlarla başlangıç ("~30sn index, <1sn re-index")
Kaynak: KnowGraph performans benchmark
EOF

# Kanıtlar
cat > stores/proof/ornek-kanit.md << 'EOF'
# Kanıt: KnowGraph Performans
- İlk index: ~30sn (474 entity, 85 edge)
- Cached re-index: <1sn
- 15+ dil desteği
- %100 test coverage
EOF
```

---

## 4. Başlangıç Seviyesi

### 4.1 İlk Run'ınızı Oluşturun

```bash
# En basit haliyle
hermes content new "RISC-V pipeline timing closure için 7 strateji"

# Output:
# ✅ Created run: 2026-05-risc-v-pipeline-timing-closure-icin-7-strateji
# (Route: ORIGINAL)
```

### 4.2 Run'ları Listeleyin

```bash
# Tüm run'ları gör
hermes content runs

# Output:
# ### All Content Runs
# - 2026-05-risc-v-pipeline... — captured — ORIGINAL — active (3 files)
# - 2026-05-knowgraph-projesi... — drafting — ORIGINAL — active (5 files)
```

```bash
# Sadece durum özeti
hermes content status

# Output:
# ### Active Content Runs
# - 2026-05-risc-v-pipeline... — `captured`
# - 2026-05-knowgraph-projesi... — `drafting`
```

### 4.3 State Yönetimi

```bash
# State görüntüle
hermes content state <slug>

# Output:
# ### <slug>
# - **State:** captured
# - **Next actions:**
#   1. Run idea review → decide route
#   2. Write idea.md with route rationale

# State güncelle
hermes content state <slug> --set idea_review

# Output:
# ✅ <slug>: captured → idea_review
```

### 4.4 Idea Gate Kullanımı

```bash
# Rota kararını gör
hermes content route "Bir makaleden ilham aldım" --source external

# Output:
# ### Idea Gate — Route Decision
# - **Route:** REWRITE
# - **Rationale:** Dış kaynaktan ilham alınmış...
# - **Source:** harici

# Rota kararı ile yeni run
hermes content new "Kendi deneyimim" --source internal
```

### 4.5 Slop Taraması

```bash
# Bir run'ın draft'ını tara
hermes content scan <slug>

# Output:
# ### Slop Scan: <slug>
# - **Score:** PASS
# - **Tier 1 (Critical):** 0
# - **Tier 2 (High):** 0
# - **Tier 3 (Medium):** 1
# - **Bonus (Tone):** 0
# - **Findings:** 'very'
```

**Slop Skor Anlamları:**

| Skor | Anlamı | Ne Yapmalı? |
|------|--------|-------------|
| **PASS** | Slop tespit edilmedi | Yayına hazır |
| **REVISE** | Hafif slop var | Belirtilen pattern'leri düzelt |
| **REJECT** | Ciddi slop var | Brief'e dön, yeniden yaz |

### 4.6 Sistem Bakımı

```bash
# Audit
hermes content audit
# ✅ Content OS v2.4.0 Audit: 3 active, 0 archived. Structure OK.

# Setup (dizinleri sıfırla)
hermes content setup
```

---

## 5. Orta Seviye — Pipeline Derinlemesine

### 5.1 Full Pipeline Akışı

İşte bir fikrin **baştan sona** tüm pipeline'dan geçirilmesi:

```bash
# ADIM 1: Fikri yakala
hermes content new "OpenLane DRC hatası debugging framework" \
  --source external

# ADIM 2: Rota kararını ver (Idea Gate)
hermes content state <slug> --set idea_review
# → content-object.md state: idea_review

# ADIM 3: Brief oluştur (Writer Context Packet)
# İki seçenek:
#
# Seçenek A: LLM ile otomatik (tool action)
# hermes content/manager action=generate_brief slug=<slug>
#
# Seçenek B: Manuel yaz
# brief.md dosyasını elle doldur
hermes content brief <slug>
# → Hermes agent'tan brief yazmasını ister

# ADIM 4: State güncelle
hermes content state <slug> --set brief_ready

# ADIM 5: Draft oluştur
hermes content draft <slug>
# → Hermes agent'tan draft yazmasını ister
# → draft-package.md oluşur

# ADIM 6: Verify et
hermes content verify <slug>
# → Verifier Agent çalışır
# → verifier-report.md oluşur

# ADIM 7: Slop kontrolü
hermes content scan <slug>

# ADIM 8: Rubric skoru
hermes content score <slug>
# → 12-puan bookmarkability değerlendirmesi

# ADIM 9: Onayla ve yayına hazırla
hermes content state <slug> --set draft_review
# → İnsan onayı beklenir
hermes content state <slug> --set approved

# ADIM 10: Yayınla
hermes content state <slug> --set scheduler_ready
hermes content state <slug> --set scheduled
hermes content state <slug> --set published

# ADIM 11: Feedback topla
# 24 saat sonra:
hermes content state <slug> --set feedback_24h
# 72 saat sonra:
hermes content state <slug> --set feedback_72h

# ADIM 12: Öğren ve arşivle
hermes content postmortem <slug>
hermes content state <slug> --set learned
hermes content archive <slug>

# Output:
# ✅ Run <slug> archived. Moved to runs/archive/
```

### 5.2 LLM ile Brief Üretimi

`generate_brief()`, Hermes'in gerçek `async_call_llm()` fonksiyonunu kullanarak brief.md üretir.

**Girdi olarak kullanılan dosyalar:**

```
idea.md ──────────────────────────────────┐
context.md (proof + hooks + voice) ───────┤
voice-profile.md ─────────────────────────┤
master-avoid-slop.md ─────────────────────┤
                                          ▼
                                 ┌────────────────┐
                                 │  async_call_llm │
                                 │  task="curator" │
                                 └────────┬───────┘
                                          ▼
                                 ┌────────────────┐
                                 │   brief.md     │
                                 │  (Writer       │
                                 │   Context      │
                                 │   Packet)      │
                                 └────────────────┘
```

**Output — brief.md şablonu:**

```markdown
# Writer Context Packet — {SLUG}
## Meta
- **Route:** ORIGINAL
- **Format:** Thread (8 tweets)
- **Pillar:** Open Source AI / Developer Tools

## Thesis
ONE sentence — what must this post prove?

## Target Reader
ONE specific person. Role + situation + stake.

## Angle (Unexpected Framing)
What makes this different from what everyone else says?

## Proof Elements
- Metrics: concrete numbers
- Stories: real experiences

## Constraints
- Format rules, length, tone, banned phrases

## Voice Anchors
2-3 example sentences that sound like the brand at its best.

## Risks (Slop / Cringe Traps)
What would make this feel AI-written?

## Rubric Targets
- [ ] Saves reader a future task → target: 2
- [ ] Includes proof → target: 2
- [ ] Reusable takeaway → target: 2
- [ ] Specific audience → target: 2
- [ ] Portable (no-author) → target: 2
- [ ] Strong visual → target: 1
Target total: 11/12
```

### 5.3 LLM ile Draft Üretimi

`generate_draft()`, Writer Agent prompt'u ile draft-package.md üretir.

**Writer Agent'ın okuduğu dosyalar (sırayla):**

| # | Dosya | İçerik |
|---|-------|--------|
| 1 | `brief.md` | Writer Context Packet (ne yazılacağı) |
| 2 | `voice-profile.md` | Üslup kuralları (nasıl yazılacağı) |
| 3 | `master-avoid-slop.md` | Yasaklı kalıplar (ne yazılmayacağı) |
| 4 | (opsiyonel) Proof bank | Kanıt deposu |
| 5 | (opsiyonel) Hooks | Başarılı hook pattern'leri |

**Output — draft-package.md yapısı:**

```markdown
---
draft:
[Full content — thread, single post, or article]

rubric_self_assessment:
- Saves reader a future task: 2 — "reason"
- Includes proof: 2 — "specific evidence"
- TOTAL: 11/12

avoid_slop_pass:
- (clean — no slop detected)

open_loops_flagged:
- (none)

voice_check:
- All voice rules followed: yes
- Any banned patterns used: no
---
```

### 5.4 LLM ile Verification

`run_verifier()`, Verifier Agent ile draft'ı denetler:

```
brief.md ───────────────┐
draft-package.md ───────┤
master-avoid-slop.md ───┤
rubric.md ──────────────┤
                         ▼
                ┌────────────────┐
                │  async_call_llm │
                │  task="curator" │
                └────────┬───────┘
                         ▼
                ┌────────────────┐
                │verifier-report │
                │  .md           │
                └────────────────┘
```

**Output — verifier-report.md yapısı:**

```markdown
## brief_check
- Thesis delivered: yes — "specific evidence"

## rubric_scoring
- Saves reader a task: 2 — "specific quote"
- TOTAL: 10/12
- PASSES_THRESHOLD (8/12): yes

## VERDICT
- [APPROVE] — threshold met, slop findings minor

## required_fixes
1. [Line 42]: "phrase" → rewrite suggestion
```

**Verdict Anlamları:**

| Verdict | Anlamı | Sonraki Adım |
|---------|--------|-------------|
| **APPROVE** | Geçer not + minör slop | Onayla, yayına hazırla |
| **REVISE** | Yakın ama düzeltme gerekli | Brief'e dön, belirtilen yerleri düzelt |
| **REJECT** | Rubric eşiği karşılanmamış | Fikri yeniden değerlendir |

### 5.5 Rubric Değerlendirme

`evaluate_rubric()` = LLM ile 12-puan bookmarkability değerlendirmesi:

```json
{
  "scores": {
    "saves_reader_task": 2,
    "includes_proof": 2,
    "reusable_takeaway": 2,
    "specific_audience": 2,
    "portable": 2,
    "strong_visual": 0
  },
  "summary": "Strong thread...",
  "total": 10,
  "passes": true,
  "lowest_scores": ["strong_visual"]
}
```

**Puanlama Kriterleri:**

| Kriter | 0 Puan | 1 Puan | 2 Puan |
|--------|--------|--------|--------|
| **Saves reader a future task** | Sadece bilgi | Kısmen kaydedilebilir | Kesin kaydedilir |
| **Includes proof** | İddia var, kanıt yok | Zayıf kanıt | Spesifik sayı/isim |
| **Reusable takeaway** | Genel tavsiye | Kısmen uygulanabilir | Template/checklist |
| **Specific audience** | Herkese hitap | Bir gruba | Tek kişiye |
| **Portable** | Yazar gerekli | Kısmen bağımsız | Tam bağımsız |
| **Strong visual** | Metin sadece | Zayıf görsel | Grafik/ekran görüntüsü |

### 5.6 Postmortem Analizi

Yayın sonrası LLM ile exact-line analizi:

```bash
hermes content postmortem <slug>
```

Analiz şu sorulara cevap arar:

- **what_worked**: Hangi satırlar/en çok bookmark aldı?
- **what_drove_engagement**: Etkileşimi ne tetikledi?
- **what_missed**: Hangi bölüm beklendiği gibi gitmedi?
- **what_would_i_change**: Ne farklı yapılabilirdi?
- **pattern_to_capture**: Hangi kalıp tekrar kullanılmalı?
- **update_to_voice_rules**: Yeni ses insight'ı var mı?
- **update_to_avoid_slop**: Yeni slop pattern'i keşfedildi mi?

---

## 6. İleri Seviye

### 6.1 Tool Action Kullanımı

Content OS, **2 resmi Hermes tool**'u ile kullanılır:

#### content_os_manager (24 action)

```bash
# Managed action içeren mesaj gönder
hermes content/manager action=new_run idea="Bir içerik fikri" source_hint=internal

# LLM işlemleri (async)
hermes content/manager action=generate_brief slug=xxx
hermes content/manager action=generate_draft slug=xxx
hermes content/manager action=run_verifier slug=xxx
hermes content/manager action=postmortem slug=xxx metrics='{"bookmarks":42}'

# Kalite
hermes content/manager action=scan_slop text="içerik metni"
hermes content/manager action=score slug=xxx

# State yönetimi
hermes content/manager action=get_state slug=xxx
hermes content/manager action=update_state slug=xxx state=approved
hermes content/manager action=get_next_actions slug=xxx

# Sistem
hermes content/manager action=audit
hermes content/manager action=setup
hermes content/manager action=get_all_runs
```

#### content_os_retriever (5 kategori)

```bash
# Strateji dosyalarını al
hermes content/retriever category=strategy

# Voice profilini al
hermes content/retriever category=voice

# Run verilerini al
hermes content/retriever category=run slug=xxx

# Depoları al
hermes content/retriever category=stores

# Öğrenilenleri al
hermes content/retriever category=learnings
```

### 6.2 Voice Evolution

Sistem, her run'un feedback'inden öğrenerek voice profilini geliştirir:

```bash
# Voice profilini güncelle
hermes content/manager action=update_voice voice/updates='
  new_rules:
    - "Her cümle tek bir fikir taşımalı"
  banned_patterns:
    - "ekosistem"
  insights:
    - "Kişisel hikayeler daha çok bookmark alıyor"
'
```

**Voice Evolution Cycle:**

```
Postmortem çıktısı
       │
       ▼
Yeni voice insight'ı keşfedildi
       │
       ▼
voice-profile.md güncellendi
       │
       ▼
master-avoid-slop.md güncellendi
       │
       ▼
Sonraki draft'larda otomatik kullanılır
```

### 6.3 Signal Processing

Signal katmanı, dış kaynaklardan içerik fikirleri toplar:

```bash
# X sinyallerini tara
hermes content signal x
# → inbox.md içinde "X" veya "twitter" geçen entry'leri arar
# → Bulamazsa pillars-based placeholder döner

# RSS sinyallerini tara
hermes content signal rss
# → strategy/source-watchlist.md'deki URL'leri listeler
# → Bulamazsa placeholder döner
```

**Önemli:** Signal processing **gerçek X/RSS API çağrısı yapmaz**. Sadece:
- `inbox.md` içinde X'le ilgili entry'leri regex ile tarar
- `source-watchlist.md`'deki URL'leri listeler

Gerçek API entegrasyonu için harici bir sistem (Postiz, Buffer, vb.) kullanmanız gerekir.

### 6.4 Cross-Run Pattern Analysis

Tüm active + archived run'ları analiz eder:

```bash
hermes content patterns
```

Output:
```
### Run Patterns Analysis
- **Total runs:** 4
- **Avg bookmarks:** 42.5
- **Archived:** 1

**Top formats:**
- Thread (8 tweets): 2
- Single Post: 1
- Article: 1

**State distribution:**
- approved: 1
- learned: 1
- drafting: 1
- idea_review: 1
```

### 6.5 Run'lar Arası Arama

Tüm run'ların tüm .md dosyalarında içerik araması:

```bash
hermes content search "pipeline"

# Output:
# ### Search Results for "pipeline"
# - 2026-05-knowgraph... — draft-package.md — drafting
# - 2026-05-riscv-tim... — idea.md — idea_review
```

### 6.6 Öğrenilenleri Kullanma

Önceki run'lardan çıkarılan dersleri brief üretiminde kullanma:

```bash
hermes content learnings --topic timing
# From knowgraph-feedback: # 24h Feedback — timing analysis...
```

`get_learnings_for_brief()` fonksiyonu şu kaynakları tarar:
1. `stores/feedback/` — Feedback dosyaları
2. `stores/proof/` — Kanıt dosyaları
3. İlk 5 sonucu brief'e context olarak ekler

### 6.7 GBrain MCP Entegrasyonu (İskele)

GBrain (Graph Brain) entegrasyonu, vektör arama ile semantic context sağlar:

```python
# Python içinde etkinleştirme
core = ContentOSCore(Path('.'))
core.enable_gbrain()
# → _get_relevant_proof() artık önce GBrain'i sorgular
# → Fallback: stores/proof/ dizinini tara
```

Şu anki durum:
- `gbrain_enabled = False` (varsayılan)
- `_query_gbrain()` metodu tanımlı ama iskelet halinde
- Gerçek MCP çağrısı Hermes agent seviyesinde yapılır
- Etkinleştirmek için: `content_os_core.py` içinde GBrain MCP tool'unu tespit edip `enable_gbrain()` çağır

### 6.8 Hook Auto-Detection

`post_tool_call` hook'u, dosya yazma işlemlerini otomatik algılar:

```python
# Hermes agent bir dosyaya yazdığında:
# write_file(path="runs/active/xxx/brief.md", content=...)
# → Hook tetiklenir
# → Dosya adına göre state otomatik güncellenir

brief.md           → brief_ready  (otomatik)
draft-package.md   → drafting     (otomatik)
verifier-report.md → verification (otomatik)
published          → published    (otomatik, elle oluşturulan dosya)
```

---

## 7. Tam Referans

### 7.1 CLI Komutları

| Komut | Zorunlu Parametre | Opsiyonel | Ne Yapar? |
|-------|-------------------|-----------|-----------|
| `setup` | — | — | Dizin yapısını oluşturur |
| `status` | — | — | Tüm aktif run'ların state'lerini gösterir |
| `audit` | — | — | Sistem sağlık kontrolü yapar |
| `new` | `idea` (pozisyonel) | `--source`, `--slug` | Yeni run oluşturur + Idea Gate |
| `route` | `idea` (pozisyonel) | `--source` | Idea Gate kararını gösterir (run oluşturmaz) |
| `state` | `slug`? (ops) | `--set` | State gösterir veya günceller |
| `brief` | `slug` | `--llm` | Writer Context Packet başlatır |
| `draft` | `slug` | `--llm` | Draft oluşturmayı başlatır |
| `verify` | `slug` | — | Verifier çalıştırır |
| `scan` | `slug` | — | 107 pattern slop taraması yapar |
| `score` | `slug` | — | 12-puan rubric değerlendirmesi yapar |
| `signal` | — | `source = x\|rss` | Sinyal taraması yapar |
| `postmortem` | `slug` | `--impressions`, `--bookmarks` | Yayın sonrası analiz yapar |
| `runs` | — | `--no-archive` | Tüm run'ları listeler |
| `learnings` | — | `--topic` | Önceki run'lardan öğrenilenleri getirir |
| `patterns` | — | — | Cross-run pattern analizi yapar |
| `search` | `query` | — | Run'larda metin araması yapar |
| `voice-update` | — | — | Ses profilini gösterir |
| `archive` | `slug` | — | Run'ı arşivler |

### 7.2 Slash Commands

| Komut | Ne Yapar? |
|-------|-----------|
| `/content status` | Aktif run'ların state'leri |
| `/content new <idea>` | Yeni run oluştur |
| `/content state [slug]` | State göster |
| `/content route <idea>` | Idea Gate kararı |
| `/content brief <slug>` | Brief talimatı (agent'a inject) |
| `/content draft <slug>` | Draft talimatı (agent'a inject) |
| `/content verify <slug>` | Verify talimatı (agent'a inject) |
| `/content scan <slug>` | Slop tara |
| `/content audit` | Sistem kontrolü |
| `/content signal [x\|rss]` | Sinyal tara |
| `/content archive <slug>` | Run arşivle |
| `/content learnings` | Öğrenilenler |
| `/content patterns` | Pattern analizi |
| `/content runs` | Tüm run'lar |
| `/content context <slug>` | Run context'ini göster |
| `/content voice-update` | Voice profilini göster |

### 7.3 Tool Action Tam Liste

**content_os_manager:**

| Action | Parametreler | Async? | LLM Kullanır? |
|--------|-------------|--------|---------------|
| `setup` | — | Hayır | Hayır |
| `audit` | — | Hayır | Hayır |
| `list` | `include_archived` | Hayır | Hayır |
| `new_run` | `idea`, `slug?`, `source_hint?` | Hayır | Hayır |
| `decide_route` | `idea`, `source_hint?` | Hayır | Hayır |
| `get_state` | `slug` | Hayır | Hayır |
| `update_state` | `slug`, `state` | Hayır | Hayır |
| `sync_state` | `slug` | Hayır | Hayır |
| `get_next_actions` | `slug` | Hayır | Hayır |
| `generate_brief` | `slug`, `extra_context?` | **Evet** | **Evet** |
| `generate_draft` | `slug` | **Evet** | **Evet** |
| `run_verifier` | `slug` | **Evet** | **Evet** |
| `scan_slop` | `text` | Hayır | Hayır |
| `score` | `slug` | **Evet** | **Evet** |
| `signal` | `source` | Hayır | Hayır |
| `postmortem` | `slug`, `metrics?` | **Evet** | **Evet** |
| `update_voice` | `updates` | Hayır | Hayır |
| `get_learnings` | `topic?` | Hayır | Hayır |
| `analyze_patterns` | — | Hayır | Hayır |
| `search_runs` | `query` | Hayır | Hayır |
| `get_all_runs` | `include_archived?` | Hayır | Hayır |
| `archive_run` | `slug` | Hayır | Hayır |

**content_os_retriever:**

| Category | Parametreler | Ne Döner? |
|----------|-------------|-----------|
| `strategy` | — | `positioning.md`, `audience.md`, `pillars.md`, `source-watchlist.md` |
| `voice` | — | `voice-profile.md`, `master-avoid-slop.md` |
| `run` | `slug` | Run klasöründeki tüm .md dosyaları |
| `stores` | — | `inbox`, `workboard`, `ideas/`, `hooks/`, `proof/`, `feedback/` |
| `learnings` | `topic?` | Önceki run'lardan öğrenilen dersler (düz metin) |

### 7.4 Dizin Yapısı (Full)

```
plugins/content-os/                      # Plugin root
│
├── content_os_core.py                   # ⭐ İş mantığı (2097 satır, 42 method)
├── __init__.py                          # Plugin kayıt (422 satır)
├── cli.py                               # CLI komut ağacı (414 satır)
├── plugin.yaml                          # Manifest
├── README.md                            # Kullanıcı dokümanı
├── SKILL.md                             # Skill tanımı (Hermes otomatik yükler)
├── AGENTS.md                            # Geliştirici notları
│
├── strategy/                            # ← SİZ DOLDURURSUNUZ
│   ├── positioning.md                   #   Tek cümle positioning
│   ├── audience.md                      #   Tek kişi hedef kitle
│   ├── pillars.md                       #   3-5 içerik pillar'ı
│   └── source-watchlist.md              #   RSS/X kaynak takip listesi
│
├── voice/                               # Ses profili
│   ├── voice-profile.md                 #   Üslup kuralları + yasaklı kalıplar
│   └── master-avoid-slop.md             #   107 slop pattern (3 tier + bonus)
│
├── stores/                              # İçerik depoları
│   ├── inbox.md                         #   10 aktif fikir
│   ├── workboard.md                     #   Öncelik sırası
│   ├── ideas/                           #   Arşivlenmiş fikirler
│   ├── hooks/                           #   Başarılı hook pattern'leri
│   ├── proof/                           #   Kanıt dosyaları
│   └── feedback/                        #   Run feedback arşivi
│
├── runs/                                # İçerik run'ları
│   ├── active/                          #   Aktif içerik objeleri
│   │   └── {slug}/                      #     Her run = bir klasör
│   │       ├── content-object.md        #       Run meta
│   │       ├── idea.md                  #       Fikir + rota
│   │       ├── context.md               #       Bağlam
│   │       ├── brief.md                 #       Writer Context Packet
│   │       ├── draft-package.md         #       Draft
│   │       ├── verifier-report.md       #       Verifier raporu
│   │       └── feedback.md              #       Yayın sonrası analiz
│   └── archive/                         #   Arşivlenmiş run'lar
│
├── modules/                             # Agent modülleri
│   └── writer/                          #   Writer agent yapılandırması
│       ├── references/                  #     Referans brief/draft'lar
│       └── templates/                   #     Şablonlar
│
├── workflows/                           # 5 playbook
│   ├── idea-to-published-post.md        #   13 aşamalı ana workflow
│   ├── verifier-checklist.md            #   Verifier kontrol listesi
│   ├── scheduler-handoff.md             #   Schedule'a teslimat
│   ├── feedback-loop.md                 #   Feedback döngüsü
│   └── archiveling.md                   #   Arşivleme prosedürü
│
├── references/                          # 6 referans dokümanı
│   ├── audit-technique.md               #   Audit teknikleri
│   ├── production-prompts.md            #   LLM prompt'ları
│   ├── avoid-slop-patterns.md           #   Slop kalıpları detayı
│   ├── rubric-template.md               #   Rubric şablonu
│   ├── thread-brief.md                  #   Thread brief örneği
│   └── skill-audit-checklist.md         #   Audit kontrol listesi
│
└── scripts/                             # Yardımcı script'ler
    ├── stress_test.sh                   #   7 testli stress test (bash)
    └── setup-content-os.sh              #   Etkileşimli kurulum
```

### 7.5 Slop Pattern Kataloğu (107 Pattern)

#### 🔴 Tier 1 — Kritik (32 pattern, sıfır tolerans)

| # | Kategori | Örnek Tetikleyiciler |
|---|----------|---------------------|
| 1 | Promosyon Dili | groundbreaking, game-changing, revolutionary, transformative, paradigm-shifting |
| 2 | Önem Abartısı | pivotal moment, testament to, significant step, quantum leap |
| 3 | Belirsiz Atıf | experts believe, studies show, research suggests, data shows |
| 4 | Sahte Etkinlik | the system compounds, the data tells us, the power of |
| 5 | Retorik Kurulum | the question is whether, at its core, what if i told you |
| 6 | Staccato Parçalama | `no X. no Y. no Z.` pattern |
| 7 | Em Dash Aşırı | `--` (em dash >1-2 adet) |
| 8 | Dolgu Zarfları | actually, literally, quietly, simply, just, basically |

#### 🟡 Tier 2 — Yüksek (32 pattern, ≥3 REVISE / ≥5 REJECT)

| # | Kategori | Örnek Tetikleyiciler |
|---|----------|---------------------|
| 9 | Copula Avoidance | serves as, stands as, features, encompasses, utilizes |
| 10 | -ing Padding | leveraging, implementing, optimizing, enabling |
| 11 | Rule of Three | three things, three reasons, three ways |
| 12 | Filler Phrases | in order to, due to the fact that, in today's world |
| 13 | Generic Conclusions | the future looks bright, exciting times ahead |
| 14 | Signposting | let's dive in, here's what you need to know, TL;DR |
| 15 | Hyperbolic Quantifiers | every single, all the time, never ever |
| 16 | Hedging | it could potentially, it might be argued, arguably |

#### 🟢 Tier 3 — Orta (33 pattern, ≥8 REVISE / ≥15 REJECT)

| # | Kategori | Örnek Tetikleyiciler |
|---|----------|---------------------|
| 17 | Passive Voice | was/were/been + past participle |
| 18 | Elegant Variation | also known as, synonym chains |
| 19 | False Ranges | from basic to advanced, from beginner to expert |
| 20 | Conjunction Overuse | cümleye And/But ile başlama |
| 21 | Unnecessary Intensifiers | very, so, such |
| 22 | Paragraph-Level Vagueness | it is important to note that |
| 23 | Rhetorical Questions | have you ever wondered, can you imagine |
| 24 | Awkward List Intros | there are X things that |
| 25 | False Precision | exactly 93.7% |
| 26 | Clichéd Metaphors | level up, dive deep, game plan, roadmap |
| 27 | Self-Referential Humility | I may be wrong, I could be wrong |
| 28 | Empty Emphasis | UPPERCASE, [BRACKET] emphasis |
| 29 | Temporal Vagueness | recently, lately, these days |
| 30 | False Balance | some say X while others say Y |
| 31 | Unearned Authority | as someone who, having worked in |
| 32 | Hedging Through Specificity | exactly X.X |
| 33 | Template Language | in this post, we'll explore |

#### ⚪ Bonus — Ton (9 pattern, kontekst bazlı)

| # | Kategori | Örnek Tetikleyiciler |
|---|----------|---------------------|
| 35 | Faux Authority | you should, you must, never do this |
| 36 | Vibes Over Data | it feels like, seems to me |
| 37 | Thread-Bait Hooks | here's the thing, the secret |
| 38 | Oversharing Backstory | "X years ago, I..." |
| 40 | Under-Explaining Proof | result: % result |

---

## 8. Workflow Playbook

### 8.1 Hızlı Başlangıç — 5 Dakikada İlk Run

```bash
# 1. Plugin'i kontrol et
hermes content audit

# 2. İlk fikri oluştur
hermes content new "Konum hakkında bir içerik" --source internal

# 3. State'i ilerlet
slug=$(hermes content status | grep "captured" | head -1 | awk '{print $NF}')
hermes content state "$slug" --set idea_review

# 4. Route kararını gör
hermes content route "Konum hakkında bir içerik"

# 5. Brief hazırla
hermes content brief "$slug"

# 6. Draft hazırla
hermes content draft "$slug"

# 7. Slop tara
hermes content scan "$slug"

# 8. Audit yap
hermes content audit
```

### 8.2 Günlük İçerik Rutini

```bash
# Sabah: Sinyalleri tara
hermes content signal x
hermes content signal rss

# Öğle: Yeni fikirleri işle
hermes content new "Bugünün fikri" --source external

# Akşam: Draft'ları verify et
hermes content verify <slug>

# Haftalık: Pattern analizi
hermes content patterns
```

### 8.3 Full Production Pipeline (13 Adım)

```
AŞAMA 1:  captured           → Fikir sisteme girer
AŞAMA 2:  idea_review        → Rota kararı verilir
AŞAMA 3:  brief_ready        → Writer Context Packet yazılır
AŞAMA 4:  drafting           → Writer Agent draft üretir
AŞAMA 5:  verification       → Verifier Agent kontrol eder
AŞAMA 6:  draft_review       → İnsan onayı beklenir
AŞAMA 7:  approved           → Onaylandı
AŞAMA 8:  scheduler_ready    → Yayına hazır
AŞAMA 9:  scheduled          → Planlandı
AŞAMA 10: published          → Yayınlandı
AŞAMA 11: feedback_24h       → 24s metrik kontrolü
AŞAMA 12: feedback_72h       → 72s derin analiz
AŞAMA 13: learned            → Öğrenim çıkarıldı
         → archived           → Arşivlendi
```

### 8.4 Slop Düzeltme Workflow'u

```
Draft'ta slop tespit edildi
       │
       ▼
  ┌────────────────┐
  │ REVISE mi?     │──── Tier 1 ≥1 veya Tier 2 ≥3 veya Tier 3 ≥8
  │ REJECT mi?     │──── Tier 1 ≥3 veya Tier 2 ≥5 veya Tier 3 ≥15
  └────────┬───────┘
           │
    ┌──────┴──────┐
    ▼              ▼
  REVISE         REJECT
    │              │
    │              ▼
    │        Brief'e dön
    │        Fikri yeniden değerlendir
    │
    ▼
  Belirtilen pattern'leri düzelt:
  • "groundbreaking" → somut sonuç
  • "experts believe" → spesifik kaynak
  • "very" → sil veya spesifik ifadeyle değiştir
  • "leverage" → "kullan" ile değiştir
    │
    ▼
  Yeniden verify et
```

---

## 9. Sorun Giderme

### 9.1 State Hataları

| Sorun | Sebep | Çözüm |
|-------|-------|-------|
| `Invalid transition: X → Y` | State lifecycle'da geçersiz geçiş | `sync_state` ile dosyadan oku veya `--force` kullan |
| State cache'te eski state | Cache güncellenmemiş | `.state_cache/runs_state.json` sil, ContentOSCore yeniden başlat |
| `state: unknown` dönüyor | Run bulunamadı veya content-object.md bozuk | Run klasörünü kontrol et, content-object.md var mı? |
| State otomatik güncellenmiyor | `post_tool_call` hook'u tetiklenmemiş | Tool adını kontrol et: `write_file`, `write_to_file`, `create_file` |

### 9.2 LLM Hataları

| Sorun | Sebep | Çözüm |
|-------|-------|-------|
| `Brief generation failed` | LLM çağrısı başarısız | `agent/auxiliary_client` import edilebilir mi? Provider ayarları doğru mu? |
| Draft boş veya yarım döndü | LLM timeout veya token limiti | Prompt'u kısalt, max_tokens'ı artır |
| Verifier hiç slop bulamıyor | Draft gerçekten temiz | LLM'den ziyade regex kontrolü — `scan_slop` ile manuel dene |

### 9.3 Dosya Hataları

| Sorun | Sebep | Çözüm |
|-------|-------|-------|
| `No strategy files found` | `strategy/` dizini boş | `positioning.md`, `audience.md`, `pillars.md` oluştur |
| `stores/ideas/` boş | Hiç fikir kaydedilmemiş | `stores/ideas/` altına .md dosyaları ekle |
| `stores/proof/` boş | Hiç kanıt kaydedilmemiş | `stores/proof/` altına kanıt .md dosyaları ekle |
| `stores/hooks/` boş | Hiç hook kaydedilmemiş | `stores/hooks/` altına hook pattern .md dosyaları ekle |
| `stores/feedback/` boş | Hiç run tamamlanmamış | Normal — run yayınlanıp feedback alınınca dolar |
| Workboard'daki run'lar yok | run/active/ veya archive/ altında mevcut değil | `hermes content runs` ile gerçek run'ları kontrol et, workboard'u güncelle |

### 9.4 Slop Detection Hataları

| Sorun | Sebep | Çözüm |
|-------|-------|-------|
| Temiz metin REVISE döndü | Regex çok agresif | False positive. İnsan kontrolü yap, gerekirse pattern'i güncelle |
| Slop metin PASS döndü | Regex kaçırdı | False negative. master-avoid-slop.md'e yeni pattern ekle |
| `UPPERCASE` pattern'i tetiklenmiyor | Regex `[A-Z]{4,}` 4+ büyük harf arar | Başlıklarda kullanılıyorsa normal, içerikteyse sorun |
| Copula avoidance bulamıyor | `services as -> serves as` gibi typo varsa | Regex birebir eşleşme arar. Typo'ları da kontrol et |

### 9.5 Signal Processing Hataları

| Sorun | Sebep | Çözüm |
|-------|-------|-------|
| Signal "Unknown source" | Geçersiz source parametresi | Sadece `x` veya `rss` kullan |
| Signal her zaman placeholder döner | inbox.md'de "X" geçen entry yok | inbox.md'e elle X kaynaklı fikir ekle |
| RSS signal listesi boş | source-watchlist.md yok | `strategy/source-watchlist.md` oluştur |

### 9.6 Performance Sorunları

| Sorun | Sebep | Çözüm |
|-------|-------|-------|
| 50+ run'da yavaş state okuma | Her `get_state()` dosya okur | State cache otomatik çalışır. `.state_cache/runs_state.json` kontrol et |
| Yavaş search | Tüm .md dosyalarını tarar | Daha spesifik query kullan. İlk 5 sonucu döndürür |
| Yavaş LLM çağrıları | Provider hızına bağlı | Provider değiştir veya timeout'u artır |

---

## 10. En İyi Uygulamalar

### 10.1 İçerik Stratejisi

```
✅ YAPILMASI GEREKENLER:

  1. Brief'i atlama — En kritik aşama
  2. Her run'da en az 1 proof elementi kullan
  3. Voice profilini her ay güncelle
  4. Her postmortem'den en az 1 ders çıkar
  5. ORIGINAL route'a öncelik ver (en yüksek değer)
  6. inbox'ı 10 fikirle sınırla
  7. Yarısı gerçek kaynaktan gelsin (DM, görüşme)

❌ YAPILMAMASI GEREKENLER:

  1. LLM çıktısını düzenlemeden yayınlama
  2. Aynı gün 3+ post yayınlama
  3. Her konuda içerik üretme (pillar'larına sadık kal)
  4. Sadece REWRITE rotası kullanma
  5. Feedback döngüsünü atlama
```

### 10.2 Slop'tan Kaçınma Rehberi

```diff
- KÖTÜ (SLOP):
  "This groundbreaking solution leverages cutting-edge AI to
  revolutionize the way you approach pipeline timing closure.
  Experts believe this transformative approach will change
  everything. Let's dive in!"

+ İYİ (BOOKMARKABLE):
  "I fixed 3 pipeline timing violations last week. Here's exactly
  how: Step 1 — profile the critical path. Step 2 — move the ALU
  to stage 3. Step 3 — re-run synthesis. Result: 40ns → 12ns.
  Try this on your next tapeout."
```

### 10.3 Pipeline Optimizasyonu

| Seviye | Süre | Ne Yapılır? |
|--------|------|-------------|
| **Hızlı** | ~15 dk | new + brief + draft + scan → publish |
| **Standart** | ~1 saat | new + brief + draft + verify + scan + score + review + publish |
| **Full** | ~2 saat | signal + new + brief + draft + verify + scan + score + postmortem + archive |

### 10.4 Voice Evolution Checklist

Her run tamamlandığında:

- [ ] Postmortem çalıştırıldı mı?
- [ ] Yeni voice insight'ı var mı?
- [ ] Yeni slop pattern'i keşfedildi mi?
- [ ] `voice-profile.md` güncellendi mi?
- [ ] `master-avoid-slop.md` güncellendi mi?
- [ ] `stores/hooks/` yeni hook eklendi mi?
- [ ] `stores/proof/` yeni kanıt eklendi mi?

### 10.5 Kalite Gates

```
YAYIN ÖNCESİ KONTROL LİSTESİ:

□ Brief'teki thesis draft'ta teslim edildi mi?
□ Target reader'a hitap ediyor mu?
□ Voice kurallarına uyuldu mu? (0 ihlal)
□ Slop pattern'i kalmadı mı? (PASS)
□ Rubric skoru ≥8/12 mi?
□ En az 1 proof elementi var mı?
□ En az 1 reusable takeaway var mı?
□ İnsan okudu mu? (en önemlisi!)
```

### 10.6 Run İsimlendirme (Slug) Convention

```
Format: {YYYY}-{MM}-{kisa-aciklama}

Örnek:
  2026-05-openlane-drc-fix
  2026-05-knowgraph-projesi-graph-rag-mcp-server
  2026-05-riscv-timing-violation

Kurallar:
  • Küçük harf, tire ile ayrılmış
  • Maksimum 50 karakter (prefix hariç)
  • Tarih prefix'i otomatik eklenir
  • Özel slug başa YYYY-MM- almazsa eklenir
```

---

## Ek: Hızlı Başvuru Kartı

```bash
# ┌─────────────────────────────────────────────────────────────┐
# │                  CONTENT OS — HIZLI REFERANS                │
# ├─────────────────────────────────────────────────────────────┤
# │                                                             │
# │  YENİ RUN:          hermes content new "fikir" --source X   │
# │  STATE GÖSTER:      hermes content state <slug>             │
# │  STATE GÜNCELLE:    hermes content state <slug> --set <s>   │
# │  RUN LİSTELE:       hermes content runs                     │
# │  SLOP TARA:         hermes content scan <slug>              │
# │  AUDIT:             hermes content audit                    │
# │  ROTA KARARI:       hermes content route "fikir" --source X │
# │  ARA:               hermes content search "kelime"          │
# │  PATTERN:           hermes content patterns                 │
# │  ARŞİVLE:           hermes content archive <slug>           │
# │  ÖĞREN:             hermes content learnings --topic X      │
# │  SİNYAL:            hermes content signal [x|rss]           │
# │                                                             │
# │  SLASH:             /content new "fikir"                    │
# │                                                             │
# │  TOOL MANAGER:      hermes content/manager action=<action>  │
# │  TOOL RETRIEVER:    hermes content/retriever category=<cat> │
# │                                                             │
# └─────────────────────────────────────────────────────────────┘
```

---

> **Content OS v2.4.0** — AI-Augmented Content Production System
> Plugin: `/usr/local/lib/hermes-agent/plugins/content-os/`
> Kaynak: Shann³ (@shannholmberg) — [postiz.com/blog/ai-content-system-5m-impressions](https://postiz.com/blog/ai-content-system-5m-impressions)
>
> *"Never publish without editing. The system is an accelerator, not an autopilot."*
