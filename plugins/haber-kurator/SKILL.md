---
title: "Haber-Kurator → MIGRATED to Prodinamik Engine"
description: "Haber-Kurator plugin (thin wrapper) — all functionality migrated to Prodinamik Engine"
category: haber-kurator
---

# Haber-Kurator (MIGRATED)

> ⚠️ **Haber-Kurator is fully migrated to [Prodinamik Engine](../prodinamik-engine/SKILL.md)**

## Quick Migration Guide

This plugin is now a **thin wrapper** that delegates all calls to Prodinamik Engine.

| Old Way | New Way |
|---------|---------|
| `haber_kurator_manager action=fetch_news` | `prodinamik action=fetch_news country=turkey` |
| `haber_kurator_manager action=verify_news` | `prodinamik action=verify_news country=turkey` |
| `/haber` | `/run haber <title>` |
| `hermes haber ...` | `hermes prodinamik ...` |

## Legacy Backward Compatibility

The old tool names (`haber_kurator_manager`, `haber_kurator_retriever`) still work via thin wrapper delegation. However, new usage should use the `prodinamik` tool directly.

Original source code archived at: `plugins/archive/haber-kurator/`

## References

- [Prodinamik Engine SKILL.md](../prodinamik-engine/SKILL.md)
- Archive: `plugins/archive/haber-kurator/`
