"""
Backward-compatible config entrypoint.

Primary implementation lives in `src/config/settings.py` and loads:
- `config.yaml` (non-sensitive config, per-environment)
- `.env.{active_env}` (sensitive config)
"""

from src.config.settings import Settings, settings
