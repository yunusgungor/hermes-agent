# News Thread Templates — Somut Tweet Thread Şablonları

> Bu döküman, günlük AI news thread'leri için kullanılacak somut şablonları içerir.
> Her template farklı bir bükülük dağılımı ve format için tasarlanmıştır.

---

## 📐 ORTAK YAPI (Tüm Thread'ler İçin)

### Tweet Uzunluk Kuralları

| Tweet # | Hedef Karakter | Maksimum | Not |
|---------|---------------|----------|-----|
| **Tweet 1 (Hook)** | 180-220 | 250 | Kısa, etkili, merak uyandıran |
| **Tweet 2-6 (Detay)** | 220-260 | 280 | Teknik detay, metrik, yorum |
| **Tweet 7 (Kısa Haberler)** | 260-280 | 280 | Birden çok haber sıkıştırılır |
| **Tweet 8 (Kapanış)** | 180-220 | 250 | Özet + öngörü |

### Format Kuralları

- Her tweet başında 🔴/🟠/🟢 bükülük emojisi
- Kaynak linki son tweette veya thread içinde
- Her tweette en az 1 somut metrik veya teknik terim
- 8 tweette toplam en az 8 farklı teknik bilgi

---

## Template A: Klasik Günlük AI News (Varsayılan)

*Bükülük: 1 KRİTİK + 1 YÜKSEK + 1-2 ORTA*

```
Tweet 1: 🔴 KRİTİK: [Haber başlığı]

[Kim ne duyurdu? Tek cümle özü + neden şimdi önemli?]
[Sektörel etki — kim kazanır/kaybeder?]

Tweet 2: [Teknik derinlik]

[Neyin değiştiğini anlat — architecture, benchmark, metrik]
[Önceki durumla karşılaştır: X → Y, %Z iyileşme]
[Tradeoff: ne kazanıldı, ne kaybedildi?]

Tweet 3: [Sektörel etki]

[Rakiplere göre durumu]
[Benimseme engeli var mı?]
[Kısa vadeli etki: 3-6 ay içinde ne değişir?]

Tweet 4: 🟠 YÜKSEK: [İkinci haber başlığı]

[Ne oldu? Tek cümle]
[Neden önemli? — metrik veya etki göster]
[Bağlam: bu neden şimdi oldu?]

Tweet 5: [Detay]

[Teknik analiz veya karşılaştırma]
[Varsa benchmark, latency, veya maliyet verisi]

Tweet 6: 🟢 [Üçüncü haber başlığı]

[Kısa + yorum — 2-3 cümle]

Tweet 7: 🟢 Diğer haberler

▸ [Haber 1] — [tek cümle yorum]
▸ [Haber 2] — [tek cümle yorum]

Tweet 8: 📌 Günün Büyük Resmi

[Bugünün haberlerini birleştiren trend veya pattern]
[Öngörü: önümüzdeki günlerde nereye evrilir?]
```

### Örnek (Doldurulmuş)

```
Tweet 1: 🔴 KRİTİK: OpenAI GPT-5.5 Instant'ı duyurdu

GPT-5.5 Instant, GPT-5'in 2.8x hızlı, %40 daha ucuz versiyonu.
Ama asıl önemli olan: çıkarım mimarisi tamamen değişmiş.
İşte mühendis gözüyle analiz:

Tweet 2: Architecture farkı ne?

GPT-5'te MoE routing vardı, her token için 8 expert aktive oluyordu.
GPT-5.5'te bunu 4 expert'e düşürmüşler, ama routing latency'yi %60 azaltan
yeni bir quantization yaklaşımı eklemişler. Tradeoff: kalite düşüşü %2,
hız kazancı %180.

Tweet 3: Bu ne anlama geliyor?

Rakipler (Claude 4, Gemini) latency avantajını kaybediyor.
Özellikle real-time uygulamalar (voice, streaming) için GPT-5.5
yeni standart olabilir. Maliyet avantajı da eklenince,
enterprise adoption hızlanır.

Tweet 4: 🟠 YÜKSEK: Anthropic, Claude 4'ün fine-tuning API'sini açtı

İlk kez Claude 4 için özel fine-tuning mümkün.
Fiyat: base model'in 1.5x'i, minimum 1000 örnek.

Tweet 5: Fine-tuning detayı

Eğitim: 1000 örnek ~$500, çıkarım base model'den %40 pahalı.
Ama sonuçlar: SWE-bench fine-tuned versiyonda %67 (base %62).
Özellikle code generation ve domain-specific task'lerde etkili.

Tweet 6: 🟢 DeepSeek MoE architecture paper'ı yayınladı

DeepSeek-V4 teknik raporu: 128 expert, sadece 8'i aktif/token.
Training cost: Llama 4'ün %35'i, performans: MMLU'da eşit.

Tweet 7: 🟢 Diğer haberler

▸ HuggingFace: en çok indirilen model DeepSeek-V4 (Llama 4'ü geçti)
▸ Replicate: GPT-5.5 Instant desteği ekledi, latency testleri başladı
▸ LMSYS Arena: GPT-5.5 Instant liderliğe yerleşti (ELO 1423)

Tweet 8: 📌 Günün Büyük Resmi

Bugünün iki haberi aynı trendi gösteriyor: inference optimization.
GPT-5.5 hız odaklı, Claude 4 fine-tuning esneklik odaklı.
Önümüzdeki 3 ayda "hız + özelleştirme" rekabeti kızışacak.
```

---

## Template B: KRİTİK Haber Ağırlıklı

*Bükülük: 2 KRİTİK + 1 YÜKSEK (büyük bir gün)*

```
Tweet 1: 🔴 KRİTİK: [En büyük haber]

[Hook — neden bu haftanın en önemli gelişmesi?]
[Etki alanı: kimleri etkiler?]

Tweet 2-4: [Derin analiz (3 tweet)]
- Architecture/metrik detayı
- Sektörel etki + rakip karşılaştırması
- 6-12 aylık öngörü

Tweet 5: 🔴 KRİTİK: [İkinci büyük haber]

[Hook + teknik detay]

Tweet 6-7: [Analiz]
- Karşılaştırma
- Tradeoff + etki

Tweet 8: 🟠 YÜKSEK: [Üçüncü haber — daha kısa]

[Ne + neden önemli + 1 cümle yorum]

Tweet 9: 📌 Büyük Resim

[İki KRİTİK haberi birleştiren trend]
[Sektörün gidiş yönü]
```

---

## Template C: ORTA Ağırlıklı (Sakin Gün)

*Bükülük: 1 YÜKSEK + 3 ORTA (büyük haber yok)*

```
Tweet 1: 🟠 HAFTANIN EN ÖNEMLİSİ: [Haber]

[Hook — neden diğerlerinden ayrılıyor?]

Tweet 2-3: [Detay + yorum]

Tweet 4: 🟢 [İkinci haber — engineering blog]
[Thread değeri: ne öğreneceğiz?]

Tweet 5: [Teknik özet + çıkarım]

Tweet 6: 🟢 [Üçüncü haber — funding / duyuru]
[Kısa + yorum]

Tweet 7: 🟢 [Dördüncü haber]
[Çok kısa]

Tweet 8: 📌 Haftanın Trendi

[Bugünün haberlerinin gösterdiği yönelim]
```

---

## Template D: Haftalık AI Roundup (Pazartesi)

*Son 7 günün özeti, 10-12 tweet*

```
Tweet 1-2: Haftanın Özeti
📅 [Tarih aralığı] — AI dünyasında neler oldu?

Bu hafta [sayı] önemli gelişme var.
🔴 KRİTİK: [sayı]
🟠 YÜKSEK: [sayı]
🟢 ORTA: [sayı]
Hadi tek tek bakalım:

Tweet 3-5: 🔴 En Kritik 1-2 Gelişme
[Derin analiz]

Tweet 6-8: 🟠 Önemli Gelişmeler
[2-3 haber, her biri 1 tweet + yorum]

Tweet 9-10: 🟢 Kısa Haberler + Funding
[Hızlı geçiş, her biri 1-2 cümle]

Tweet 11: 📊 Haftalık Trend
[Bu haftanın verilerini birleştiren grafik/metrik]

Tweet 12: 📌 Gelecek Hafta
[Beklenen duyurular, öngörüler]
```

---

## Template E: Model Karşılaştırma (Aylık)

*Big 3 veya açık/kapalı kaynak karşılaştırması, 10-12 tweet*

```
Tweet 1: Model Savaşları — [Ay] karşılaştırması

OpenAI, Anthropic, Google (ve belki Meta/Mistral/DeepSeek):
Bu ay kim ne yaptı? Benchmark, fiyat, feature karşılaştırması:

Tweet 2-3: 🔴 OpenAI
[Son duyuru + benchmark + fiyat değişimi]

Tweet 4-5: 🟠 Anthropic
[Son duyuru + benchmark + fiyat]

Tweet 6-7: 🟠 Google DeepMind
[Son duyuru + benchmark]

Tweet 8: 🟢 Açık Kaynak
[Meta / Mistral / DeepSeek durumu]

Tweet 9-10: 📊 Karşılaştırma Tablosu

| Model | MMLU | SWE-bench | Fiyat | Hız |
|-------|------|-----------|-------|-----|
| GPT-5 | 91%  | 62%       | $15/M | 2.1s |
| Cld 4 | 90%  | 64%       | $20/M | 3.4s |

Tweet 11: 🏆 Bu Ayın Kazananı
[Kim önde? Hangi kategoride?]

Tweet 12: 📌 Trend
[Hangi yöne gidiyor? Fiyat düşüşü, hız artışı, vs.]
```

---

## ⚠️ Template Kullanım Kuralları

### Yapılması Gerekenler

- ✅ Template'i kılavuz olarak kullan, katı şablon olarak değil
- ✅ Haberin doğasına göre tweet sayısını ayarla (KRİTİK=uzun, ORTA=kısa)
- ✅ Her template'te mutlaka teknik metrik/veri olmalı
- ✅ Son tweette mutlaka "big picture" veya öngörü olmalı
- ✅ Kaynak linki en az 1 tweette belirtilmeli

### Yapılmaması Gerekenler

- ❌ Template'i doldurmak için anlamsız cümle yazma
- ❌ Zorlama bükülük (DÜŞÜK habere KRİTİK deme)
- ❌ Template'in dışına çıkma korkusuyla doğal akışı bozma
- ❌ Her gün aynı template'i kullanma (çeşitlendir)

---

## ✅ Template Performans Takibi

Her template'in performansı aylık değerlendirilir:

| Template | Kullanım Sayısı | Ort. Impression | Ort. Bookmark | Ne Zaman Kullanılır |
|----------|----------------|-----------------|---------------|---------------------|
| **A (Klasik)** | — | — | — | Varsayılan, her gün |
| **B (KRİTİK)** | — | — | — | Büyük haber günleri |
| **C (Sakin)** | — | — | — | Hafta sonu / sakin gün |
| **D (Haftalık)** | — | — | — | Pazartesi |
| **E (Karşılaştırma)** | — | — | — | Ayda 1 |
