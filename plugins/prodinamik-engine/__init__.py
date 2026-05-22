"""Prodinamik Engine Plugin — Hermes Agent integration.

Loads the pre-compiled __init__.pyc module and re-exports its register()
function so Hermes can discover and load this plugin at startup.
"""
from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path

_parent = Path(__file__).parent
_pyc = _parent / "__init__.pyc"

# Load the pre-compiled module
_name = "prodinamik_engine_compiled"
if _name not in sys.modules:
    spec = importlib.util.spec_from_file_location(_name, _pyc)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {_pyc} — plugin is corrupt or missing")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[_name] = mod
    spec.loader.exec_module(mod)

# Re-export for Hermes plugin loader
from prodinamik_engine_compiled import VERSION, register as _compiled_register  # noqa: E402, F401

logger = logging.getLogger(__name__)


def register(ctx):
    """Plugin registration — wraps the compiled register() with Telegram compatibility.

    The compiled code registers 5 slash commands:
        /run <profile> <title>
        /p-approve <slug>
        /p-next <slug>
        /p-status [slug]
        /p-resume <slug> <answer>

    The Telegram bot command menu excludes plugin commands that require
    arguments (``telegram_bot_commands()`` filters out entries whose
    ``args_hint`` starts with ``<``). To make all commands visible in
    Telegram, we re-register them **without** ``args_hint`` after the
    compiled registration runs.

    CLI mode is unaffected — the compiled code already handles that.
    """

    def _wrap_handler(handler):
        """Wrap a handler to accept raw args + ctx."""
        import inspect

        if inspect.iscoroutinefunction(handler):

            async def _async_wrapped(raw, ctx=ctx):
                return await handler(raw, ctx)
            _async_wrapped.__name__ = getattr(handler, "__name__", "handler")
            return _async_wrapped
        else:

            def _sync_wrapped(raw, ctx=ctx):
                return handler(raw, ctx)
            _sync_wrapped.__name__ = getattr(handler, "__name__", "handler")
            return _sync_wrapped

    # 1. Run the original compiled registration (registers tool + hooks)
    try:
        _compiled_register(ctx)
    except Exception as exc:
        logger.warning("Compiled registration failed: %s", exc)

    # 2. Re-register all slash commands without args_hint so Telegram shows them
    #    Commands with args_hint="<...>" are otherwise filtered out by
    #    telegram_bot_commands() → _requires_argument().
    from hermes_cli.plugins import get_plugin_manager

    mgr = get_plugin_manager()
    for name, entry in list(mgr._plugin_commands.items()):
        if name.startswith("p-") or name == "run":
            handler = entry.get("handler")
            if handler:
                ctx.register_command(
                    f"/{name}",
                    _wrap_handler(handler),
                    description=entry.get("description", "") or "Prodinamik Engine command",
                    args_hint="",  # No hint → passes _requires_argument() → shows in Telegram
                )

    logger.info(
        "Prodinamik Engine v%s: %d slash commands re-registered for Telegram",
        VERSION,
        len([n for n in mgr._plugin_commands if n.startswith("p-") or n == "run"]),
    )

