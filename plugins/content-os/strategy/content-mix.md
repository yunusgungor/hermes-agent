# Content Mix & Publishing Strategy

> Her içerik türünün bir amacı, bir hedef kitlesi ve bir başarı metriği vardır.
> Bu döküman, içerik oranlarını, yayın takvimini ve format dağılımını tanımlar.

---

## 📊 İçerik Oranları

### Dağılım (Haftalık)

| İçerik Türü | Haftalık Adet | Oran | Amaç |
|-------------|---------------|------|------|
| **Günlük AI News Thread** (P6) | 6 | %50 | Awareness + reach + new followers |
| **Orijinal Teknik Thread** (P1-P5) | 3 | %25 | Authority + bookmark + engagement |
| **Derinlik Analizi** (P6 → P1-P5) | 1 | %8 | Authority + cross-pillar |
| **Blog Yazısı** (P1-P5) | 1 | %8 | SEO + long-term traffic |
| **Haftalık AI Roundup** (P6) | 1 | %8 | Summary + bookmark |
| **Model Karşılaştırma / Trend** (Aylık) | 0.25 | %2 | Viral potansiyel |

**Toplam:** ~12 içerik/hafta + 4 blog/hafta

### Dağılım Mantığı

```
%50 News Thread (P6)
  → Sürekli görünürlük, yeni takipçi, düzenli reach
  → Düşük bookmark, yüksek impression, yüksek follower conversion

%25 Orijinal Thread (P1-P5)
  → Derin engagement, yüksek bookmark, authority
  → Düşük reach (algorithm), yüksek bookmark, yüksek mention

%25 Diğer (Derinlik, Blog, Roundup, Karşılaştırma)
  → SEO, long-tail traffic, cross-reference
  → En yüksek bookmark, en düşük reach, en yüksek DM
```

---

## 📐 İçerik Türü Tanımları

### 1. Günlük AI News Thread

| Özellik | Değer |
|---------|-------|
| **Tweet Sayısı** | 8 |
| **Uzunluk** | 800-1200 karakter toplam |
| **Haber Sayısı** | 3-5 (KRİTİK + YÜKSEK + ORTA) |
| **Hazırlık Süresi** | 20-30 dk |
| **Yayın** | Cron job ile 08:00 TSİ otomatik |
| **Hedef** | Awareness, reach, follower |
| **Bookmark Hedefi** | >50/thread |

### 2. Orijinal Teknik Thread

| Özellik | Değer |
|---------|-------|
| **Tweet Sayısı** | 10-15 |
| **Uzunluk** | 1500-2500 karakter |
| **Hazırlık Süresi** | 1-3 saat |
| **Yayın** | Manuel, Salı/Perşembe 14:00 TSİ |
| **Hedef** | Authority, bookmark, engagement |
| **Bookmark Hedefi** | >200/thread |

### 3. Blog Yazısı

| Özellik | Değer |
|---------|-------|
| **Kelime** | 2000-4000 |
| **Format** | Markdown → Blog platformu |
| **Diagram** | En az 2 architecture diagram |
| **Hazırlık Süresi** | 4-8 saat |
| **Yayın** | Haftada 1, Pazar |
| **Hedef** | SEO, long-term traffic, referans |
| **Aylık Görüntüleme** | >1000/yazı |

### 4. Derinlik Analizi

| Özellik | Değer |
|---------|-------|
| **Format** | 8-12 tweet thread |
| **Kaynak** | Bir haberin teknik derinlemesine |
| **Hedef** | Haber → authority funnel |
| **Yayın** | Haber sonrası 24-48 saat içinde |

---

## 📅 Haftalık Yayın Takvimi

| Gün | 08:00 TSİ | 14:00 TSİ | Ek |
|-----|-----------|-----------|----|
| **Pazartesi** | 🔵 Haftalık AI Roundup | 🟢 Orijinal Thread | |
| **Salı** | 🟡 Günlük AI News | 🟢 Orijinal Thread | |
| **Çarşamba** | 🟡 Günlük AI News | 🟠 Derinlik Analizi | |
| **Perşembe** | 🟡 Günlük AI News | 🟢 Orijinal Thread | |
| **Cuma** | 🟡 Günlük AI News | 🟠 Funding Roundup | |
| **Cumartesi** | 🟡 Günlük AI News | — | Model karşılaştırma (ayda 1) |
| **Pazar** | — | 📝 Blog yazısı | Gelecek hafta planlama |

**Renk kodları:**
- 🟡 Günlük — Cron job otomatik
- 🟢 Orijinal — Manuel, yüksek çaba
- 🟠 Derinlik — Haber bazlı, orta çaba
- 🔵 Haftalık — Hafta özeti, orta çaba
- 📝 Blog — En yüksek çaba

---

## 📈 İçerik Funnel

İçerik türleri bir funnel oluşturur:

```
                   ┌──────────────────┐
                   │  Günlük News     │  En geniş reach
                   │  (P6, 6/hafta)   │  Yeni takipçi kazanımı
                   └────────┬─────────┘
                            │
                   ┌────────▼─────────┐
                   │  Derinlik Analiz │  News → Authority
                   │  (P6→P1, 1/hft)  │  Daha derin engagement
                   └────────┬─────────┘
                            │
                   ┌────────▼─────────┐
                   │  Orijinal Thread │  En yüksek bookmark
                   │  (P1-5, 3/hft)   │  Authority inşası
                   └────────┬─────────┘
                            │
                   ┌────────▼─────────┐
                   │  Blog Yazısı     │  SEO + Long-term
                   │  (1/hft)         │  Referans kaynağı
                   └──────────────────┘
```

**Her içerik türü bir sonrakine trafik taşır:**
- News thread → içinde orijinal içeriğe link
- Derinlik analizi → blog yazısına referans
- Orijinal thread → blog yazısına link
- Blog → newsletter sign-up (gelecek)

---

## 📦 Format Dağılım Kuralları

### Tweet Thread Formatı (Tüm Türler İçin)

| Bileşen | Zorunlu mu? | Açıklama |
|---------|------------|----------|
| **Hook** (tweet 1) | ✅ | Haberin özü + neden önemli |
| **Teknik detay** | ✅ | Metrik, benchmark, architecture |
| **Yorum** | ✅ | Tradeoff, etki, bağlam |
| **Görsel** | ⬜ İsteğe bağlı | Architecture diagram (varsa %80 daha iyi) |
| **Link** | ✅ | Kaynak gösterimi |
| **Kapanış** | ✅ | Alınacak ders, öngörü |
| **#hashtag** | ⬜ | Sadece doğal kullanım |

### Blog Yazısı Formatı

| Bölüm | Açıklama |
|-------|----------|
| **Giriş** | Problem + neden önemli |
| **Arkaplan** | Bağlam, mevcut çözümler |
| **Architecture** | Sistem tasarımı (diagram zorunlu) |
| **Tradeoff** | Alternatifler + seçim gerekçesi |
| **Implementation** | Spesifik uygulama detayları |
| **Lessons Learned** | Production dersleri |
| **Sonuç** | Özet + reusable pattern |

---

## 📉 Düşük Performans Kriterleri

Bir içerik türü şu eşiklerin altındaysa gözden geçirilir:

| İçerik Türü | Düşük Performans | Aksiyon |
|-------------|------------------|---------|
| News thread | <5K impressions veya <20 bookmark | Kaynak kalitesini kontrol et |
| Orijinal thread | <50 bookmark | Topic seçimini gözden geçir |
| Blog | <500 views/ay veya <30 gün organik | SEO audit, başlık değiştir |
| Derinlik analizi | <1K impressions | Haber seçimi + timing |

---

## 📋 Aylık Content Mix Review

Her ay sonu:

- [ ] İçerik oranları hedefe uygun mu? (%50 news, %25 original, %25 other)
- [ ] Hangi içerik türü en iyi ROI'yi verdi?
- [ ] Hangi gün/saat en iyi performans?
- [ ] Yeni format eklenmeli mi? (video, podcast, newsletter)
- [ ] Düşük performanslı tür var mı?
- [ ] Funnel çalışıyor mu? (news → blog conversion)
