---
title: "Content-OS → MIGRATED to Prodinamik Engine"
description: "Content-OS plugin (thin wrapper) — all functionality migrated to Prodinamik Engine"
category: productivity
---

# Content-OS (MIGRATED)

> ⚠️ **Content-OS is fully migrated to [Prodinamik Engine](../prodinamik-engine/SKILL.md)**

## Quick Migration Guide

This plugin is now a **thin wrapper** that delegates all calls to Prodinamik Engine.

| Old Way | New Way |
|---------|---------|
| `content_os_manager action=new_run idea="..."` | `prodinamik action=run profile=content title="..."` |
| `content_os_manager action=scan_slop text="..."` | `prodinamik action=scan_slop text="..."` |
| `/content` | `/run content <title>` |
| `hermes content ...` | `hermes prodinamik ...` |

## Legacy Backward Compatibility

The old tool names (`content_os_manager`, `content_os_retriever`) still work via thin wrapper delegation. However, new usage should use the `prodinamik` tool directly.

Original source code archived at: `plugins/archive/content-os/`

## References

- [Prodinamik Engine SKILL.md](../prodinamik-engine/SKILL.md)
- Archive: `plugins/archive/content-os/`
