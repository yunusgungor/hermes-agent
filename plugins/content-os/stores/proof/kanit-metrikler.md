# Kanıt: KnowGraph Performans Metrikleri

**Proje:** KnowGraph — Code Knowledge Graph MCP Server
**Tip:** Benchmark / Metrik
**Tarih:** 2026-05-13

- İlk index: ~30sn (474 entity, 85 edge call graph, 45 data flow)
- Cached re-index: <1sn
- Query latency: 2-5sn (CODE), <1sn (TEXT)
- Memory: ~100-150MB total
- Incremental indexing: sadece değişen dosyalar
- Dil desteği: 15+ (Python, JS, Rust, Go, C++, Java...)

---

# Kanıt: KnowGraph Kod Kalitesi

**Proje:** KnowGraph
**Tip:** Proje metriği
**Tarih:** 2026-05-13

- 109 commit, production-ready v1.0.0
- %100 test coverage
- Zero dead code policy
- MIT License
- pip install knowgraph (PyPI)
- Joern CPG (Code Property Graph) tabanlı
- Security: SQLi, XSS, Buffer Overflow taint tracking

---

# Kanıt: Neural Processor X1 Optimizasyonu

**Proje:** Neural Processor X1
**Tip:** Benchmark
**Tarih:** 2026-05-07

- RISC-V + NPU pipeline
- %21 daha küçük alan
- 9× daha az güç tüketimi
- 3 pipeline tweak'i ile sonuç
