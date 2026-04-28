# Telegram bridge integration

This folder contains the Telegram <-> Codex CLI bridge used for long-running remote Codex Autoresearch Convo sessions.

Key features:
- Telegram long-prompt buffering with `/prompt_begin`, `/prompt_end`, `/prompt_cancel`
- live-tail heartbeat updates
- resume-safe Codex passthrough filtering
- optional autonomous continuation mode with `AUTONOMOUS_LONG_RUN` or `CODEX_TG_AUTO_CONTINUE=1`

Do not commit `.env` files or Telegram tokens.
