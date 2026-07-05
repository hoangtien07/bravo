"""Wave 2 — boot-guard mở rộng (W2.6) + observability record (W2.2). Không cần DB."""
from __future__ import annotations

import pytest

from app.config import Settings


def _prod(**kw) -> Settings:
    base = dict(env="production", jwt_secret="x" * 20, mcp_token_pepper="y" * 20,
                cloud_enabled=False, allow_self_approval=False)
    base.update(kw)
    return Settings(**base)


def test_bootguard_rejects_self_approval_in_prod():
    with pytest.raises(RuntimeError, match="allow_self_approval"):
        _prod(allow_self_approval=True).validate_boot()


def test_bootguard_oidc_requires_strong_session_and_full_config():
    with pytest.raises(RuntimeError, match="session_secret"):
        _prod(oidc_enabled=True, session_secret="change-me-session").validate_boot()
    with pytest.raises(RuntimeError, match="oidc_issuer|client_id|redirect"):
        _prod(oidc_enabled=True, session_secret="s" * 20).validate_boot()


def test_bootguard_passes_clean_prod():
    _prod().validate_boot()  # không raise


def test_bootguard_oidc_full_config_passes():
    _prod(oidc_enabled=True, session_secret="s" * 20, oidc_issuer="http://kc/realms/b",
          oidc_client_id="bravo", oidc_client_secret="sec", oidc_redirect_uri="https://a/cb"
          ).validate_boot()


def test_observability_record_is_safe_noop_style():
    # record_llm/record_tool không được raise dù prometheus có hay không.
    from app.observability import record_llm, record_tool
    record_llm("local", 10, 5)
    record_tool("kb_search", "executed")
