# Writer Context Packet — 2026-05-knowgraph-projesi-graph-rag-mcp-server-for-code
## Meta
- **Route:** ORIGINAL
- **Format:** Thread (8 tweets)
- **Pillar:** Open Source AI / Developer Tools

## Thesis
KnowGraph, AI kod asistanlarınıza kodunuzu sadece metin olarak değil, bir **canlı graph** olarak anlama yeteneği kazandıran açık kaynak bir MCP server'dır.

## Target Reader
AI araçları kullanan yazılım geliştiriciler (Claude/Cursor/Gemini kullanıcıları). 
Kod tabanını anlamakta zorlanan, "AI kodumu gerçekten anlıyor mu?" diye soran mühendisler.

## Angle (Beklenmedik Çerçeve)
Herkes vector similarity peşinde koşarken, KnowGraph **Graph Theory + Joern CPG** ile deterministik kod anlayışı sunuyor. Vector'lerin bulanıklığı yerine, gerçek ilişkileri takip ediyor.

## Proof Elements
- 109 commit, production-ready v1.0.0
- 15+ dil desteği (Python, JS, Rust, Go, C++, Java...)
- ~30s ilk index, <1s yeniden index
- 474 entity extract, 85 edge call graph, 45 data flow
- Security analysis: SQLi, XSS, Buffer Overflow taint tracking
- MCP compatible — Claude, Cursor, Gemini, her MCP client ile çalışır
- Joern CPG (Code Property Graph) ile güçlendirilmiş
- %100 test coverage, zero dead code
- pip install knowgraph ile kurulum

## Constraints
- X thread formatı: her tweet bağımsız okunabilir olmalı
- Teknik ama her seviyeden geliştiriciye hitap eden dil
- Son tweet'te CTA: GitHub'ta star + denemeye çağrı

## Voice Anchors
- Doğrudan, teknik ama samimi
- "Herkes X yaparken, biz Y yaptık" hikayesi
- Kişisel deneyim (kendi projem) anlatımı

## Risks (Slop/Cringe)
- Aşırı teknik jargon (Scala, CPG, PDG — açıklanmalı)
- "AI çağında" gibi klişe açılış
- Abartılı iddialar (kanıtlarla desteklenmeli)

## Rubric Targets
- [ ] Saves reader a future task → hedef: 2
- [ ] Includes proof → hedef: 2 (sayılar, benchmark'lar)
- [ ] Reusable takeaway → hedef: 2 (pip install knowgraph)
- [ ] Specific audience → hedef: 2 (AI kullanan geliştiriciler)
- [ ] Portable (no-author) → hedef: 2 (herkes kullanabilir)
- [ ] Strong visual → hedef: 1 (metin thread, görsel yok)
Target total: 11/12
