# Workflow: Idea → Published Post

> 13 aşamalı ana playbook. Her içerik objesi bu workflow'u takip eder.
> Bu workflow, Production Leader (Hermes Agent) tarafından yürütülür.

---

## Genel Bakış

```
╔════════════════════════════════════════════════════════════╗
║  IDEA → PUBLISHED POST — 13 AŞAMA                       ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  AŞAMA 1:  captured                                       ║
║     │                                                     ║
║     ▼                                                     ║
║  AŞAMA 2:  idea_review ───────────────────────────────┐   ║
║     │ (Rota kararı: ORIGINAL/REPURPOSE/              │   ║
║     │          REWRITE/RESEARCH+IDEATE)               │   ║
║     ▼                                                   │   ║
║  AŞAMA 3:  brief_ready                                 │   ║
║     │                                                   │   ║
║     ▼                                                   │   ║
║  AŞAMA 4:  drafting ───► brief.md okunur            │   ║
║     │         (Writer Agent çalıştırılır)            │   ║
║     ▼                                                   │   ║
║  AŞAMA 5:  verification ───► verifier-report.md       │   ║
║     │ (Rubric + Slop kontrolü)                       │   ║
║     ▼                                                   │   ║
║  AŞAMA 6:  draft_review ───► İnsan onayı beklenir   │   ║
║     │ (Verifier sonuçlarına göre:                    │   ║
║     │  • APPROVE → AŞAMA 7                          │   ║
║     │  • REVISE → AŞAMA 3'e dön (brief güncelle)   │   ║
║     │  • REJECT → Fikir çöpe, inbox'a dön           │   ║
║     ▼                                                   │   ║
║  AŞAMA 7:  approved                                    │   ║
║     │                                                   │   ║
║     ▼                                                   │   ║
║  AŞAMA 8:  scheduler_ready ───► Schedule'e hazırla  │   ║
║     │ (görsel optimizasyonu, hashtag, zamanlama)      │   ║
║     ▼                                                   │   ║
║  AŞAMA 9:  scheduled                                   │   ║
║     │                                                   │   ║
║     ▼                                                   │   ║
║  AŞAMA 10: published                                   │   ║
║     │                                                   │   ║
║     ▼                                                   │   ║
║  AŞAMA 11: feedback_24h ───► 24s sonra kontrol     │   ║
║     │ (Bookmark, impression, engagement sayılarıı)    │   ║
║     ▼                                                   │   ║
║  AŞAMA 12: feedback_72h ───► 72s sonra derin analiz│   ║
║     │ (Kalıcı örüntüler, voice insights)             │   ║
║     ▼                                                   │   ║
║  AŞAMA 13: learned ──► Sonuçlar stores/'a yazılır   │   ║
║     │ (voice-profile, hooks/, proof/ güncellenir)   │   ║
║     ▼                                                   │   ║
║     └──────────────────────────────────────────────────┘   ║
║                                                            ║
║  ARŞİV: runs/active/'dan runs/archive/'a taşı           ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

## Aşama Detayları

### AŞAMA 1: captured
**Açıklama:** İçerik fikri ilk kez sisteme girer.

**Giriş:**
- Signal katmanından gelen fikir (dış)
- Kişisel OS'den gelen düşünce (iç)
- Mevcut içerikten türetilen fikir (yeniden kullanım)

**Çıkış:** `runs/active/{slug}/content-object.md` oluşturulur.
```markdown
# Content Object — {SLUG}

## Meta
- **ID:** {unique-id}
- **Created:** {YYYY-MM-DD HH:MM}
- **Status:** captured
- **Source:** {signal_layer | knowledge_graph | existing_content}

## Planlama
- **Format:** {tahmini format}
- **Pilar:** {tahmini pilar}
- **Deadline:** {opsiyonel}
```

**Eylem:** Run folder oluştur, content-object.md yaz.

---

### AŞAMA 2: idea_review
**Açıklama:** Fikir için en uygun rota seçilir.

**Soru:** "Bu fikir nereden geldi ve ne tür bir içerik olacak?"

**Rota Seçimi:**

| Sorgu | Cevap | Rota |
|--------|-------|------|
| "Bu fikir kişisel deneyimimden mi geliyor?" | Evet | **ORIGINAL** |
| "Mevcut bir içeriğimi türetebilir miyim?" | Evet | **REPURPOSE** |
| "Dışarıdan bir kaynaktan ilham aldım mı?" | Evet | **REWRITE** |
| "Bir konuyu araştırıp fikir mi üretiyorum?" | Evet | **RESEARCH+IDEATE** |

**Çıkış:** `idea.md` oluşturulur:
```markdown
# Idea — {SLUG}

## Kaynak
- **Rota:** {ORIGINAL | REPURPOSE | REWRITE | RESEARCH+IDEATE}
- **Kaynak detay:** {link veya referans}

## Gerekçe
{Bu rotanın neden seçildiğinin açıklaması}

## Rota Kuralları
- [ ] ORIGINAL: Dış kaynak YOK, yüksek zevk gerekli
- [ ] REPURPOSE: Mevcut içerik referansı belirtildi
- [ ] REWRITE: Kaynak açıkça belirtildi, atıf kuralları tanımlandı
- [ ] RESEARCH+IDEATE: Çıktı POST DEĞİL, fikir listesi
```

**Eylem:** `idea.md` yaz. Run folder'ı güncelle: `content-object.md` → status: "idea_review".

---

### AŞAMA 3: brief_ready
**Açıklama:** Writer context packet yazılır.

> ⭐ **EN KRİTİK AŞAMA.** Brief ne kadar sıkı olursa, taslak o kadar iyi gelir.

**Yazım Kuralları:**
- Hedef: 400-900 token
- Her alan zorunlu
- Sadece BU post için geçerli bilgiler
- Üslup kuralları referans olarak dahil, her şey DEĞİL

**Çıkış:** `brief.md` — Tam şablon için SKILL.md'ye bakın.

**Eylem:** `brief.md` yaz. content-object.md → status: "brief_ready".

---

### AŞAMA 4: drafting
**Açıklama:** Writer Agent çalıştırılır.

**Ön Koşullar:**
- `brief.md` mevcut ve dolu
- `voice-profile.md` mevcut
- `master-avoid-slop.md` mevcut

**Writer Agent Çağrısı:**
```
Rol: Writer Agent
Giriş dosyaları (sırayla oku):
1. brief.md
2. voice-profile.md
3. master-avoid-slop.md

GÖREV:
1. Üç dosyayı dikkatle oku
2. brief'e göre içeriği taslakla
3. Üslup kurallarını tam olarak takip et
4. rubric'in hangi satırının karşılanamadığını dürüstçe bildir
5. draft package formatında çıktı ver

ÇIKTI: draft-package.md formatı
```

**Çıkış:** `draft-package.md`
```
draft:
{taslak içerik}

rubric_self_assessment:
- Saves the reader a future task: [0/1/2] — [gerekçe]
- Includes proof: [0/1/2] — [gerekçe]
- Gives a reusable takeaway: [0/1/2] — [gerekçe]
- Has a specific audience: [0/1/2] — [gerekçe]
- Portable: [0/1/2] — [gerekçe]
- Strong visual: [0/1/2] — [gerekçe]
- TOTAL: [X/12]

avoid_slop_pass:
- [ ] LINE [N]: [kalıp ihlali] — [yeniden yazım önerisi]
- (temizse boş)

open_loops_flagged:
- [bilmediğim şey]
- (yoksa boş)

voice_check:
- Tüm 5 üslup kuralına uyuldu: [evet/hayır]
- Yasaklı kalıp kullanıldı: [evet/hayır — listele]
```

**Eylem:** content-object.md → status: "drafting". draft-package.md'yi yaz.

---

### AŞAMA 5: verification
**Açıklama:** Verifier Agent çalıştırılır.

**Ön Koşullar:**
- `draft-package.md` mevcut
- `brief.md` mevcut
- `rubric.md` mevcut
- `master-avoid-slop.md` mevcut

**Verifier Agent Çağrısı:**
```
Rol: Verifier Agent
Giriş dosyaları:
1. brief.md — post'un ne vermesi gerekiyordu
2. draft-package.md — yazarın çıktısı
3. rubric.md — kalite matrisi
4. master-avoid-slop.md — slop kalıpları

GÖREV:
1. 4 dosyayı oku
2. Taslağı her rubric satırına karşı kontrol et
3. Taslağı her avoid-slop kalıbına karşı kontrol et
4. Yeniden YAZMA — sadece bulguları raporla
5. APPROVE/REVISE/REJECT önerisi ver

ÇIKTI: verifier-report.md formatı
```

**Çıkış:** `verifier-report.md`
```
brief_check:
- Thesis delivered: [yes/partial/no] — [draft'tan kanıt]
- Target reader served: [yes/partial/no] — [kanıt]
- Angle honored: [yes/partial/no] — [kanıt]
- Constraints met: [yes/partial/no] — [kanıt]
- Voice rules followed: [yes/no] — [ihlaller varsa listele]

rubric_scoring:
- Saves reader a task: [0/1/2] — [spesifik kanıt]
- Includes proof: [0/1/2] — [spesifik kanıt]
- Reusable takeaway: [0/1/2] — [spesifik kanıt]
- Specific audience + job: [0/1/2] — [spesifik kanıt]
- Portable: [0/1/2] — [spesifik kanıt]
- Strong visual: [0/1/2] — [spesifik kanıt veya "sağlanmadı"]
- TOTAL: [X/12]
- THRESHOLD: 8/12
- PASSES: [yes/no]

avoid_slop_findings:
- [ ] LINE [N]: [kesin ifade] — [kalıp adı] — [yeniden yazım]
- (temizse boş)

VERDICT:
- [APPROVE] — eşik karşılandı, slop bulguları önemsiz
- [REVISE] — yakın ama spesifik düzeltmeler gerekli
- [REJECT] — eşik karşılanmadı, brief'e geri gönder

required_fixes:
- [spesifik, eyleme dönüştürülebilir düzeltme]
```

**Eylem:** content-object.md → status: "verification". verifier-report.md'yi yaz.

---

### AŞAMA 6: draft_review
**Açıklama:** İnsan (kullanıcı) onayı beklenir.

**Verifier Raporu Özeti:**
- Total skor: X/12
- Verdict: {APPROVE | REVISE | REJECT}
- Düzeltme gereken yerler: {list}

**Kullanıcıdan beklenen:**
```
┌─────────────────────────────────────────────────────┐
│  TASLAK DEĞERLENDİRME                              │
│                                                     │
│  Post: {SLUG}                                      │
│  Skor: {X}/12  Eşik: 8/12                        │
│  Verdict: {APPROVE | REVISE | REJECT}             │
│                                                     │
│  Yapılacak:                                        │
│  [ ] Taslağı oku                                   │
│  [ ] Ses kontrolü yap (benim sesime benziyor mu?) │
│  [ ] Verifier bulgularını kontrol et              │
│  [ ] Slop kontrollerini gözden geçir              │
│                                                     │
│  Onay:                                             │
│  [ ] YAYINLA                                       │
│  [ ] REVİZYON İSTE: {düzeltme talimatı}          │
│  [ ] REDDET: {gerekçe}                            │
└─────────────────────────────────────────────────────┘
```

**Eylem Seçenekleri:**

| Karar | Sonraki Aşama | Eylem |
|-------|--------------|-------|
| **APPROVE** | 7: approved | content-object.md → status: "approved" |
| **REVISE** | 3: brief_ready | `brief.md` güncelle, düzeltme talimatları ekle, AŞAMA 4'e dön |
| **REJECT** | — | Run folder'ı kapat, fikri inbox'a geri koy, `content-object.md` → status: "rejected" |

---

### AŞAMA 7: approved
**Açıklama:** İnsan onayı alındı. İçerik yayınlamaya hazır.

**Eylem:**
- `draft-package.md` içindeki taslağı son hali olarak onayla
- content-object.md → status: "approved"
- Tarih ve onaylayan kaydet

---

### AŞAMA 8: scheduler_ready
**Açıklama:** Yayınlama için son hazırlık.

**Kontrol Listesi:**
```
┌─────────────────────────────────────────────────────┐
│  SCHEDULER HANDOFF — Son Kontroller                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  GÖRSEL OPTİMİZASYONU:                            │
│  [ ] Görsel seçildi mi? (varsa)                  │
│  [ ] Görsel açıklaması (alt text) yazıldı mı?   │
│  [ ] Görsel dosya formatı doğru mu? (PNG/JPG)   │
│                                                     │
│  METADATA:                                         │
│  [ ] Hashtag'ler seçildi mi? (maksimum 3-5)     │
│  [ ] Mention edilecek hesap var mı?               │
│  [ ] CTA (call-to-action) belirlendi mi?          │
│                                                     │
│  ZAMANLAMA:                                        │
│  [ ] Yayınlama zamanı seçildi mı?                 │
│  [ ] Hedef kitle hangi zaman diliminde aktif?   │
│                                                     │
│  YEDEkleme:                                        │
│  [ ] Taslak bir yere kaydedildi mi?               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Eylem:** content-object.md → status: "scheduler_ready".

---

### AŞAMA 9: scheduled
**Açıklama:** İçerik planlayıcıya teslim edildi.

**Teslim Bilgisi:**
- Platform: X/Twitter
- Yayınlama zamanı: {tarih + saat}
- İçerik: {draft'tan final versiyon}
- Görsel: {varsa ek}
- Hashtag'ler: {list}

**Eylem:** content-object.md → status: "scheduled".

---

### AŞAMA 10: published
**Açıklama:** İçerik yayınlandı.

**Kayıt:**
- Yayınlama tarihi: {YYYY-MM-DD}
- Yayınlama saati: {HH:MM}
- Post URL: {link}
- Bookmark hedefi: {yok veya belirli bir rakam}

**Eylem:**
- content-object.md → status: "published"
- Yayınlama tarihini kaydet
- Post URL'yi kaydet
- AŞAMA 11 için zamanlayıcı kur (24 saat)

---

### AŞAMA 11: feedback_24h
**Açıklama:** 24 saat sonra ilk metrik kontrolü.

**Toplanacak Metrikler:**
```
┌─────────────────────────────────────────────────────┐
│  24 SAAT FEEDBACK — {SLUG}                         │
│  Tarih: {YYYY-MM-DD}                               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  METRİKLER:                                        │
│  - Impressions:    ___________                      │
│  - Engagements:   ___________                      │
│  - Likes:         ___________                      │
│  - Retweets:      ___________                      │
│  - Bookmarks:     ___________  ⭐ ANA METRİK       │
│  - Replies:       ___________                      │
│                                                     │
│  Bookmark oranı: bookmarks/impressions × 100 = ___% │
│                                                     │
│  EN ÇOK ETKİLEŞİM ALAN TWEET (thread ise):       │
│  _____________________________________________    │
│                                                     │
│  İLK GÖZLEMLER:                                   │
│  - Beklentiler karşılandı mı?                     │
│  - Sürpriz olan ne oldu?                         │
│  - Hangi kalıp bookmark aldı?                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Eylem:** `feedback.md` dosyasına 24s section yaz. content-object.md → status: "feedback_24h".

---

### AŞAMA 12: feedback_72h
**Açıklama:** 72 saat sonra derin analiz.

**Toplanacak Metrikler:**
```
- İmpressions (artış): ___________
- Bookmark oranı (nihai): ___%
- Kalıcı etkileşim (son 48s): ___________
```

**Derin Analiz:**
```
┌─────────────────────────────────────────────────────┐
│  72 SAAT FEEDBACK — {SLUG}                         │
│  Tarih: {YYYY-MM-DD}                               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  KALICI ÖRÜNTÜLER:                                │
│  1. ____________________________________________  │
│  2. ____________________________________________  │
│                                                     │
│  EN İYİ PERFORMANS:                               │
│  - Hangi format/en iyi çalıştı?                  │
│  - Bookmark oranı: ___%                           │
│                                                     │
│  EN DÜŞÜK PERFORMANS:                             │
│  - Neden beklenenden düşük?                       │
│  - Eksik olan ne?                                 │
│                                                     │
│  VOICE INSIGHTS:                                   │
│  - Ses kalıbı doğru muydu?                        │
│  - Hangi cümleler çok samimi geldi?               │
│  - Hangi kalıplar AI hissi verdi?                 │
│                                                     │
│  SLOP TESPİTİ (varsa):                            │
│  - Tespit edilen yeni slop kalıbı: _____________  │
│  - master-avoid-slop.md'a ekle: [evet/hayır]      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Eylem:** `feedback.md` dosyasına 72s section yaz. content-object.md → status: "feedback_72h".

---

### AŞAMA 13: learned
**Açıklama:** Öğrenilenler çıkarılır ve sistem güncellenir.

**Güncellenecek Dosyalar:**

| Dosya | Ne Güncellenir | Nasıl |
|--------|---------------|-------|
| `voice/voice-profile.md` | Yeni ses kalıbı veya düzeltme | feedback'ten çıkan ses insights |
| `stores/hooks/` | Yeni başarılı hook | Bookmark sürücüsü hook'lar |
| `stores/proof/` | Yeni kanıt (varsa) | Metrik içeren veriler |
| `stores/feedback/` | Bu post'un tam analizi | feedback.md arşiv olarak |
| `workflows/feedback-loop.md` | Sistem kalıpları | Kalıcı öğrenimler |

**Öğrenim Çıktısı Formatı:**
```markdown
# Learnings — {SLUG}

## Bu Post'tan Çıkarılanlar

### Ses
- [Yeni ses kalıbı veya insight]

### İçerik
- [Başarılı olan format veya angle]

### Strateji
- [Sonraki post'lar için ders]

## Sistem Güncellemeleri
- [ ] voice-profile.md güncellendi
- [ ] hooks/ eklendi
- [ ] proof/ güncellendi
- [ ] master-avoid-slop.md güncellendi (varsa)
```

**Eylem:** Tüm güncellemeleri yap. content-object.md → status: "learned".

---

## Arşivleme

**Tetikleyici:** AŞAMA 13 tamamlandığında.

**Eylem:**
1. Run folder'ı `runs/active/`'dan `runs/archive/`'a taşı
2. Tüm dosyalar korunur
3. Arşiv loguna kaydet

```bash
mv /content-os/runs/active/{slug} /content-os/runs/archive/{slug}
echo "ARCHIVED: {slug} | {YYYY-MM-DD} | bookmarks: {N}" >> /content-os/runs/archive/INDEX.md
```

---

## Hata Yönetimi

| Durum | Çözüm |
|-------|--------|
| Writer Agent düşük kaliteli çıktı verdi | brief.md'yi daha sıkı yeniden yaz. Proof bank'ı genişlet. |
| Verifier çok fazla slop buldu | Tier 1 (8 kalıp, ≥3 = REJECT) her taslakta ön kontrol et; Tier 2 (8 kalıp, 3+ = REVISE, 5+ = REJECT); Tier 3 (18+ kalıp, bağlamsal değerlendir) — detaylı tablo: `references/avoid-slop-patterns.md` |
| İnsan onay vermiyor | Angle veya format değişikliği öner. Kullanıcının endişesini anla. |
| Feedback kötü (düşük bookmark) | Postmortem çalıştır, rubric eksiklerini tespit et |
| İnspirasyon tıkandı | RESEARCH+IDEATE rotasına geç, sinyal katmanını tara |
