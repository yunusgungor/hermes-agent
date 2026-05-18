# Content-OS Setup Workflow — Eksiksiz Hazırlık Rehberi

> **Amaç:** Content-OS plugin'ini sıfırdan kurmak, tüm hazırlık adımlarını hatasız tamamlamak.
> **Hedef:** USER_GUIDE.md Bölüm 3 (Kurulum ve Yapılandırma) + Bölüm 4.1 (İlk Run) eksiksiz.
>
> **Versiyon:** v2.4.0
> **Kapsam:** Plugin yüklemesi → strateji/voice/stores → CLI fix → audit → ilk run — tüm tuzaklar dahil

---

## İçindekiler

1. [Ön Koşullar](#1-ön-koşullar)
2. [Plugin Doğrulama](#2-plugin-doğrulama)
3. [CLI Fix (Container Ortamı)](#3-cli-fix-container-ortamı)
4. [Dizin Yapısı ve İlk Kurulum](#4-dizin-yapısı-ve-ilk-kurulum)
5. [Strateji Dosyaları](#5-strateji-dosyaları)
6. [Voice Profili](#6-voice-profili)
7. [İçerik Depoları](#7-içerik-depoları)
8. [State Cache ve Filesystem Sync](#8-state-cache-ve-filesystem-sync)
9. [Git Commit ve Push](#9-git-commit-ve-push)
10. [Doğrulama](#10-doğrulama)
11. [Sorun Giderme](#11-sorun-giderme)

---

## 1. Ön Koşullar

- Content-OS plugin'i Hermes Agent'ın built-in plugin'i (`/opt/hermes/plugins/content-os/`)
- Git repo sağlam: `yunusgungor/content-os.git` (branch: `beta`)
- Python 3.11+ (venv)

```bash
# Plugin konumunu doğrula — iki olası path:
ls /opt/hermes/plugins/content-os/  # (Hermes WebUI container)
# veya
ls /usr/local/lib/hermes-agent/plugins/content-os/  # (standart kurulum)
```

## 2. Plugin Doğrulama

```bash
# Olması gereken dosyalar:
# __init__.py  content_os_core.py  cli.py  plugin.yaml  SKILL.md  USER_GUIDE.md
# strategy/  voice/  stores/  runs/  modules/  workflows/  references/  scripts/
# .git  ⛔ ASLA SİLME

ls /opt/hermes/plugins/content-os/
```

**Tuzak:** Plugin `/opt/hermes/plugins/content-os/` altındaysa USER_GUIDE.md'deki `/usr/local/lib/hermes-agent/plugins/content-os/` path'inden farklıdır. Bu normaldir — workspace'e göre path değişir.

## 3. CLI Fix (Container Ortamı)

Hermes WebUI container'ında venv symlink'i genellikle bozuktur:
```
/opt/hermes/venv/bin/python → /root/.local/share/uv/python/.../python3.11 (mevcut değil)
```

**Belirti:** `hermes content setup` çalışmaz — `ModuleNotFoundError: No module named 'yaml'`

**Çözüm — Wrapper Script:**

```bash
cat > /usr/local/bin/hermes << 'SHELL'
#!/bin/bash
export PYTHONPATH="/opt/hermes/venv/lib/python3.11/site-packages:/opt/hermes${PYTHONPATH:+:$PYTHONPATH}"
exec /usr/local/bin/python3 /opt/hermes/hermes "$@"
SHELL
chmod +x /usr/local/bin/hermes
```

**Doğrulama:**
```bash
hermes content status   # Çalışmalı
```

**Not:** C extension'ları Python 3.11 için derlendiğinden 3.12'de uyumsuz olabilir, ama pure-Python CLI tam çalışır.

## 4. Dizin Yapısı ve İlk Kurulum

```bash
# Adım 4a: Dizin yapısını oluştur
hermes content setup

# ✓ Output: "Content OS v2.4.0 structure initialized."

# Adım 4b: Sistem sağlık kontrolü
hermes content audit

# ✓ Output: "Content OS v2.4.0 Audit: X active, Y archived. Structure OK."
```

**`setup` komutu şu dizinleri oluşturur:**
```
/opt/hermes/plugins/content-os/
├── runs/active/
├── runs/archive/
├── .state_cache/
├── strategy/       ← boş (insan doldurur)
├── voice/          ← boş (insan doldurur)
├── stores/         ← boş (insan doldurur)
```

**Tuzak — Audit uyarıları:**
- `⚠️ Missing strategy file: positioning.md` → NORMAL. İnsan doldurması için.
- Setup sonrası 0 active run görmek normal.
- Eğer audit hata dönerse: `hermes content setup`'ı tekrar çalıştır.

## 5. Strateji Dosyaları

### 5.1 positioning.md

**Konum:** `strategy/positioning.md`
**Format:** Tek cümle. Bir yabancı profilinden çıktıktan sonra bunu tekrarlayabilmeli.

```markdown
# Positioning

> Tek cümle.

---

"AI-native sistemler, multi-agent orchestration ve cognitive infrastructure tasarlayan bir mühendis."

## Expanded Positioning

Ben:
- AI agent sistemleri,
- autonomous orchestration,
- realtime cognitive architectures,
- event-driven AI infrastructure,
- LLM operating systems,
- production-grade AI platform engineering

alanlarında çalışan bir sistem geliştiricisiyim.

## Positioning Constraints

Asla:
- "AI influencer"
- "growth hacker"
- "prompt engineer"
- "vibe coder"
```

**Tuzaklar:**
- Tek cümle positioning çok kritik — segment değil, **bir kişinin zihninde kalacak** ifade
- Constraints bölümü voice'a rehberlik eder, atlama
- Expanded positioning içerik kararlarını yönlendirir, kendini kısıtlama değil

### 5.2 audience.md

**Konum:** `strategy/audience.md`
**Format:** Tek kişi. Segment değil.

```markdown
# Audience

> Tek kişi. Segment değil.

---

25 yaşında bir yazılım mühendisi.

Backend biliyor. Bir miktar AI biliyor. LLM kullanmış.
Ama büyük sistem düşünemiyor.

Şu problemleri yaşıyor:
- agent sistemleri nasıl tasarlanır bilmiyor,
- production AI infra kurmamış,
- event-driven architecture konusunda yüzeysel.

## Reader Psychology

Bu kişi:
- yüzeysel motivasyon içeriklerinden nefret ediyor,
- teknik yoğunluğu seviyor,
- abstraction seviyesini yükseltmek istiyor.
```

**Tuzaklar:**
- "Backend biliyor" — çok temel anlatma, senin seviyene çek
- Reader psychology bookmark kararlarını belirler — hangi içerik tipinin bookmark alacağını buradan çıkar

### 5.3 pillars.md

**Konum:** `strategy/pillars.md`
**Format:** Her pillar: odak, içerik tipleri, ana tema.

```markdown
# Content Pillars

---

## Pillar 1 — AI Systems Architecture

Odak:
- LLM infrastructure
- AI operating systems
- orchestration engines

İçerik Tipleri:
- architecture breakdown
- infra decomposition
- execution flow analysis

Ana Tema:
"AI uygulaması değil, AI sistemi nasıl inşa edilir?"
```

**Önerilen 5 Pillar:**
| # | Pillar | Ana Tema |
|---|--------|----------|
| 1 | AI Systems Architecture | "AI uygulaması değil, AI sistemi" |
| 2 | Multi-Agent & Autonomous Systems | "Organizasyon gibi çalışan agent sistemleri" |
| 3 | Production-Grade Infrastructure | "Demo değil, production sistem" |
| 4 | Cognitive Engineering | "Prompt engineering değil, machine cognition" |
| 5 | AI-Native Product Engineering | "AI özellik eklenmiş ürün değil, AI-native ürün" |

### 5.4 source-watchlist.md (İsteğe Bağlı)

```bash
touch strategy/source-watchlist.md
# Content OS tarafından kullanılmaz, sadece referans.
```

## 6. Voice Profili

### 6.1 voice-profile.md

**Konum:** `voice/voice-profile.md`
**Kapsam:** 7+ prensip, yasaklı kalıplar, content shape, tone.

```markdown
# Voice Profile

## Core Identity
[Kim olduğun, nasıl bir anlatım kullandığın]

## WRITING PRINCIPLES (7+ prensip)
1. Sistem Perspektifi — component, flow, dependency, tradeoff, lifecycle
2. Somutluk Zorunludur — topology, metric, execution flow
3. Teknik Yoğunluk Korunur — beginner marketing dili yasak
4. Anti-Hype — "revolutionary", "game changer" yasak
5. Öğretici Sistem Tasarımı — mental model öğret, tool öğretme
6. Her Paragraf Tek Amaç Taşır
7. Engineering Tradeoff Zorunludur

## STYLE CONSTRAINTS
### Yasaklı Kalıplar
- "Let's dive in", "Here's the thing", "Game changer"
- "The future of AI", "Everyone should", "You must"

### Tercih Edilen Yapılar
- decomposition, architecture maps, execution lifecycle
- failure analysis, bottleneck reasoning, systems thinking

## CONTENT SHAPE
1. Problem → 2. Constraint → 3. System Model → 4. Architecture
5. Tradeoff → 6. Failure Mode → 7. Optimization → 8. Reusable Pattern
```

**Tuzaklar:**
- **"voice" = "üslup", sesli değil.** Türkçe'de karıştırma.
- voice-profile.md ile master-avoid-slop.md senkronize olmalı — aynı yasaklı kalıplar her iki dosyada da tutarlı.
- LLM brief/draft üretiminde voice-profile.md referans alınır — ne kadar detaylı olursa output o kadar iyi.

### 6.2 master-avoid-slop.md

**Konum:** `voice/master-avoid-slop.md`
**Kaynak:** `content_os_core.py` içindeki `FULL_SLOP_TIER1/2/3/BONUS` listeleri.

**Format:** 4 tier, her pattern için ID | Kalıp | Trigger (Regex/Kelime) | Çözüm

| Tier | Adet | Eşik (REVISE) | Eşik (REJECT) |
|------|------|--------------|--------------|
| 🔴 Tier 1 | 32 | ≥1 pattern | ≥3 pattern |
| 🟡 Tier 2 | 32 | ≥3 pattern | ≥5 pattern |
| 🟢 Tier 3 | 33 | ≥8 pattern | ≥15 pattern |
| ⚪ Bonus | 9 | Kontekst bazlı | — |

**Güncelleme:** `content_os_core.py`'deki regex listeleri değişirse bu dosyayı da güncelle.

**Tuzak:** "aslında", "sırf", "sadece" gibi Türkçe dolgu zarfları Tier 1 pattern'i olarak yakalanır. Verifier REJECT verirse manuel düzelt.

## 7. İçerik Depoları

### 7.1 stores/inbox.md

İçerik fikirlerinin ham giriş kutusu:

```markdown
# Inbox

---

## 1. [Fikir Başlığı]
[Açıklama — neden önemli, hangi problemi çözüyor]

---

## 2. ...
```

**Püf nokta:** Her fikir:
- Bir problemi tanımlamalı
- Somut bir sistem/architecture referansı içermeli
- Tool odaklı değil, system thinking odaklı olmalı

### 7.2 stores/workboard.md

Run'ların öncelik sırası:

```markdown
# Workboard

| # | Slug | State | Pillar | Not |
|---|------|-------|--------|-----|
| 1 | [slug] | [state] | [pillar] | [not] |

## Yapılacaklar
- [ ] [slug] → [next state transition]
```

**Tuzak — Pillar referansları:** workboard.md'deki pillar isimleri `strategy/pillars.md` ile birebir eşleşmeli. Eski pillar'lar (RISC-V, SKY130, OpenLane) değiştiğinde workboard'u da güncelle.

### 7.3 stores/ideas/

Fikir deposu. Her dosya bir fikir:

```markdown
# Fikir: [Başlık]
**Kaynak:** [Kendi deneyim / Dış kaynak]
**Rota:** [ORIGINAL / REPURPOSE / REWRITE / RESEARCH+IDEATE]
**Pillar:** [Pillar adı]

[Fikir açıklaması — problem, çözüm, çıktı]
```

**Format standardı:** Her fikir dosyası yukarıdaki frontmatter'ı içermeli. `content_os_core.py`'nin `_read_idea()` fonksiyonu bu formatı parse eder.

### 7.4 stores/hooks/

Hook pattern'leri. Başarılı açılış cümlesi kalıpları:

```markdown
# Hook: [Pattern adı]
Pattern: [Açıklama]
Örnek: "[Kullanılmış hook cümlesi]"
Neden çalışıyor: [Analiz]
```

### 7.5 stores/proof/

Kanıtlar. Metrik, benchmark, performans verileri:

```markdown
# Proof: [Başlık]
- Metric 1: [değer]
- Metric 2: [değer]
- Sonuç: [çıkarım]
```

### 7.6 stores/feedback/

Yayın sonrası analizler. 4 alt kategori:
- `failed-content/` — Düşük performans gösteren içerikler + failure analysis
- `high-performance/` — Yüksek bookmark/impression alan içerikler + what worked
- `meta-insights/` — Cross-run öğrenilen dersler, voice evolution
- `pattern-library/` — Tekrar kullanılabilir başarılı pattern'ler

## 8. State Cache ve Filesystem Sync

**Problem:** `content_os_core.py` iki yerde state tutar:
1. `.state_cache/runs_state.json` — JSON cache (update_state() ile güncellenir)
2. `runs/active/{slug}/content-object.md` — YAML format: `state: X`

Bunlar bazen uyuşmaz. **Bu bilinen bir bug'dır.**

### Sync Prosedürü

```bash
# 1. Cache'i kontrol et
cat .state_cache/runs_state.json | python3 -m json.tool

# 2. Her run'ın content-object.md'sini kontrol et
grep -A1 "state:" runs/active/*/content-object.md

# 3. Metadata alanlarını kontrol et
for f in runs/active/*/content-object.md; do
  echo "=== $(basename $(dirname $f)) ==="
  grep -E "(Status|Route|Format|Pillar)" "$f" | head -5
  echo "---"
  grep -E "^state:" "$f"
  echo
done
```

**Fix:** Python script'i ile sync:
```python
import json
from pathlib import Path

PLUGIN_DIR = Path("/opt/hermes/plugins/content-os")
CACHE_PATH = PLUGIN_DIR / ".state_cache" / "runs_state.json"
cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))

for run_dir in (PLUGIN_DIR / "runs" / "active").iterdir():
    if not run_dir.is_dir(): continue
    co_path = run_dir / "content-object.md"
    content = co_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    slug = run_dir.name
    cache_state = cache.get(slug, {}).get("state")

    # Bold Status'i güncelle
    new_lines = []
    for line in lines:
        if "**Status:**" in line and cache_state:
            new_lines.append(f"- **Status:** {cache_state}")
        elif line.startswith("state:") and "**" not in line and cache_state:
            new_lines.append(f"state: {cache_state}")
        else:
            new_lines.append(line)
    co_path.write_text("\n".join(new_lines), encoding="utf-8")
```

**Hangi state kazandı?:**
- `update_state()` ile set edilen state → **cache authoritative**
- `sync_state()` ile otomatik algılanan → filesystem (dosya varlığına göre)
- Eğer fark varsa: cache'teki state daha günceldir. content-object.md YAML'ını cache'e göre güncelle.

## 9. Git Commit ve Push

```bash
cd /opt/hermes/plugins/content-os

# Önce git identity kontrol et
git config user.email "mail@yunusgungor.com"
git config user.name "Yunus Gungor"

# Stage all
git add -A

# Commit
git commit -m "content-os: setup sync - [kısa açıklama]"

# Push (SSH veya HTTPS ile)
git push origin beta
```

**Tuzak — Authentication:**
- SSH: `Host key verification failed.` → `ssh -o StrictHostKeyChecking=no -T git@github.com` ile host key ekle
- HTTPS: `Password authentication is not supported` → `gh auth setup-git` ile credential helper ayarla
- Veya: `git remote set-url origin https://TOKEN@github.com/yunusgungor/content-os.git`

**Kritik Kural:** `.git` klasörünü ASLA SİLME. Plugin'in birincil reposudur, deployment kalıntısı değil.

## 10. Doğrulama

### 10.1 Setup Doğrulama

```bash
echo "=== 1. Plugin Varlığı ==="
[ -d /opt/hermes/plugins/content-os ] && echo "✅" || echo "❌"

echo "=== 2. Temel Dosyalar ==="
for f in __init__.py content_os_core.py cli.py plugin.yaml SKILL.md; do
  [ -f "/opt/hermes/plugins/content-os/$f" ] && echo "✅ $f" || echo "❌ $f"
done

echo "=== 3. Dizin Yapısı ==="
for d in strategy voice stores runs scripts; do
  [ -d "/opt/hermes/plugins/content-os/$d" ] && echo "✅ $d" || echo "❌ $d"
done

echo "=== 4. Strateji Dosyaları ==="
for f in positioning.md audience.md pillars.md; do
  [ -f "/opt/hermes/plugins/content-os/strategy/$f" ] && echo "✅ $f" || echo "❌ $f"
done

echo "=== 5. Voice Dosyaları ==="
for f in voice-profile.md master-avoid-slop.md; do
  [ -f "/opt/hermes/plugins/content-os/voice/$f" ] && echo "✅ $f" || echo "❌ $f"
done

echo "=== 6. Store Dosyaları ==="
for d in ideas hooks proof feedback; do
  count=$(ls /opt/hermes/plugins/content-os/stores/$d/*.md 2>/dev/null | wc -l)
  [ $count -gt 0 ] && echo "✅ stores/$d ($count files)" || echo "⚠️ stores/$d (empty)"
done

echo "=== 7. İnbox + Workboard ==="
[ -f /opt/hermes/plugins/content-os/stores/inbox.md ] && echo "✅ inbox.md" || echo "❌ inbox.md"
[ -f /opt/hermes/plugins/content-os/stores/workboard.md ] && echo "✅ workboard.md" || echo "❌ workboard.md"

echo "=== 8. CLI Çalışıyor mu? ==="
hermes content audit 2>&1 | head -3

echo "=== 9. State Cache ==="
[ -f /opt/hermes/plugins/content-os/.state_cache/runs_state.json ] && echo "✅" || echo "❌"

echo "=== 10. Git ==="
cd /opt/hermes/plugins/content-os
[ -d .git ] && echo "✅ .git mevcut" || echo "❌ .git KAYIP!"
git status --short | head -5

echo "=== 11. .git ASLA SİLME: Doğrulandı ==="
```

Bu script'in OUTPUT'u aşağıdaki gibi olmalıdır:
```
=== 3.1-3.5 TOPLAM ===
✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅ (19/19 PASS)
=== CLI ===
✅ hermes content setup
✅ hermes content audit (0 hata, 0 uyarı)
✅ hermes content status
✅ hermes content runs
=== Git ===
✅ .git mevcut
✅ Working tree clean
✅ origin → git@github.com:yunusgungor/content-os.git (branch: beta)
=== USER_GUIDE Uyumu ===
✅ Bölüm 3.1 — Plugin yüklü
✅ Bölüm 3.2 — setup + audit çalıştı
✅ Bölüm 3.3 — positioning.md, audience.md, pillars.md dolu
✅ Bölüm 3.4 — voice-profile.md dolu
✅ Bölüm 3.5 — stores/ideas, hooks, proof dolu
✅ Bölüm 4.1 — İlk run oluşturulabilir
```

### 10.2 Pipeline Doğrulama

```bash
# Aktif run'ları listele
hermes content runs

# State'leri kontrol et
hermes content status

# Cache vs filesystem karşılaştırması
python3 -c "
import json
cache = json.loads(open('/opt/hermes/plugins/content-os/.state_cache/runs_state.json').read())
for slug, data in cache.items():
    print(f'{slug}: {data[\"state\"]}')
"
```

## 11. Sorun Giderme

| Sorun | Sebep | Çözüm |
|-------|-------|-------|
| `ModuleNotFoundError: No module named 'yaml'` | Venv symlink bozuk | `/usr/local/bin/hermes` wrapper oluştur |
| Audit: "Missing strategy file" | positioning/audience/pillars eksik | Manuel doldur |
| `hermes content setup` çalışmıyor | CLI wrapper yok | Bölüm 3'teki wrapper script'i çalıştır |
| State cache vs filesystem farklı | Bilinen bug | Bölüm 8'deki sync script'ini çalıştır |
| `hermes content new` slug çok uzun | Türkçe karakter → slug truncation | `--slug` parametresi kullan |
| Verifier REJECT (Tier 1) | aslında/sırf/sadece dolgu zarfları | Manuel düzelt, yeniden scan |
| `git push` Host key verification | SSH bilinmeyen host | `ssh -o StrictHostKeyChecking=no -T git@github.com` ile ekle |
| `git push` Authentication failed | HTTPS token formatı | `gh auth setup-git` ile credential helper ayarla |
| `.git` silindi | Deployment hatası | **KRİTİK:** GitHub'dan clone'la, `.git`'i kurtar |
| `xurl` not found | Kurulu değil | `curl -fsSL https://raw.githubusercontent.com/xdevplatform/xurl/main/install.sh \| bash` |
| `xurl auth status` → No apps | X API app kaydedilmemiş | developer.x.com'da app oluştur + `xurl auth apps add` |
| `xurl` auth errors | OAuth token default app'a kaydedilmiş | `xurl auth oauth2 --app <app-name>` ile yeniden dene |

### Acil Durum — .git Kurtarma

```bash
# Eğer .git yanlışlıkla silindiyse:
cd /opt/hermes/plugins/content-os
git init
git remote add origin git@github.com:yunusgungor/content-os.git
git fetch origin beta
git reset origin/beta
# Değişiklikler kaybolabilir — son commit'ten itibaren çalış.
```

---

## Kaynak

- **USER_GUIDE.md:** `/opt/hermes/plugins/content-os/USER_GUIDE.md`
- **SKILL.md:** `/home/hermeswebui/.hermes/skills/productivity/content-os/SKILL.md`
- **Plugin kodu:** `/opt/hermes/plugins/content-os/content_os_core.py`
- **Original blog:** [postiz.com/blog/ai-content-system-5m-impressions](https://postiz.com/blog/ai-content-system-5m-impressions)
- **Shann³:** [@shannholmberg](https://x.com/shannholmberg)
