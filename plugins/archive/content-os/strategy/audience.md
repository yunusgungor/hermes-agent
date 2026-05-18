# Audience

> **Tek kişi.** Segment değil.
> Her içerik bu tek kişinin problemine cevap vermeli,
> yoksa yazılmamalı.

---

## 👤 Birincil Persona: "Arda"

### Demografi

| Özellik | Değer |
|---------|-------|
| **Yaş** | 25-28 |
| **Ünvan** | Backend Developer → AI Systems Architect (geçiş yapmak istiyor) |
| **Deneyim** | 3-6 yıl backend (Python/Go/Node.js) |
| **Şirket** | Ölçeklenen startup veya büyük şirketin AI ekibi |
| **Lokasyon** | Türkiye (İstanbul/Ankara/İzmir) veya remote yurtdışı |
| **Eğitim** | CS veya EE mühendislik (lisans) |
| **Gelir** | $40K-$80K/yıl (Türkiye) veya $100K+ (remote) |

### Günlük Rutin

```
09:00 — İşe başla, stand-up, PR review
10:00 — Feature geliştirme (backend API, veritabanı, servis)
12:00 — Öğle arası + Twitter'da gezinme (içeriklerimi burada görür)
13:00 — Feature devam / bug fix
15:00 — Toplantı (AI feature planning / architecture review)
17:00 — Deep work / code review
19:00 — Çıkış, Twitter'da takip
20:00-23:00 — Kişisel projeler, AI araştırma, learning
```

**Twitter'da ne zaman benim içeriklerimi görür?**
- Sabah kahve (09:00-09:15) — hızlı tarama
- Öğle arası (12:00-12:30) — thread okuma
- Akşam üstü (17:00-17:30) — derin okuma
- Gece (22:00-23:00) — bookmark + kaydetme

### Teknik Yetenek Seti

| Alan | Seviye | Açıklama |
|------|--------|----------|
| **Backend (Python/Go)** | 🟢 İleri | API, veritabanı, servis mimarisi |
| **AI/ML** | 🟡 Orta | LLM kullanımı, prompt engineering, API entegrasyonu |
| **Cloud (AWS/GCP)** | 🟡 Orta | Deployment, scaling, container |
| **Sistem Tasarımı** | 🟠 Başlangıç | Monolith → microservice geçişi yapmış |
| **Event-Driven Arch** | 🔴 Düşük | Queue kullanmış ama pattern'leri bilmiyor |
| **Agent Systems** | 🔴 Düşük | LangChain kullanmış, orchestrator vs worker farkını tam bilmiyor |
| **Distributed Systems** | 🟠 Başlangıç | Temel CAP theorem, consistency modelleri |
| **AI Infrastructure** | 🔴 Düşük | Model serving, inference optimization bilmiyor |

### Yaşadığı Problemler (Pillar Bazlı)

#### Pillar 1 — AI Systems Architecture
- LLM'i API'den çağırmak dışında ne yapacağını bilmiyor
- "AI sistemi" ile "AI uygulaması" arasındaki farkı kavrayamamış
- ORM/Repository pattern gibi backend pattern'lerini AI'a uyarlamaya çalışıyor (yanlış abstraction)
- Agent lifecycle yönetimini hiç düşünmemiş

#### Pillar 2 — Multi-Agent & Autonomous Systems
- LangGraph ile agent chain yapmış ama bunun orchestrator-worker pattern olmadığını bilmiyor
- Agent'lar arası iletişimi REST çağrısıyla yapmaya çalışıyor
- Memory management'ı her agent'a ayrı ayrı koyuyor (paylaşılmıyor)
- Failover/retry stratejisi yok, agent crash'lerinde kayboluyor

#### Pillar 3 — Production-Grade Infrastructure
- Model'ı FastAPI ile serve ediyor, production scaling'i hiç düşünmemiş
- Event-driven architecture'ı Kafka ile başlatıp vazgeçmiş (overwhelmed)
- Observability sadece console.log (OpenTelemetry nedir bilmiyor)
- Circuit breaker, bulkhead, rate limiter pattern'lerini hiç uygulamamış

#### Pillar 4 — Cognitive Engineering
- "Memory" denince aklına sadece vector DB geliyor
- Reasoning pipeline nedir bilmiyor (Chain-of-Thought'tan öteye geçememiş)
- Knowledge graph ile vector search arasında seçim yapamıyor
- World model kavramını hiç duymamış

#### Pillar 5 — AI-Native Product Engineering
- "AI feature" eklenmiş ürün yapıyor, AI-native değil
- UX'te AI feedback'in nasıl sunulacağını bilmiyor
- Human-in-the-loop nerede olmalı, nerede olmamalı — hiç düşünmemiş
- AI product metriklerini (user trust, latency tolerance, hallucination cost) bilmiyor

#### Pillar 6 — Tech News
- Haberleri Hacker News, Reddit, Medium'da takip ediyor ama kayboluyor
- Bir duyurunun industry impact'ini değerlendiremiyor
- Trendleri görüyor ama nereye gittiğini anlamıyor
- Günlük 2 saatini haber okuyarak geçiriyor, verim alamıyor

### Neden Beni Takip Ediyor?

> *"İnternetin çoğu tool anlatıyor, bu adam system architecture anlatıyor."*

**Spesifik nedenler:**
1. **Sistem seviyesi düşünce** — Abstraction'ı yükseltiyorum, kod snippet'inden öte mimari anlatıyorum
2. **Gerçek production dersleri** — Demo projelerden değil, gerçek sistemlerden bahsediyorum
3. **Tradeoff'ları gösteriyorum** — "En iyi yaklaşım" değil, "ne zaman ne kullanılır" anlatıyorum
4. **Haberleri süzüyorum** — 2 saatlik okuma süresini 5 dakikaya indiriyorum
5. **Teknik yoğunluk** — Marketing dili değil, mühendis dili kullanıyorum

### Neden Bookmark Atar?

**Bookmark atma kriterleri (öncelik sırasına göre):**

| # | Kriter | Örnek |
|---|--------|-------|
| 1 | **Reusable pattern** | "Bu orchestration modelini kendi sistemimde kullanabilirim" |
| 2 | **Architecture diagram** | "Şu topology'yi referans alabilirim" |
| 3 | **Production lesson** | "Bu hatayı ben de yapabilirdim" |
| 4 | **Benchmark/data** | "Şu metrik karşılaştırmasını sunumda kullanabilirim" |
| 5 | **Tradeoff analizi** | "X vs Y kararını documentation'da referans gösterebilirim" |
| 6 | **Teknik haber yorumu** | "Bu haberdeki mimari detayı başka yerde görmedim" |

### Neden Retweet / Mention Yapar?

- **Kendi ekibine göndermek için** — "Ekip arkadaşım bunu okumalı"
- **Kararını desteklemek için** — "Bu thread'deki argümanı CTO'ya gösterdim"
- **İtiraz etmek için** — "Bu noktada farklı düşünüyorum ama katkı değerli"
- **Kendi işine referans için** — "Biz de benzer bir sistemi şöyle kurduk..."

### Reader Psychology (Derinlemesine)

**Okuma alışkanlıkları:**
- Önce hook'u okur, 2. tweet'e geçmeden önce değer görürse devam eder
- Tweet'te metrik/veri varsa daha çok okur
- Architecture diagram varsa %80 daha fazla kalma süresi
- Türkçe + İngilizce teknik terim karışımı tercih eder
- Paragraf yerine madde işareti/liste formatını daha hızlı tüketir

**Nefret ettiği içerik türleri:**
- "Motivational" AI content
- Clickbait haber başlıkları
- "X şirketi Y'yi duyurdu" — yorumsuz link paylaşımı
- Yüzeysel tutorial (Keras ile 5 satırda MNIST)
- Kişisel gelişim kılıfında AI content
- Aşırı basitleştirilmiş teknik içerik ("ELI5" formatı)

**Güvendiği kaynak işaretleri:**
- Açık kaynak referans (GitHub repo linki)
- Production deployment deneyimi ("biz şu sistemi kurarken...")
- Spesifik metrik/benchmark
- Bilinen bir architecture pattern'e atıf
- Kendi yaşadığı hatayı anlatması

---

## 👤 İkincil Persona: "Cem"

### Demografi

| Özellik | Değer |
|---------|-------|
| **Yaş** | 30-40 |
| **Ünvan** | CTO / Tech Lead / AI Team Lead |
| **Deneyim** | 10+ yıl yazılım, 2-3 yıl AI lead |
| **Şirket** | AI odaklı startup veya kurumsal AI dönüşüm ekibi |
| **Problem** | AI sistem mimarisi kararları vermek zorunda, ama kendisi backend kökenli |

**Neden takip eder?**
- Ekibi için karar verirken referans arıyor
- Trendleri takip etmesi gerekiyor ama derin okumaya vakti yok
- Ekip arkadaşına yönlendirmek için bookmark'lıyor
- LinkedIn'de paylaşmak için kaliteli içerik arıyor

**Farkı:** Arda'dan daha az teknik detay, daha çok stratejik yorum bekler. Haber thread'lerinde "bu ne anlama geliyor?" kısmı onun için kritik.

---

## 👻 Anti-Persona (Bu İçerik KİMİN İçin Değil)

| Tip | Neden Uymaz |
|-----|-------------|
| **Junior developer** (<2 yıl) | Teknik yoğunluk çok yüksek, sistem deneyimi yok |
| **AI researcher (PhD)** | Yeterince teorik/matematiksel değil |
| **Product manager / non-tech** | Çok teknik, jargon yoğun |
| **Data scientist** | Model training/evaluation odaklı değil, system architecture odaklı |
| **Hobbyist / "vibe coder"** | Ciddi teknik içerik, hobi seviyesinde değil |
| **HR / recruiter** | Hiçbir ilgisi yok |
| **Student (lisans)** | Deneyim seviyesi tutmaz |

---

## 🧭 Reader Journey

Bir takipçinin geçirdiği aşamalar:

### Aşama 1: Keşif
**Nasıl bulur?**
- RT/mention yoluyla
- Haber thread'i keşfedilir
- LinkedIn'de paylaşım
- X algoritması (AI news thread)

**Ne görür?** Günlük AI news thread (8 tweet, bükülük sıralı)
**Karar:** Hook değerli mi? → Takip et veya geç

### Aşama 2: Test
**Ne yapar?** 2-3 gün boyunca thread'leri okur
**Test kriterleri:**
- Her gün düzenli içerik var mı?
- Teknik derinlik tutarlı mı?
- Haber seçimi isabetli mi?
- Yorum katma değer sağlıyor mu?

**Karar:** Kaliteli bulursa → bildirimleri açar, Bookmark klasörüne ekler

### Aşama 3: Güven
**Ne yapar?** Orijinal içerikleri de okumaya başlar
**Ne bekler?**
- Architecture pattern'leri
- Production dersleri
- Derin teknik analiz

**Karar:** Güven oluşursa → mention, RT, ekip arkadaşına yönlendirme

### Aşama 4: Savunuculuk
**Ne yapar?**
- Ekip toplantısında referans gösterir
- LinkedIn'de paylaşır
- Blog yazısını ekibine okuma listesi olarak verir
- Konferans konuşmasında referans alır

**Nasıl ölçülür?** Mention sayısı, yorum kalitesi, DM gelen sorular

---

## 📊 Audience Metrics (Takip Edilecek)

| Metrik | Hedef | Nasıl Ölçülür |
|--------|-------|--------------|
| **Engagement rate** | >%5 | Tweet impressions / interactions |
| **Bookmark rate** | >%10 | Bookmark sayısı / impression |
| **Yeni takipçi/gün** | >20/gün | X analytics |
| **DM gelen soru/hafta** | >5 | DM kutusu |
| **Mention/hafta** | >10 | X analytics |
| **Retweet/hafta** | >15 | X analytics |
| **Reader retention** (thread sonuna kadar) | >%40 | X analytics (impression drop-off) |

---

## 📋 Audience Doğrulama Checklist

Her içerik öncesi sorulacak sorular:

- [ ] Bu içerik Arda'nın hangi problemini çözüyor?
- [ ] Bu içerik olmasaydı Arda ne kaybederdi?
- [ ] Arda bu içeriği bookmark'lar mı? Neden?
- [ ] Arda bu içeriği ekibine gönderir mi?
- [ ] Bu içerik Cem'in karar vermesine yardımcı olur mu?
- [ ] Anti-persona'lardan biri bu içeriği anlar mı? (Anlarsa çok basit)
- [ ] Bu içeriği sadece ben mi yazabilirim? (Başkası yazarsa farkım ne?)
