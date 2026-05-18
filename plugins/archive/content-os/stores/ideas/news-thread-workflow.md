# Günlük Tech News Thread Workflow

## Pipeline Akışı

Bu workflow, günlük cron job tarafından otomatik tetiklenir:

1. **Web'den haber çek** — güvenilir kaynaklardan (TechCrunch, The Verge, ArsTechnica, HN, arXiv)
2. **Haberleri analiz et** — her habere bükülük seviyesi ata (KRİTİK/YÜKSEK/ORTA/DÜŞÜK)
3. **Bükülük sırala** — KRİTİK > YÜKSEK > ORTA > DÜŞÜK
4. **İlk 5 haberi seç** — DÜŞÜK haberleri genelde atla (yer yoksa)
5. **Content OS run'ı oluştur** — `hermes content new` veya `content_os_manager action=new_run`
6. **Tweet thread hazırla** — generate_draft veya manuel template
7. **Verification** — run_verifier + scan_slop + score
8. **Publish hazır** — draft_review state

## Örnek Thread Template (Bükülük Sıralı 8 Tweet)

```
Tweet 1: 🔴 KRİTİK: [Haber başlığı — hook]
         [Haberin özü 1 cümle + neden bu kadar önemli]

Tweet 2: [Teknik detay — ne değişti?]
         [Metrik / benchmark / architecture farkı]

Tweet 3: [Sektörel etki — kim kazanır/kaybeder?]
         [Tradeoff analizi]

Tweet 4: 🟠 YÜKSEK: [İkinci haber başlığı]
         [Ne oldu + neden önemli]

Tweet 5: [Detay + rakip karşılaştırması]

Tweet 6: 🟢 ORTA: Kısa Haberler
         • [Haber 1] — [1 cümle yorum]
         • [Haber 2] — [1 cümle yorum]
         • [Haber 3] — [1 cümle yorum]

Tweet 7: 🟢 Devam
         • [Haber 4]
         • [Haber 5]

Tweet 8: 📌 Bugünün Özeti
         En kritik: [K]
         Takip edilmesi gereken: [Y]
         Yarın için öngörü: [1 cümle]
```

## Kalite Standartları

- Her tweet'te en az 1 **somut bilgi** (metric, benchmark, tarih, isim)
- Her tweet'te en az 1 **mühendis yorumu** (tradeoff, etki, bağlam)
- Sadece link paylaşan tweet yasak (yorum şart)
- KRİTİK haberlerde mutlaka teknik derinlik
- DÜŞÜK haberleri dahil etme (zaman kaybı)
