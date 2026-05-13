# Workflow: Feedback Loop

> Yayınlanmış post'ların metriklerini toplama, analiz etme ve sistemi güncelleme mekanizması.

---

## Genel Bakış

```
PUBLISHED (AŞAMA 10)
       │
       ├──► 24 SAAT SONRA ────────────────────► AŞAMA 11
       │         • Metrikleri topla                • İlk izlenimler
       │         • Bookmark oranı hesapla           • Hangi tweet en çok etkileşim aldı?
       │                                           • Beklentiler karşılandı mı?
       │
       ├──► 72 SAAT SONRA ────────────────────► AŞAMA 12
       │         • Derin metrik analizi             • Kalıcı örüntüler
       │         • Bookmark oranı (nihai)            • Ses insights
       │                                           • Slop tespiti
       │
       └──► 7 GÜN SONRA (opsiyonel) ──────────► AŞAMA 13+
                 • Uzun vadeli performans            • Sürdürülebilirlik
                 • Toplam etkileşim                  • Kalıcı değer
```

---

## AŞAMA 11: 24 Saat Feedback

### Veri Toplama

**Metrik Kaynağı:** X/Twitter Analytics veya xurl

```
┌─────────────────────────────────────────────────────┐
│  24 SAAT METRİKLER — {SLUG}                        │
│  Tarih: {YYYY-MM-DD} — Yayın: {YYYY-MM-DD HH:MM}  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  İMPRESSIONS (görüntülenme):  _________            │
│  ENGAGEMENTS (etkileşim):      _________            │
│  LIKES (beğeni):               _________            │
│  RETWEETS (rt):               _________            │
│  BOOKMARKS (yer imi):         _________  ⭐ ANA    │
│  REPLIES (yanıt):             _________            │
│  PROFILE VISITS:              _________            │
│  FOLLOWER DEĞİŞİMİ:           ±________            │
│                                                     │
│  ─────────────────────────────────────────────     │
│                                                     │
│  HESAPLAMALAR:                                      │
│  Bookmark oranı: bookmarks/impressions × 100 = ___%  │
│  Engagement oranı: engagements/impressions × 100 = _%│
│  Beğeni/İzlenim oranı: likes/impressions × 100 = __%│
│  RT/İzlenim oranı: rts/impressions × 100 = ___%    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Thread Performansı (Thread ise)

```
┌─────────────────────────────────────────────────────┐
│  THREAD PERFORMANS — {SLUG}                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Toplam Tweet: ___                                 │
│                                                     │
│  EN ÇOK ETKİLEŞİM ALAN TWEET:                   │
│  Tweet #{N}: "____________"                        │
│  Bookmark: ___ | Like: ___ | RT: ___ | Reply: ___ │
│                                                     │
│  EN DÜŞÜK PERFORMANS ALAN TWEET:                │
│  Tweet #{N}: "____________"                        │
│  Bookmark: ___ | Like: ___ | RT: ___ | Reply: ___ │
│                                                     │
│  GÖZLEM: Hangi kalıp en çok bookmark aldı?         │
│  _____________________________________________     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### İlk İzlenimler

```
┌─────────────────────────────────────────────────────┐
│  İLK İZLENİMLER                                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  BEKLENTİ DURUMU:                                  │
│  [ ] Beklentileri aştı                             │
│  [ ] Beklentilere ulaştı                          │
│  [ ] Beklentilerin altında kaldı                   │
│                                                     │
│  SÜRPRİZ OLAN:                                     │
│  _____________________________________________     │
│                                                     │
│  BEKLENMEDİK OLAN:                                 │
│  _____________________________________________     │
│                                                     │
│  HANGİ KISIM EN ÇOK İLGİ ÇEKTİ?                 │
│  _____________________________________________     │
│                                                     │
│  HANGİ KISIM HİÇ İLGİ ÇEKMEDİ?                  │
│  _____________________________________________     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## AŞAMA 12: 72 Saat Feedback

### Derin Metrik Analizi

```
┌─────────────────────────────────────────────────────┐
│  72 SAAT METRİKLER — {SLUG}                        │
│  Tarih: {YYYY-MM-DD}                               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  İMPRESSIONS (nihai):     _________  (artış: +___) │
│  BOOKMARKS (nihai):       _________  (artış: +___) │
│  LIKES (nihai):           _________  (artış: +___) │
│  RETWEETS (nihai):        _________  (artış: +___) │
│  REPLIES (nihai):         _________  (artış: +___) │
│  FOLLOWER DEĞİŞİMİ:       ±________                │
│                                                     │
│  ─────────────────────────────────────────────     │
│                                                     │
│  NİHAİ ORANLAR:                                    │
│  Bookmark oranı: ___% (nihai)                      │
│  Engagement oranı: ___%                            │
│  Lifetime viral katsayısı: ___ (opsiyonel)         │
│                                                     │
│  ─────────────────────────────────────────────     │
│                                                     │
│  KARŞILAŞTIRMA:                                    │
│  Bu post'un bookmark oranı: ___%                   │
│  Son 10 post'un ortalaması: ___%                   │
│  → {SLUG} ortalamanın {üzerinde/altında}        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Kalıcı Örüntüler Analizi

```
┌─────────────────────────────────────────────────────┐
│  KALICI ÖRÜNTÜLER — {SLUG}                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ALGORITMA PERFORMANSI:                           │
│  [ ] Feed'de organik yayılım başladı               │
│  [ ] Rakip post'lar altında görünüyor (QRT)       │
│  [ ] Yeni kaynak/hesap paylaştı                   │
│  [ ] Hiçbir örüntü yok                            │
│                                                     │
│  BOOKMARK KALICI MI?                               │
│  [ ] Evet — bookmark hâlâ artıyor                  │
│  [ ] Kısmen — ilk 24s'de yoğunlaştı              │
│  [ ] Hayır — pik noktasını geçti                  │
│                                                     │
│  YANIT TEMALARI (reply'lerden):                  │
│  En sık karşılaşılan soru: ____________________   │
│  En sık karşılaşılan yorum: ___________________   │
│  En sık karşılaşılan eleştiri: _________________   │
│                                                     │
│  BUNLARI TAKİP ET:                                │
│  [ ] Bookmark oranı ___% → Sonraki post'lerde      │
│        bu formatı/angle'ı kullan                  │
│  [ ] Reply'lerdeki soru → Gelecek post için       │
│        içerik fırsatı olarak kaydet               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Ses İçgörüleri (Voice Insights)

```
┌─────────────────────────────────────────────────────┐
│  SES İÇGÖRÜLERİ — {SLUG}                         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  SES KALlBI DOĞRU MUYDU?                          │
│  [ ] Evet — okuyucular sesin doğal olduğunu       │
│        belirtti                                     │
│  [ ] Kısmen — bazı yerlerde AI hissi var          │
│  [ ] Hayır — genel olarak ses otantik değil        │
│                                                     │
│  HANGİ CÜMLELER ÇOK SAMIMİ GELDİ?                │
│  1. "___________________________________"          │
│  2. "___________________________________"          │
│                                                     │
│  HANGİ CÜMLELER AI HİSSİ VERDİ?                  │
│  1. "___________________________________"          │
│     → Sebep: ___________________________________   │
│  2. "___________________________________"          │
│     → Sebep: ___________________________________   │
│                                                     │
│  ÜSLUP KURALI İHLALİ VAR MI?                        │
│  [ ] Yasak kalıp kullanıldı: ___________________ │
│  [ ] Üslup kuralı ihlal edildi: __________________  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Slop Tespiti (Post-Publish)

```
┌─────────────────────────────────────────────────────┐
│  SLOP TESPİTİ — {SLUG}                            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  YAYINLANDIKTAN SONRA FARK EDİLEN SLOP:          │
│  [ ] Yok                                            │
│  [ ] Var — aşağıda listele                        │
│                                                     │
│  Yeni slop kalıbı tespit edildi:                  │
│  1. Kalıp: "________________________________"     │
│     Nerede: Tweet #{N}                             │
│     Sebep: ___________________________________   │
│                                                     │
│  MASTER-AVOID-SLOP MD'E EKLE?                     │
│  [ ] Evet — eklenecek                             │
│  [ ] Hayır — tek seferlik                          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## AŞAMA 13: Learnings — Sistem Güncelleme

### Öğrenim Çıkarımı

```
┌─────────────────────────────────────────────────────┐
│  ÖĞRENİLENLER — {SLUG}                             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  BU POSTTAN ÇIKARILACAK 3 ŞEY:                  │
│                                                     │
│  1. İÇERİK STRATEJİSİ:                          │
│     ___________________________________________   │
│                                                     │
│  2. SES KALlBI:                                    │
│     ___________________________________________   │
│                                                     │
│  3. TEKNİK/DENEYİMSEL:                            │
│     ___________________________________________   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Sistem Güncellemeleri

**Güncellenecek dosyalar ve içerikler:**

| Dosya | Eylem | Detay |
|--------|-------|-------|
| `stores/hooks/` | Yeni hook ekle | Bookmark sürücüsü kalıbı |
| `stores/proof/` | Kanıt güncelle | Yeni metrikler varsa |
| `voice/voice-profile.md` | Üslup kuralı ekle/güncelle | Üslup içgörülerinden |
| `voice/master-avoid-slop.md` | Yeni slop ekle | Tespit edilen kalıp |
| `workflows/feedback-loop.md` | Sistem kalıbı güncelle | Kalıcı öğrenim |

### Güncelleme Kontrol Listesi

```
┌─────────────────────────────────────────────────────┐
│  SİSTEM GÜNCELLEME KONTROLÜ                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [ ] stores/hooks/{slug}.md oluşturuldu           │
│      Hook: "________________________________"       │
│                                                     │
│  [ ] voice/voice-profile.md güncellendi           │
│      Eklenen: ________________________________   │
│                                                     │
│  [ ] voice/master-avoid-slop.md güncellendi       │
│      Eklenen: ________________________________   │
│                                                     │
│  [ ] stores/proof/ güncellendi (varsa)            │
│      Eklenen: ________________________________   │
│                                                     │
│  [ ] Sonraki post'lar için not kaydedildi:       │
│      ____________________________________________   │
│                                                     │
│  [ ] Sonraki brief'ler için angle önerisi:       │
│      ____________________________________________   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Postmortem Prompt — Kullanım

> Postmortem Prompt, 72 saat feedback'in en kritik parçasıdır. **Her yayınlanmış post'tan sonra çalıştırılmalı.**

**Nasıl çalıştırılır:**
```
Postmortem Prompt'u çalıştır:
1. Tüm metrikleri topla (24s + 72s)
2. Postmortem prompt'unu modele ver
3. Model EXACT satırları işaret etmeli — "güçlü hook" değil
4. Çıkan sonuçları feedback.md'ye kaydet
5. Sistem güncellemelerini uygula
```

**Çıktı beklenen:**
```
# Postmortem — {SLUG}

## what_drove_bookmarks
1. "[exact quote]" — [specific reason this earned a bookmark]
2. "[exact quote]" — [specific reason this earned a bookmark]

## what_drove_engagement
1. "[exact quote]" — [specific reason this drove likes/retweets]

## what_missed
1. [specific thing that didn't land] — [why it probably fell flat]

## what_would_i_change
1. [specific revision I would make if doing it again]

## pattern_to_capture
[one reusable pattern from this post to add to hooks/ or proof/]

## update_to_voice_rules
[any new voice insight from this post to add to voice-profile.md]

## update_to_avoid_slop
[any new slop pattern noticed to add to master-avoid-slop.md]
```

---

## Weekly Aggregate Review

**Her hafta (Cronjob veya Manuel):**

```
┌─────────────────────────────────────────────────────┐
│  HAFTALIK PERFORMANS ÖZETİ                         │
│  Hafta: {YYYY-WN}                                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  TOPLAM POST SAYISI: ___                           │
│                                                     │
│  TOPLAM METRİKLER:                                  │
│  - Toplam impressions: _________                    │
│  - Toplam bookmarks: _________                     │
│  - Ortalama bookmark oranı: ___%                   │
│  - En yüksek bookmark oranı: ___% (post: {slug}) │
│                                                     │
│  EN İYİ PERFORMANS:                                 │
│  1. {slug} — ___ bookmarks, ___% oran              │
│  2. {slug} — ___ bookmarks, ___% oran              │
│  3. {slug} — ___ bookmarks, ___% oran              │
│                                                     │
│  EN DÜŞÜK PERFORMANS:                               │
│  1. {slug} — ___ bookmarks, ___% oran             │
│  2. {slug} — ___ bookmarks, ___% oran             │
│                                                     │
│  KALICI ÖRÜNTÜLER:                                 │
│  _____________________________________________     │
│                                                     │
│  SONRAKİ HAFTA İÇİN DERSLER:                      │
│  _____________________________________________     │
│                                                     │
└─────────────────────────────────────────────────────┘
```
