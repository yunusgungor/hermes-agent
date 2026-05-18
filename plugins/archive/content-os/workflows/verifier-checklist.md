# Workflow: Verifier Checklist

> Adım adım doğrulama kontrol listesi. Verifier Agent veya insan reviewer için.

---

## Ön Hazırlık

**Çalıştırmadan önce:**
- [ ] `brief.md` mevcut ve dolu
- [ ] `draft-package.md` mevcut
- [ ] `voice-profile.md` mevcut
- [ ] `master-avoid-slop.md` mevcut
- [ ] `references/rubric-template.md` mevcut

**Okuma sırası:**
1. Önce `brief.md` — ne üretilmesi gerekiyordu?
2. Sonra `draft-package.md` — ne üretildi?
3. Sonra diğer referanslar

---

## KONTROL 1: Brief Uyumu

**Soru:** Taslak, brief'teki spesifikasyonlara uyuyor mu?

| Kontrol | Soru | Evet | Hayır |
|---------|------|------|-------|
| Thesis | Tek cümlelik thesis karşılandı mı? | ✅ | ❌ |
| Target Reader | Belirtilen kişi için mi yazıldı? | ✅ | ❌ |
| Angle | Beklenmedik çerçeve korundu mu? | ✅ | ❌ |
| Format | Belirtilen format kullanıldı mı? | ✅ | ❌ |
| Length | Uzunluk sınırlarına uyuldu mu? | ✅ | ❌ |
| Tone | Ton doğru mu? | ✅ | ❌ |
| Banned phrases | Yasaklı ifadeler kullanılmadı mı? | ✅ | ❌ |
| Proof | Belirtilen kanıtlar kullanıldı mı? | ✅ | ❌ |

**Kayıt:**
```
brief_check:
- Thesis delivered: [yes/partial/no] — [kanıt]
- Target reader served: [yes/partial/no] — [kanıt]
- Angle honored: [yes/partial/no] — [kanıt]
- Constraints met: [yes/partial/no] — [kanıt]
- Voice rules followed: [yes/no] — [ihlaller]
```

---

## KONTROL 2: Bookmarkability Rubric Puanlaması

**Her satır için 0, 1 veya 2 puan ver. Toplam 12 puan üzerinden hesapla.**

### Satır 1: Gelecek Görev Tasarrufu
```
Soru: Bu post, okuyucunun gelecekte yapacağı bir işi kısaltıyor mu?

0 puan: Sadece bilgi veriyor. Okuyucu bookmark'lasa bile tekrar gelip bir şey okuyacak ama bir şey YAPMAYACAK.
1 puan: Biraz faydalı ama net değil. Bookmark değeri belirsiz.
2 puan: Evet — post bookmark'lanınca okuyucu "bu gelecekte X yaparken işime yarayacak" diye düşünecek.

Kanıt: [Taslağın hangi kısmı bunu kanıtlıyor?]
Skor: [0/1/2]
```

### Satır 2: Kanıt
```
Soru: Somut veri, metrik, isimli örnek veya proje sonucu var mı?

0 puan: Sadece genel iddialar. "Birçok kişi bunu yapıyor" gibi.
1 puan: Zayıf kanıt. "Bazı projelerde X oldu" gibi, detaysız.
2 puan: Somut: "Y projesinde X sonucu", "4/10 kişi", "setup slack = -0.08ns" gibi.

Kanıt: [Tam olarak hangi veriler var?]
Skor: [0/1/2]
```

### Satır 3: Tekrar Kullanılabilir Takeaway
```
Soru: Okuyucu bu bilgiyi tekrar kullanabilir mi?

0 puan: Tek seferlik içgörü. Bilgi ama araç değil.
1 puan: Kısmen kullanışlı ama açıkça yapılandırılmamış.
2 puan: Evet — şablon, checklist, framework veya mental model aktif olarak sunulmuş.

Kanıt: [Hangi yapı tekrar kullanılabilir?]
Skor: [0/1/2]
```

### Satır 4: Hedef Kitle + İş Tanımı
```
Soru: Kimin için yazıldığı ve ne yapması gerektiği net mi?

0 puan: "herkes için", "mühendisler için", "creator'lar için" gibi genel hedef.
1 puan: Kısmen tanımlanmış ama belirsizlik var.
2 puan: Net: rol + durum + stake ile tanımlanmış spesifik kişi.

Kanıt: [Hedef kitle tam olarak kim?]
Skor: [0/1/2]
```

### Satır 5: Taşınabilirlik (Yazarsız Uygulanabilirlik)
```
Soru: Ben olmadan okuyucu bunu uygulayabilir mi?

0 puan: Talimat eksik. Benim deneyimim/bağlamım olmadan anlaşılmaz.
1 puan: Çoğunlukla uygulanabilir ama kritik boşluklar var.
2 puan: Birebir: adım adım veya şablon, bana ihtiyaç yok.

Kanıt: [Okuyucu bu bilgiyi tek başına uygulayabilir mi?]
Skor: [0/1/2]
```

### Satır 6: Görsel Gücü
```
Soru: Etkili bir görsel veya metinsel yapı var mı?

0 puan: Sadece düz metin. Hiç görsel yok ve metinsel yapı da zayıf.
1 puan: Zayıf. Genel bir resim veya basit metinsel yapı.
2 puan: Etkili: metrik içeren ekran görüntüsü, özel diyagram, önce/sonra karşılaştırması.

Kanıt: [Görsel veya metinsel yapı nasıl?]
Skor: [0/1/2]
```

### Toplam
```
Satır 1: ___/2
Satır 2: ___/2
Satır 3: ___/2
Satır 4: ___/2
Satır 5: ___/2
Satır 6: ___/2
─────────────────
TOPLAM:   ___/12
EŞİK:     8/12
GEÇER Mİ?: [EVET / HAYIR]
```

---

## KONTROL 3: Slop Taraması

**Her satır için kontrol et. Her ihlali kaydet.**

### Tier 1 — Sıfır Tolerans

| # | Kalıp | Kontrol | İhlal? |
|---|-------|---------|---------|
| 1 | Promosyon dili | "groundbreaking", "game-changing", "revolutionary" arama | [ ] Var [ ] Yok |
| 2 | Önem abartısı | "pivotal", "testament", "significant step" arama | [ ] Var [ ] Yok |
| 3 | Belirsiz atıf | "experts believe", "studies show" arama | [ ] Var [ ] Yok |
| 4 | Sahte etkinlik | "the system compounds", "the data tells us" arama | [ ] Var [ ] Yok |
| 5 | Retorik kurulum | "The question is whether", "At its core" arama | [ ] Var [ ] Yok |
| 6 | Staccato parçalama | "no X. no Y. no Z." pattern arama | [ ] Var [ ] Yok |
| 7 | Tire aşırı kullanımı | "--" (em dash) sayma → hedef: 0-1 | [ ] Sayı: ___ |
| 8 | Dolgu zarfları | "actually", "literally", "quietly", "simply" arama | [ ] Var [ ] Yok |

### Tier 2 & 3 — Hızlı Tarama

> **Tier 2 (8 kalıp — 9-16):** 3+ tespit = REVISE, 5+ = REJECT
> **Tier 3 (18+ kalıp — 17-34+):** Bağlamda değerlendir. Çok fazla = REVISE
> Tam liste: `references/avoid-slop-patterns.md`

**Tier 2 — Yüksek (Revize Et)**

|| # | Kalıp | Kontrol | İhlal? |
||---|-------|---------|---------|
|| 9 | Copula Avoidance | "serves as", "stands as", "features" arama | [ ] Var [ ] Yok |
|| 10 | -ing Padding | "-ing" ile biten gereksiz fiiller arama | [ ] Var [ ] Yok |
|| 11 | Rule of Three Zorlama | Mecburen 3'e dayatılmış listeler | [ ] Var [ ] Yok |
|| 12 | Filler Phrases | "In order to", "Due to the fact that" arama | [ ] Var [ ] Yok |
|| 13 | Generic Conclusions | "The future looks bright", "Exciting times ahead" | [ ] Var [ ] Yok |
|| 14 | Signposting | "Let's dive in", "Here's what you need to know" | [ ] Var [ ] Yok |
|| 15 | Hyperbolic Quantifiers | "every", "all", "always", "never", "totally" arama | [ ] Var [ ] Yok |
|| 16 | Hedging | "it could potentially", "it might be argued" arama | [ ] Var [ ] Yok |

**Tier 3 — Orta (Gözden Geçir)**

|| # | Kalıp | Kontrol | İhlal? |
||---|-------|---------|---------|
|| 17 | Passive Voice | "was done", "is being built" — özne gizli | [ ] Var [ ] Yok |
|| 18 | Elegant Variation | Aynı kavram 3+ farklı şekilde adlandırılmış | [ ] Var [ ] Yok |
|| 19 | False Ranges | "from basic to advanced" gibi anlamsız ölçekler | [ ] Var [ ] Yok |
|| 20 | Conjunction Overuse | "&" veya "But" ile başlayan aşırı cümleler | [ ] Var [ ] Yok |
|| 21 | Unnecessary Intensifiers | "very", "so", "such" gereksiz kullanımda | [ ] Var [ ] Yok |
|| 22 | Paragraph-Level Vagueness | Her paragrafta genel iddia, somut kanıt yok | [ ] Var [ ] Yok |
|| 23 | Rhetorical Questions as Statements | Soru şeklinde sunulan açık cevaplar | [ ] Var [ ] Yok |
|| 24 | Awkward List Introductions | "There are X things that..." aşırı başlangıç | [ ] Var [ ] Yok |
|| 25 | False Precision | "exactly 93.7%" gibi gereksiz hassasiyet | [ ] Var [ ] Yok |
|| 26 | Clichéd Metaphors | "level up", "dive deep", "game plan" | [ ] Var [ ] Yok |
|| 27 | Self-Referential Humility | "I may be wrong, but..." | [ ] Var [ ] Yok |
|| 28 | Empty Emphasis | KÖŞELI PARANTEZ veya UPPERCASE aşırı | [ ] Var [ ] Yok |
|| 29 | Temporal Vagueness | "recently", "lately", "these days" — zaman belirtmez | [ ] Var [ ] Yok |
|| 30 | False Balance | "Bazıları X diyor, bazıları Y diyor" | [ ] Var [ ] Yok |
|| 31 | Unearned Authority | "As someone who..." gereksiz | [ ] Var [ ] Yok |
|| 32 | Template Language | "In this post, we'll explore..." her post'ta aynı | [ ] Var [ ] Yok |
|| 33+ | Bonus Kalıplar (35-38) | Faux Authority, Vibes Over Data, Thread-Bait, Oversharing | [ ] Var [ ] Yok |

### İhlal Kaydı Formatı
```
avoid_slop_findings:
- [ ] LINE [N]: "[tam ifade]" — [kalıp adı] — [önerilen yeniden yazım]
- [ ] LINE [N]: "[tam ifade]" — [kalıp adı] — [önerilen yeniden yazım]
```

---

## KONTROL 4: Ses Kontrolü

**Voice profile'a karşı kontrol et:**

```
voice_check:
- Tüm 5 üslup kuralına uyuldu: [evet/hayır]
  - Kural 1: [uyuldu / ihlal edildi — kanıt]
  - Kural 2: [uyuldu / ihlal edildi — kanıt]
  - Kural 3: [uyuldu / ihlal edildi — kanıt]
  - Kural 4: [uyuldu / ihlal edildi — kanıt]
  - Kural 5: [uyuldu / ihlal edildi — kanıt]
- Yasaklı kalıp kullanıldı: [evet/hayır]
  - Yasak 1: [kullanıldı / kullanılmadı — kanıt]
  - Yasak 2: [kullanıldı / kullanılmadı — kanıt]
  - Yasak 3: [kullanıldı / kullanılmadı — kanıt]
  - Yasak 4: [kullanıldı / kullanılmadı — kanıt]
  - Yasak 5: [kullanıldı / kullanılmadı — kanıt]
- Referans post'lara benzerlik: [evet/hayır]
```

---

## VERDICT

**Tüm kontroller toplandı. Karar ver:**

```
┌─────────────────────────────────────────────────────┐
│  VERDICT                                             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Rubric Skor:     ___/12  (Eşik: 8/12)           │
│  Slop İhlalleri: [sayı]                           │
│  Ses Uyumu:       [tam / kısmi / bozuk]           │
│                                                     │
│  [ ] APPROVE                                       │
│      → Skor >= 8/12, slop ihlalleri <= 2,         │
│        ses uyumu tam veya kısmi                   │
│                                                     │
│  [ ] REVISE                                        │
│      → Skor >= 6/12, düzeltmeler spesifik        │
│        ve uygulanabilir                            │
│                                                     │
│  [ ] REJECT                                        │
│      → Skor < 6/12 veya slop ihlalleri >= 5      │
│        veya ses uyumu bozuk                       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Gerekli Düzeltmeler (REVISE için):**
```
required_fixes:
1. [Satır N]: [spesifik düzeltme talimatı]
2. [Satır M]: [spesifik düzeltme talimatı]
```

---

## Final Rapor Formatı

```markdown
# Verifier Report — {SLUG}
Tarih: {YYYY-MM-DD}
Verifier: {agent veya insan}

## brief_check
- Thesis delivered: [yes/partial/no] — [kanıt]
- Target reader served: [yes/partial/no] — [kanıt]
- Angle honored: [yes/partial/no] — [kanıt]
- Constraints met: [yes/partial/no] — [kanıt]
- Voice rules followed: [yes/no] — [ihlaller]

## rubric_scoring
- Saves reader a task: [0/1/2] — [kanıt]
- Includes proof: [0/1/2] — [kanıt]
- Reusable takeaway: [0/1/2] — [kanıt]
- Specific audience + job: [0/1/2] — [kanıt]
- Portable: [0/1/2] — [kanıt]
- Strong visual: [0/1/2] — [kanıt]
- TOTAL: [X/12]
- PASSES_THRESHOLD: [yes/no]

## avoid_slop_findings
- [ ] LINE [N]: "[ifade]" — [kalıp] — [öneri]
- (temizse boş list)

## voice_check
- Tüm kurallara uyuldu: [evet/hayır]
- Yasaklı kalıp: [evet/hayır]

## VERDICT: [APPROVE | REVISE | REJECT]

## required_fixes
1. [düzeltme]
2. [düzeltme]
```
