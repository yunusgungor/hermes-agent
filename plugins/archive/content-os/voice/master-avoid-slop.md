# Master Avoid-Slop — Komple Pattern Kataloğu

> **Versiyon:** v2.4.0
> **Kaynak:** `content_os_core.py` regex listeleri + postmortem çıktıları
> **Temel:** Shann³ (@shannholmberg) — 100K+ bookmark pattern analizi
> **Güncelleme:** Her postmortem'den sonra yeni pattern'ler eklenir

---

## 📊 Pattern Özeti

| Tier | Adet | REVISE Eşiği | REJECT Eşiği |
|------|------|--------------|--------------|
| 🔴 Tier 1 — Kritik | 32 | ≥1 pattern | ≥3 pattern |
| 🟡 Tier 2 — Yüksek | 32 | ≥3 pattern | ≥5 pattern |
| 🟢 Tier 3 — Orta | 33 | ≥8 pattern | ≥15 pattern |
| ⚪ Bonus — Ton | 9 | Kontekst bazlı | — |
| 🇹🇷 Türkçe | 20 | ≥3 pattern | ≥5 pattern |

---

## 🔴 TIER 1 — KRİTİK (Sıfır Tolerans)

> *Eşik: ≥1 pattern → REVISE | ≥3 pattern → REJECT*
> *Bu pattern'lerden biri bile varsa içerik zayıflar. İkincisi varsa yeniden yazılmalıdır.*

| # | Kalıp | Trigger (Regex/Kelime) | Çözüm | Örnek |
|---|-------|----------------------|-------|-------|
| 1 | **Promosyon Dili** | `groundbreaking`, `game-changing`, `revolutionary`, `transformative`, `paradigm-shifting` | Sil. Somut teknik açıklama ile değiştir | ✗ "Devrim niteliğinde yeni model" → ✓ "SWE-bench'te %62 → %71 getiren yeni architecture" |
| 2 | **Önem Atfetme Abartısı** | `pivotal moment`, `testament to`, `a testament to`, `significant step`, `quantum leap` | Neden önemli olduğunu veriyle göster | ✗ "Bu bir dönüm noktası" → ✓ "İlk kez bir model X benchmark'ta insan seviyesini geçti" |
| 3 | **Belirsiz Atıf** | `experts believe`, `studies show`, `research suggests`, `data shows`, `it turns out that` | Kaynak göster veya kendi deneyimine dayandır | ✗ "Araştırmalar gösteriyor ki" → ✓ "Google'ın yayınladığı çalışmada (2026)" |
| 4 | **Sahte Etkinlik** | `the system compounds`, `the data tells us`, `compound interest of`, `the power of` | Gerçek metrik veya flow ile değiştir | ✗ "Sistemin gücü katlanarak artıyor" → ✓ "Her yeni agent eklediğinde throughput linear değil, loglinear artıyor" |
| 5 | **Retorik Kurulum** | `the question is whether`, `at its core`, `what if i told you` | Doğrudan anlatmaya başla | ✗ "What if I told you that..." → ✓ "Multi-agent sistemlerde coordination en büyük bottleneck" |
| 6 | **Staccato Parçalama** | `no X. no Y. no Z.` veya 4+ kısa cümle art arda | Akışı birleştir, tek cümlede anlat | ✗ "No central server. No coordinator. No single point of failure." → ✓ "Flat topology'de merkezi orchestrator yok — agent'lar doğrudan iletişim kurar" |
| 7 | **Em Dash Aşırı Kullanımı** | `--` (1-2'den fazla em dash) | Noktalı virgül veya yeni cümle kullan | ✗ "Agent — yani bağımsız çalışan birim — orchestrator — yani koordinatör — ile iletişim kurar" → ✓ "Agent (bağımsız çalışan birim) orchestrator (koordinatör) ile iletişim kurar" |
| 8 | **Dolgu Zarfları (English)** | `actually`, `literally`, `quietly`, `simply`, `just`, `basically` | Sil. Gereksiz güçlendiriciler | ✗ "It's basically just a simple orchestrator" → ✓ "Orchestrator, task decomposition ve result aggregation yapar" |

---

## 🟡 TIER 2 — YÜKSEK (Dikkatle İzlenir)

> *Eşik: ≥3 pattern → REVISE | ≥5 pattern → REJECT*

| # | Kalıp | Trigger | Çözüm | Örnek |
|---|-------|---------|-------|-------|
| 9 | **Copula Avoidance** | `serves as`, `stands as`, `features`, `encompasses`, `utilizes` | Basit fiil kullan: "is", "has", "uses" | ✗ "System utilizes agent-based architecture" → ✓ "System uses agent-based architecture" |
| 10 | **-ing Padding** | `leveraging`, `implementing`, `optimizing`, `enabling` | "-ing" yerine basit present tense | ✗ "By leveraging event-driven architecture..." → ✓ "Event-driven architecture ile..." |
| 11 | **Rule of Three Zorlama** | `three things`, `three reasons`, `three ways`, `triad` | Yapay değilse bırak, değilse yeniden yapılandır | ✗ "3 nedenden dolayı..." (zorlama) → ✓ Doğal sayıda madde |
| 12 | **Filler Phrases** | `in order to`, `due to the fact that`, `at this point in time`, `in today's world` | Kısalt: "to", "because", "now" | ✗ "Due to the fact that latency is high" → ✓ "Because latency is high" |
| 13 | **Generic Conclusions** | `the future looks bright`, `exciting times ahead`, `the best is yet to come` | Somut çıkarım veya pattern ile bitir | ✗ "Exciting times ahead for AI" → ✓ "Önümüzdeki 6 ayda agent systems'te 3 trend bekliyorum: ..." |
| 14 | **Signposting** | `let's dive in`, `here's what you need to know`, `tldr`, `in conclusion` | Okuyucuyu uyarma, doğrudan anlat | ✗ "Let's dive in!" → ✓ Doğrudan konuya gir |
| 15 | **Hyperbolic Quantifiers** | `every single`, `all the time`, `never ever`, `absolutely everyone` | Gerçekçi ifade kullan: "çoğu", "genellikle" | ✗ "Every single AI system needs this" → ✓ "Çoğu production AI sistemi bu pattern'i kullanır" |
| 16 | **Hedging** | `it could potentially`, `it might be argued`, `somewhat`, `arguably` | Kesin konuş veya veriye dayandır | ✗ "It could potentially improve latency" → ✓ "Latency'i %30 iyileştirir (test sonucu)" |

---

## 🟢 TIER 3 — ORTA (Bağlamda Değerlendirilir)

> *Eşik: ≥8 pattern → REVISE | ≥15 pattern → REJECT*

| # | Kalıp | Trigger | Çözüm | Örnek |
|---|-------|---------|-------|-------|
| 17 | **Passive Voice** | `was/were/been/being + *ed` | Active voice kullan | ✗ "The system was designed by..." → ✓ "Biz sistemi şu prensiplerle tasarladık..." |
| 18 | **Elegant Variation** | `also known as`, synonym chains (3+ farklı isim) | Aynı kavramı hep aynı adla an | ✗ "The orchestrator... the coordinator... the central unit..." → ✓ Hep "orchestrator" |
| 19 | **False Ranges** | `from basic to advanced`, `from beginner to expert` | Gerçekçi hedef kitle belirt | ✗ "Her seviyeye uygun" → ✓ "Backend bilen, AI systems architect olmak isteyenler için" |
| 20 | **Conjunction Overuse** | Cümle başı `And` veya `But` (arka arkaya) | Bağlaçsız yeni cümle kur | ✗ "And then... But also... And finally..." → ✓ Doğrudan anlat |
| 21 | **Unnecessary Intensifiers** | `very`, `so`, `such` | Sil veya somutla değiştir | ✗ "Very high latency" → ✓ "2.4s latency" |
| 22 | **Paragraph-Level Vagueness** | `it is important to note that`, `it should be noted that` | Doğrudan söyle | ✗ "It should be noted that latency matters" → ✓ "Latency, kullanıcı deneyimini doğrudan etkiler" |
| 23 | **Rhetorical Questions** | `have you ever wondered`, `can you imagine`, `what would you do if` | Direkt ifade et, soru kullanma | ✗ "Have you ever wondered why AI is slow?" → ✓ "AI latency'nin 3 ana kaynağı: inference, network, serialization" |
| 24 | **Awkward List Introductions** | `there are X things`, `X is/are ...` (liste öncesi) | Listeyi doğrudan ver | ✗ "There are 3 types of memory..." → ✓ "3 memory türü: episodic, semantic, procedural" |
| 25 | **False Precision** | `exactly X.Y%` (gereksiz ondalık) | Yuvarla | ✗ "Exactly 23.47% improvement" → ✓ "~%23 improvement" |
| 26 | **Clichéd Metaphors** | `level up`, `dive deep`, `game plan`, `road map` | Özgün teknik ifade kullan | ✗ "Let's level up your AI architecture" → ✓ "Orchestration topology'ni supervisor'dan flat'e geçir" |
| 27 | **Self-Referential Humility** | `i may be wrong`, `i could be wrong` | Çıkar veya veriyle destekle | ✗ "I could be wrong but..." → ✓ "Benim deneyimimde şu pattern işe yaradı: ..." |
| 28 | **Empty Emphasis** | `[PARANTEZ İÇİ]` veya `UPPERCASE` vurgu | Normal yaz, vurguyu içerikle yap | ✗ "This is REALLY important" → ✓ "Bu, sistemin en kritik bileşeni: ..." |
| 29 | **Temporal Vagueness** | `recently`, `lately`, `these days` | Tarih ver | ✗ "Recently OpenAI released..." → ✓ "16 Mayıs 2026'da OpenAI..." |
| 30 | **False Balance** | `some say X while others say Y` | Kendi pozisyonunu al | ✗ "Some say supervisor topology is better, others say flat" → ✓ "Supervisor topology consistency gerektiğinde, flat topology hız gerektiğinde" |
| 31 | **Unearned Authority** | `as someone who`, `having worked in` | Deneyimini göster ama gereksiz tanıtma yapma | ✗ "As someone who has worked in AI for 5 years..." → ✓ "Production AI sistemi kurarken şu hatayı yaptım: ..." |
| 32 | **Hedging Through Specificity** | `exactly X.Y` (anlamsız ondalık) | Anlamlı yuvarlama | ✗ "3.14159% improvement" → ✓ "~%3 improvement" |
| 33 | **Template Language** | `in this post, we... [explore/dive/cover/discuss]` | Doğrudan konuya gir | ✗ "In this thread, we'll explore..." → ✓ "Supervisor topology'de 3 problem var: ..." |
| 34 | **Unnecessary Qualification** | `the very real possibility`, `the very real chance` | "Possibility" veya "chance" yeterli | ✗ "There's a very real possibility that..." → ✓ "Bu senaryoda X olma ihtimali yüksek" |

---

## ⚪ BONUS — TON (Kontekst Bazlı)

| # | Kalıp | Trigger | Çözüm | Örnek |
|---|-------|---------|-------|-------|
| 35 | **Faux Authority** | `you should`, `you must`, `never do this` | "Bence", "Tavsiyem" gibi yumuşak ifade | ✗ "Never use synchronous calls" → ✓ "Synchronous call'lar şu durumda bottleneck yaratır: ... Alternatif: ..." |
| 36 | **Vibes Over Data** | `it feels like`, `seems to me` | Veri veya deneyimle destekle | ✗ "It feels like agent systems are overhyped" → ✓ "Agent systems'te bookmark/impression oranı düşük (kaynak: X analytics)" |
| 37 | **Thread-Bait Hooks** | `here's the thing`, `the secret` | Gerçek problemle aç | ✗ "Here's the secret to building better AI systems" → ✓ "Multi-agent sistemlerde en sık yapılan hata: orchestration topology'yi yanlış seçmek" |
| 38 | **Oversharing Backstory** | `X years ago, I/we/my/our...` (3+ paragraf) | Kısa tut, doğrudan konuya gir | ✗ "5 yıl önce bir startup'ta çalışırken..." (3 paragraf arkaplan) → ✓ "Production'da şu hatayı yaptık: ..." (1 cümle arkaplan) |
| 39 | **Under-Explaining Proof** | `result: %...` (metodoloji yok) | Nasıl ölçtüğünü de anlat | ✗ "Result: 40% improvement" → ✓ "A/B testte 1000 istek üzerinden ölçtük: supervisor mode'da ortalama 240ms, flat mode'da 140ms (%42 iyileşme)" |
| 40 | **Pseudo-Technical** | Anlamsız jargon kullanımı | Her terimi açıkla veya çıkar | ✗ "We implemented a holistic paradigm-agnostic cognitive framework" → ✓ "Event-driven architecture ile agent'lar arası iletişimi async hale getirdik" |

---

## 🇹🇷 TIER T1 — TÜRKÇE ÖZEL PATTERN'LER

> *Türkçe içeriklerde kaçınılması gereken kalıplar*
> *Eşik: ≥3 pattern → REVISE | ≥5 pattern → REJECT*

| # | Kalıp | Trigger | Çözüm | Örnek |
|---|-------|---------|-------|-------|
| T1 | **Dolgu Zarfları (Türkçe)** | `aslında`, `sırf`, `sadece`, `bence`, `yani`, `işte` | Sil. Gereksiz dolgu | ✗ "Aslında bu aslında çok basit bir sistem" → ✓ "Bu sistem 3 component'ten oluşuyor" |
| T2 | **Abartılı Sıfatlar** | `müthiş`, `harika`, `olağanüstü`, `inanılmaz`, `nefis` | Somut veriyle değiştir | ✗ "Müthiş bir gelişme!" → ✓ "Benchmark'ta %20 iyileşme sağlayan bir gelişme" |
| T3 | **Belirsiz Övgü** | `çok başarılı`, `gerçekten iyi`, `oldukça etkileyici` | Neyin başarılı olduğunu söyle | ✗ "Çok başarılı bir model" → ✓ "Özellikle code generation'da başarılı (HumanEval %92)" |
| T4 | **Soru Kipinde Yargı** | `Acaba?`, `Peki ya?`, `Öyle mi?` (tweet sonu) | Yargıyı direkt ver | ✗ "Peki bu yeterli mi?" → ✓ "Bu latency seviyesi real-time uygulamalar için yeterli değil" |
| T5 | **"Günümüzde" Açılışı** | `Günümüzde`, `Bugünün dünyasında` | Doğrudan konuya gir | ✗ "Günümüzde AI sistemleri..." → ✓ "Multi-agent sistemlerde coordination en büyük bottleneck" |
| T6 | **Anlamsız İngilizce Karıştırma** | İngilizce kelimeyi Türkçe cümle içinde gereksiz kullanma | Tutarlı dil kullan | ✗ "Bu workflow'u deploy etmek için..." (gereksiz İngilizce) → ✓ "Bu iş akışını dağıtmak için..." veya "Bu workflow'u deploy etmek için..." (tutarlı) |
| T7 | **"Yani" ile Açıklama** | `Yani kısacası`, `Yani demek oluyor ki` | Direkt anlat, özet cümlesi kurma | ✗ "Yani kısacası, supervisor daha yavaş ama daha tutarlı" (zaten anlaşıldıysa) → ✓ İlk cümlede doğru anlat |
| T8 | **Duygusal Tepki** | `Vay be!`, `Amanın!`, `Yok artık!` | Duygusal değil, teknik tepki | ✗ "Vay be, 2M context!" → ✓ "2M context'in anlamı: aynı anda 3 romanı işleyebilir" |
| T9 | **Clickbait Türkçe** | `Bunu duydunuz mu?`, `Kaçırdınız mı?`, `Görmediniz değil mi?` | Değer odaklı başlık | ✗ "Bunu duydunuz mu? OpenAI yeni model çıkardı!" → ✓ "OpenAI yeni modeli [X] ile context window'u 2M'e çıkardı" |
| T10 | **Gereksiz Soru Formatı** | `Neden mi?`, `Sebebi ne?` (kendi sorduğun soruyu kendin cevaplamak için) | Direkt anlat | ✗ "Neden mi önemli? Çünkü..." → ✓ "Önemli çünkü..." |

---

## 🛠️ SLOP TESPİT VE DÜZELTME STRATEJİSİ

### Ne Zaman Ne Yapılmalı

| Slop Durumu | Aksiyon |
|-------------|---------|
| **0 pattern** | ✅ PASS — Yayına hazır |
| **1-2 Tier 1** | 🔄 REVISE — İlgili pattern'leri düzelt |
| **3+ Tier 1** | ❌ REJECT — Yeniden yaz |
| **3-4 Tier 2** | 🔄 REVISE — Düzelt veya yeniden yapılandır |
| **5+ Tier 2** | ❌ REJECT — Yeniden yaz |
| **8-14 Tier 3** | 🔄 REVISE — Toplu düzeltme |
| **15+ Tier 3** | ❌ REJECT — Yeniden yaz |
| **Türkçe 3+** | 🔄 REVISE — Dolgu ve abartıları temizle |
| **Türkçe 5+** | ❌ REJECT — Yeniden yaz |

### Düzeltme Önceliği

```
1. Tier 1 pattern'ler (en kritik, hemen düzelt)
2. Türkçe pattern'ler (yerel dil hataları)
3. Tier 2 pattern'ler (yüksek etki)
4. Bonus ton pattern'leri (kontekst bazlı)
5. Tier 3 pattern'ler (toplu düzeltme)
```

### Hızlı Düzeltme Kontrol Listesi

Her slop taramasından sonra:

- [ ] Tier 1 count = 0 mı? (Sıfır toleranslı)
- [ ] Türkçe dolgu zarfları temizlendi mi?
- [ ] Hype kelimeleri varsa çıkarıldı mı?
- [ ] Passive voice'lar active'e çevrildi mi?
- [ ] Belirsiz atıflar kaynaklandı mı?
- [ ] Her tweet tek bir fikir taşıyor mu?

---

## 📋 QUICK REFERENCE — Günlük Kullanım Kartı

*Yayın öncesi hızlı göz atmak için:*

### En Sık Görülen 10 Slop (Öncelikli)

| # | Pattern | Neden Sık Görülür | Fix |
|---|---------|-------------------|-----|
| 1 | "aslında", "sırf", "sadece" | Türkçe dolgu, LLM çıktısında sık | Elle temizle |
| 2 | "Let's dive in" / "Here's the thing" | LLM signature pattern | Sil, doğrudan başla |
| 3 | Belirsiz atıf ("studies show") | LLM boşluk doldurması | Kaynak ekle veya çıkar |
| 4 | Em dash aşırı kullanımı | LLM'in doğal akışı | Noktalı virgül kullan |
| 5 | -ing padding ("leveraging") | LLM tercihi | Basit fiil kullan |
| 6 | Generic conclusion | LLM kapanış tercihi | Somut çıkarım ekle |
| 7 | Hype words ("revolutionary") | LLM abartma eğilimi | Metrikle değiştir |
| 8 | Passive voice | Akademik LLM eğitimi | Active voice |
| 9 | Staccato cümleler | LLM vurgu yapma çabası | Birleştir |
| 10 | "Günümüzde" açılışı | Türkçe LLM tercihi | Kes açılışı |

---

## 📚 KAYNAK

- **content_os_core.py** — `FULL_SLOP_TIER1`, `FULL_SLOP_TIER2`, `FULL_SLOP_TIER3`, `FULL_SLOP_BONUS` listeleri (ana kaynak)
- **voice-profile.md** — Kişisel yasaklı kalıplar (bu dosyadaki genel pattern'lerden farklı olabilir)
- **Postmortem analizleri** — stores/feedback/ altındaki her postmortem yeni pattern eklenmesine yol açabilir
