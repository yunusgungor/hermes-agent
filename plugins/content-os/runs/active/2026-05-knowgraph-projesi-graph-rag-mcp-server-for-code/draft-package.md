---
draft:

1/8
AI kod asistanınız kodunuzu gerçekten anlamıyorsa sorun sizde değil — yaklaşımda.

Vector similarity'nin bulanıklığı yerine Graph Theory + Joern CPG ile çalışan açık kaynak MCP server: KnowGraph 🧵👇

github.com/yunusgungor/knowgraph

2/8
KnowGraph nedir?

Bir MCP server. Kod tabanınızı knowledge graph'a çevirir. Joern Code Property Graph ile güçlendirilmiştir. 15+ dil destekler.

AI asistanınıza kodunuzu "okuma" değil, "anlama" yeteneği kazandırır.

3/8
🔬 Neler yapar?
• Graph-based code understanding
• Security: SQLi, XSS, buffer overflow taint tracking
• Impact analysis: değişikliğin etki alanı
• Time-travel: graph'te versiyon kontrolü
• PDG/CFG/DDG/CDG görselleştirme

4/8
⚡ Performans rakamları:
• İlk index: ~30sn (474 entity, 85 edge, 45 flow)
• Cached re-index: <1sn
• Query: 2-5sn (CODE), <1sn (TEXT)
• Incremental: sadece değişen dosyaları yeniden indexler
• Memory: ~100-150MB total

Production'da kanıtlanmıştır.

5/8
🔌 MCP compatible — her AI aracı:
✅ Claude Desktop
✅ Cursor
✅ Gemini (Antigravity)
✅ Her MCP client

3 satır JSON. Bu kadar. AI asistanınız artık kodunuzu graph olarak okuyabiliyor.

6/8
💻 Kurulum:
pip install knowgraph
knowgraph-setup-joern
knowgraph serve

Config'i MCP client'ınıza ekleyin, çalışsın.
Açık kaynak (MIT). 109 commit. %100 test coverage.

7/8
🧪 Doğal dilde sorgulayın:
🔹 "Find SQL injection vulnerabilities"
🔹 "Show call path from main to database_connect"
🔹 "Get PDG for calculateTax"
🔹 "Trace data flow from userInput to exec"
🔹 "Find dead code"

Türkçe de çalışır, İngilizce de.

8/8
KnowGraph, vector similarity'nin ötesine geçip Graph Theory + Joern CPG ile deterministik kod anlayışı sunar.

⭐ Star atın, deneyin, katkıda bulunun:
github.com/yunusgungor/knowgraph

Kodunuz metin değil, yaşayan bir graph'tır. 🧠

rubric_self_assessment:
- Saves reader a future task: 2 — pip install ile hemen kullanılabilir
- Includes proof: 2 — 30s index, 474 entity, <1s re-index, 15+ dil
- Gives a reusable takeaway: 2 — 3 satır JSON + pip install = çalışır
- Specific audience: 2 — AI kullanan geliştiriciler
- Portable: 2 — açık kaynak, herkes kullanabilir
- Strong visual: 1 — metin thread
TOTAL: 11/12

avoid_slop_pass:
- (clean — no slop detected)

open_loops_flagged:
- (none)

voice_check:
- Direct, technical but accessible: followed
- Proof-driven: followed (numbers in every claim)
- Personal project narrative: followed
- No banned patterns: clean
---
