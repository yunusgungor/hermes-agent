# Prodinamik Engine — Hermes Plugin

**Workflow Engine:** State machine, validation, event sourcing, AI Grid, Raft consensus.

## Slash Commands
- `/run <profile> <title>` — Create a new workflow run
- `/p-approve <slug>` — Approve a pending task
- `/p-next <slug>` — Show next step  
- `/p-status [slug]` — Show engine/run status

## Profiles
- **software** — Yazılım geliştirme (spec → prototyping → iteration → review → release)
- **content-os** — İçerik üretim (captured → idea_review → brief_ready → ... → published)
- **haber-kurator** — Haber doğrulama (fetch_news → verify_news → publish_verified)
- **research** — Araştırma pipeline
- **design** — Tasarım pipeline

## Quick Start
```
/run software "AI Modülü"
/p-status selam-paketi
/p-next selam-paketi
/p-approve selam-paketi
```

## Tool: `prodinamik`
Actions: run, list, status, approve, reject, next, transition, dashboard, budget
