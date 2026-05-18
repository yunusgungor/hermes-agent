# Writer Context Packet — flux-v1-0-ci-cd-pipeline
## Meta
- **Route:** ORIGINAL
- **Format:** Thread (12 tweets)
- **Pillar:** CI/CD & Release Automation
- **Target Date:** (not specified)

## Thesis
Flux v1.0 release sürecinde kurduğum CI/CD pipeline’ının anatomisi — neden her bileşeni seçtiğim, hangi tradeoff’ları yaptığım ve diğer Rust geliştiricilerinin bu yapıyı kendi projelerine nasıl uyarlayabileceği.

## Target Reader
Açık kaynak Rust kütüphanesi yazan, ilk major release’ini otomatize etmek isteyen bir geliştirici. crates.io publish, GitHub Release ve Docker Hub push sürecini hata yapmadan, tekrarlanabilir şekilde kurmak istiyor. En büyük endişesi: yanlış version etiketi veya secret sızdırma.

## Angle (Unexpected Framing)
Standart “GitHub Actions ile crate publish” tutorial’ı değil. Flux v1.0’ın gerçek çıkış sürecinde karşılaştığım problemlerle şekillenen bir pipeline hikâyesi. Sadece akış değil, her aşamadaki alternatiflerin neden elendiği, hangi kararın hangi sorunu çözdüğü anlatılacak. Hook olarak infra-hook pattern’i kullanılacak: bir production failure (örneğin unutulan version bump) ile açılıp pipeline’ın bu hatayı nasıl önlediği gösterilecek.

## Proof Elements
- **Metrics:** (kişisel deneyim, sayısal veri varsa kullanılır) Build → test → publish → Docker push cycle time (tahmin: ~15 dk). Otomatikleştirme öncesi manuel yayın süresi vs. sonrası.
- **Stories:** crates.io API key rotasyonu sırasında yaşanan hata, tag bazlı tetikleme ile çözülen version yönetimi.
- **Projects:** Flux v1.0 — Rust binary library + Docker image.
- **Tools:** GitHub Actions, Cargo, crates.io, Docker Hub, GitHub Releases.

## Constraints
- **Format rules:** Thread. Her tweet kendi içinde anlamlı, son tweet referans ve “next” bağlantısı. Chain yapısına dikkat.
- **Length:** 12 – 15 tweet, toplam ~2500 – 3000 karakter.
- **Language:** Türkçe, teknik terimler (e.g. “workflow”, “pipeline”, “semver”) İngilizce.
- **Tone:** Analitik, samimi, ikinci tekil şahıs (“diyelim ki”, “görürsün”). Öğretici değil, hikâye anlatıcı.
- **Banned phrases:** “hiç sorun yaşamadım”, “mükemmel çalışıyor”, “aslında çok kolay”, “yapmanız gereken tek şey”, “harika”, “sorunsuz”. (Tier 1 slop pattern’leri)  
- **Visual requirements:** En az bir adet GitHub Actions YAML snippet (markdown code block, language: yaml). Opsiyonel: crates.io release sayfası veya Docker Hub tags ekran görüntüsü.
- **Structure (Voice Profile):** Thread sırası: (1) Component — pipeline hangi parçalardan oluşuyor. (2) Flow — veri/kontrol nasıl akıyor. (3) Dependency — hangi bilgiye bağlı, dışarıda neyi tetikler. (4) Tradeoff — neden bu şekilde, alternatifler. (5) Lifecycle — release nasıl doğar, hata durumunda nasıl rollback yapılır.

## Voice Anchors
1. “Flux’ın CI/CD pipeline’ı üç ana component’ten oluşuyor: tag trigger’ı, build matrix’i (üç farklı OS/arch) ve publish aksiyonu.”
2. “En sevmediğim tradeoff: semver bump’ı elle yapmak. Otomasyona bırakırsan yanlış etiket basma riskin var, ama elle unutmanın maliyeti daha büyük.”
3. “Dependency listesi kısa: Cargo.toml, GitHub Secrets ve Docker Hub token’ı. Ama bu pipeline bir crate’i publish ederken aynı anda Docker image’ini de itiyor — aralarındaki version uyumunu sağlamak en büyük kafa karıştırıcı.”

## Risks (Slop / Cringe Traps)
- Adım adım talimat verip “neden”leri atlamak (AI yazdığı belli olur).
- “Problemsiz çalışıyor” gibi genellemeler yapmak. Gerçek sorunları ve çözümleri anlatmak yerine her şeyi pembe göstermek.
- Sadece popüler pattern’leri kopyalayıp kişisel kararlardan bahsetmemek.
- Secret yönetimi, error handling gibi kritik ama sıkıcı detayları es geçmek.
- Hedef kitleyi Rust bilmeyenler de varmış gibi fazla açıklamak (Rust özelinde kalınacak).

## Open Loops
- Pipeline’ın üretimdeki gerçek cycle time sayıları (writer elinde yoksa belirtmemeli, sadece “ortalama 15 dakika” gibi tahmin kullanmamalı).
- Docker image tag stratejisi (semver, latest, commit hash) — yazar hangisini seçti? Çatışma varsa fix’i ne?
- Pipeline’a eklenme planı olan security scanning ya da changelog generation var mı? (belki “şimdilik yok, ama sonra eklenebilir” denebilir)
- Kullanıcının farklı crate tipi (binary vs lib) olabilir — yazı sadece binary için mi geçerli? (Açıklığa kavuşturulmalı)

## Rubric Targets
- [ ] Saves reader a future task → target: 2 (pipeline şablonu, kontrol listesi)
- [ ] Includes proof → target: 2 (gerçek sürüm hikâyesi, hata ve düzeltme)
- [ ] Reusable takeaway → target: 2 (tradeoff kararları, alternatifler)
- [ ] Specific audience → target: 2 (yalnızca Rust crate geliştiricileri)
- [ ] Portable (no-author) → target: 1 (yazarın bağlamı var ama tek başına da değerli)
- [ ] Strong visual → target: 1 (YAML snippet + opsiyonel diyagram)
Target total: 10/12