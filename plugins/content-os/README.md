# Content OS — AI-Augmented Content Production System

> Hermes Agent Plugin. Structured workflow: signal → idea → brief → draft → verify → publish → feedback.
> **Kaynak:** Shann³ (@shannholmberg) — 5M impressions (2 hafta), 11M views + 100K bookmarks (2 ay).

---

## 🎯 Nedir?

Content OS, AI destekli içerik üretim sistemidir. **Bookmarkable content** üretmek için tasarlanmıştır — okuyucuların gelecekte tekrar ihtiyaç duyacağını düşünerek bookmarkladığı içerik.

**Temel fark:** İçerik = otomasyon değil, sistem hızlandırıcıdır. AI draft üretir, insan onaylar ve she concludes.

---

## 📦 Kurulum

### Gereksinimler
- **Hermes Agent** (v0.27.0+)
- **Content-OS workspace** dizini

### Adım 1: Plugin'i Yükle

```bash
hermes_home = /usr/local/lib/hermes-agent
cp content-os $hermes_home/plugins/content-os
```

### Adım 2: Content-OS Workspace Oluştur

```bash
# Workspace dizinini oluştur
mkdir -p ~/content-os

# Veya kurulum scriptini çalıştır (etkileşimli)
bash scripts/setup-content-os.sh
```

### Adım 3: Hermes'i Yeniden Başlat

```
/reload
```

---

## 🚀 Hızlı Başlangıç

```bash
# 1) Yeni içerik fikri ile başla
hermes content new "RISC-V pipeline tasarımında 7 kritik hata"

# 2) Context otomatik sağlanır - diğer komutları dene
hermes content runs
hermes content learnings
hermes content patterns
```

---

## 📁 Diz yapısı

```
content-os/
├── content_os_core.py          ⭐ Ana mantık (ContentOSCore sınıfı)
├── cli.py                      ⭐ CLI komutları
├── __init__.py                 ⭐ Plugin kayıt
├── plugin.yaml                 ⭐ Plugin manifesti
├── SKILL.md                    ⭐ Skill ana dosyası
│
├── references/                  ⭐ Referans dokümanlar
│   ├── production-prompts.md   — 4 üretim prompt'u (Writer, Verifier, Research, Postmortem)
│   ├── avoid-slop-patterns.md  — 54 AI slop kalıbı, 3 seviye
│   ├── rubric-template.md      — Bookmarkability Rubric doldurulabilir şablon
│   └── skill-audit-checklist.md— Skill sağlamlık kontrol listesi
│
├── workflows/                  ⭐ Playbook'lar
│   ├── idea-to-published-post.md  — 13 aşamalı ana workflow
│   ├── verifier-checklist.md      — Verifier için adım adım kontrol
│   ├── scheduler-handoff.md      — Planlayıcıya teslim prosedürü
│   ├── feedback-loop.md          — 24s/72s feedback mekanizması
│   └── archiveling.md            — Run folder arşivleme
│
├── modules/                    ⭐ Writer agent yapılandırması
├── stores/                    ← Ham malzeme deposu
│   ├── inbox.md               — Ham fikirler
│   ├── ideas/                 — Olgunlaşmış fikirler
│   ├── hooks/                 — Dikkat çekici açılışlar
│   ├── proof/                 — Somut kanıtlar
│   └── feedback/              — Yayın sonrası feedback
│
├── runs/                      ⭐ Her içerik = bir run folder
│   ├── active/                — Aktif run'lar
│   └── archived/             — Arşivlenmiş run'lar
│
├── strategy/                   ← Kullanıcı dolduracak (İNSAN DÜZENLENEN TEK KATMAN)
│   ├── positioning.md         — Pozisyonlama cümlesi
│   ├── audience.md            — Hedef kitle (tek kişi)
│   └── pillars.md             — İçerik pazarı
│
└── voice/                     ← Üslup kuralları + slop kontrolü
    ├── voice-profile.md       — 5 kural + 5 yasak
    └── master-avoid-slop.md   — 54 kalıp özeti
```

---

## 🔄 İçerik Üretim Pipeline'ı

```
Signal Layer (sinyaller)
         │
         ▼
    Idea Gate ──► 4 Rota: ORIGINAL / REPURPOSE / REWRITE / RESEARCH+IDEATE
         │
         ▼
    Run Folder (her içerik için 1)
         │
         ▼
    idea.md → brief.md → draft-package.md
         │                           │
         │                           ▼
         │                    verifier-report.md
         │                           │
         ▼                           ▼
    approved? ◄────────────── İnsan onayı
         │
         ▼
    scheduled → published → feedback_24h → feedback_72h → learned → archived
```

---

## ⚙️ CLI Komutları (hermes content)

### İçerik Üretim
| Komut | Açıklama |
|-------|----------|
| `new [idea]` | Yeni içerik objesi başlat |
| `brief [slug]` | Brief.md oluştur |
| `draft [slug]` | Draft üret (Writer Agent) |
| `verify [slug]` | Rubric + Slop kontrol |
| `post [slug]` | X'e gönder |
| `feedback [slug]` | 24s + 72s feedback |
| `score [draft]` | 12-point rubric ile puanla |
| `scan [slug]` | Draft'ta slop kalıplarını tara |

### Analiz & Öğrenme
| Komut | Açıklama |
|-------|----------|
| `runs` | Tüm run'ları listele (state, status, files) |
| `learnings` | Önceki run'lardan öğrenilenler |
| `patterns` | Tüm run'larda pattern analizi (avg bookmarks, top formats) |
| `search [query]` | Run'larda içerik ara |
| `context [slug]` | Run için context göster (proof, hooks, top runs, voice) |
| `postmortem [slug]` | Yayınlanmış run için postmortem analiz |

### Sistem
| Komut | Açıklama |
|-------|----------|
| `status` | Aktif run'ların state'lerini göster |
| `audit` | Sistem dizin yapısını kontrol et |
| `signal [x\|rss]` | Sinyal taraması yap |
| `voice-update` | Üslup profilini göster (güncel) |
| `setup` | Etkileşimli kurulum |
| `status` | Plugin durumu |

---

## 🧠 Yeni Özellikler (v2.4.0)

### 0. Complete Content OS v2.4.0 Implementation
Full 14-state lifecycle (captured→idea_review→brief_ready→drafting→verification→draft_review→approved→scheduler_ready→scheduled→published→feedback_24h→feedback_72h→learned→archived), 4-route Idea Gate, 54 slop patterns (3 tiers + bonus), and dual Writer/Verifier agent pipeline.

### 1. 14-State Lifecycle
14 aşamalı state machine blog'daki Content OS ile birebir uyumlu:
captured → idea_review → brief_ready → drafting → verification → draft_review → approved → scheduler_ready → scheduled → published → feedback_24h → feedback_72h → learned → archived

### 1. Otomatik Context Retrieve
Yeni run oluşturulduğunda otomatik olarak:
- Previous runs'lardan proof elementleri
- Başarılı hook patternleri
- En iyi performans gösteren run'lar
- Güncel voice profile
birleştirilip context sağlanır.

### 2. Cross-Run Learning
- `learnings` komutu: feedback ve proof store'larından öğrenilenleri getirir
- `patterns` komutu: Tüm run'larda istatistiksel pattern analizi yapar
- Bookmark ortalaması, top formatlar, top pillar'lar

### 3. Active Retrieval
- `context [slug]`: Belirli bir run için context oluşturur
- Proof bank, hooks, top runs, voice profile kombinasyonu
- Her brief/draft öncesi referans olarak kullanılabilir

### 4. Dynamic Voice Evolution
- `voice-update`: Üslup profilini gösterir
- Voice kuralları ve yasaklar otomatik applied
- Referans post'lar ve kanıt türleri dokümante

### 5. Postmortem Automation
- `postmortem [slug]`: Yayınlanmış içerik için metrik analiz
- Bookmark rate hesaplama
- Otomatik feedback kaydetme
- İlerleme önerileri

### 6. Signal Processing
- `signal x`: X'ten signal çekme
- `signal rss`: RSS feed'lerinden signal çekme
- Otomatik fikir extraction

---

## 🔒 Güvenlik & Error Handling

- **UTF-8 Encoding**: Tüm dillerde (Türkçe, Japonca, Çince, Arapça) düzgün çalışır
- **Slug Sanitization**: Özel karakterler otomatik temizlenir
- **Locked Folder Handling**: PermissionError olan folder'lar graceful atlanır
- **Duplicate Slug Detection**: Aynı slug ile tekrar oluşturma engellenir

---

## 🏆 Bookmarkability Rubric

Her içerik 12 puan üzerinden değerlendirilir. **Eşik: 8/12**

| # | Kriter | 0 | 1 | 2 |
|---|--------|---|---|---|
| 1 | Gelecek görev tasarrufu | Sadece bilgi | Kısmen | Bookmarklanabilir |
| 2 | Kanıt | Genel iddia | Zayıf referans | Somut rakam/SS |
| 3 | Tekrar kullanılabilir takeaway | Tek seferlik | Kısmen | Şablon/checklist |
| 4 | Hedef kitle | Genel | Kısmen net | Net + iş tanımı |
| 5 | Taşınabilirlik | Eksik talimat | Boşluklar var | Birebir uygulanabilir |
| 6 | Görsel gücü | Düz metin | Genel resim | Özel diyagram/SS |

---

## 🚫 54 Slop Kalıbı (3 Seviye)

### Tier 1 — Sıfır Tolerans
1. Groundbreaking / game-changing
2. Pivotal / testament to
3. Experts believe / studies show
4. The system compounds / data tells us
5. The question is whether / at its core
6. Staccato (no X. no Y. no Z.)
7. Aşırı em dash (--)
8. Actually / literally / quietly

### Tier 2 — Yüksek (3+ = REVISE, 5+ = REJECT)
9-16: Copula avoidance, -ing padding, filler phrases, signposting...

### Tier 3 — Orta (15+ = REJECT, 18+ = kesin REJECT)
17-54: Passive voice, elegant variation, cliché metaphors...

---

## 🧪 Test Senaryoları

| # | Senaryo | Sonuç |
|---|---------|-------|
| 1 | Tools via Hermes (Manager + Retriever) | ✅ |
| 2 | Retrieve Strategy | ✅ |
| 3 | Very Long Idea (500+ chars) | ✅ |
| 4 | Duplicate Slug | ✅ |
| 5 | State Priority (brief+draft) | ✅ |
| 6 | Hook (post_tool_call) | ✅ |
| 7a | Tier 2 Slop Detection | ✅ |
| 7b | Mixed Tier (T1+T2) | ✅ |
| 7c | Clean Content → PASS | ✅ |
| 8a | Empty Idea Handling | ✅ |
| 8b | Spaces Only | ✅ |
| 9 | Invalid Slug Characters | ✅ |
| 10 | UTF-8 (Japanese/Chinese/Arabic/Emoji) | ✅ |
| 11 | PermissionError Handling (locked folders) | ✅ |

---

## 📚 Kaynak

- **Ana Kaynak:** [Shann³ (@shannholmberg)](https://x.com/shannholmberg) — Content OS
- **Blog Yazısı:** [postiz.com/blog/ai-content-system-5m-impressions](https://postiz.com/blog/ai-content-system-5m-impressions)
- **LunarStrategy:** [@LunarStrategy](https://x.com/LunarStrategy)

---

## 📄 Lisans

MIT License — Ticari ve kişisel projelerde özgürce kullanılabilir.

---

*Bu repo, Shann³'ün Content OS sisteminden ilham alınarak Hermes Agent için uyarlanmıştır.*
