from pathlib import Path

from scripts.configure_wp00_cloud_llm import configure


def test_cloud_configuration_normalizes_compatible_urls_without_changing_secret(tmp_path: Path):
    path = tmp_path / ".env.wp00"
    path.write_text(
        "CLOUD_BASE_URL=compatible.example/v1\n"
        "CLOUD_EMBEDDING_BASE_URL=embedding.example/v1\n"
        "CLOUD_MODEL=chat-model\nCLOUD_API_KEY=secret-value\n"
        "JWT_SECRET=change-me\nMCP_TOKEN_PEPPER=change-me\n",
        encoding="utf-8")

    configure(path, cloud_embedding=True)

    values = dict(line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines() if "=" in line)
    assert values["CLOUD_BASE_URL"] == "https://compatible.example/v1"
    assert values["CLOUD_EMBEDDING_BASE_URL"] == "https://embedding.example/v1"
    assert values["CLOUD_API_KEY"] == "secret-value"
    assert values["EMBEDDING_DIM"] == "1536"


def test_exposed_credential_cleanup_sets_openai_defaults_but_never_preserves_the_key(tmp_path: Path):
    path = tmp_path / ".env.wp00"
    path.write_text(
        "CLOUD_BASE_URL=old.example\nCLOUD_MODEL=old-model\nCLOUD_API_KEY=exposed\n"
        "CLOUD_EMBEDDING_API_KEY=also-exposed\nJWT_SECRET=a" + "x" * 32 + "\n"
        "MCP_TOKEN_PEPPER=b" + "x" * 32 + "\n",
        encoding="utf-8")

    configure(path, openai_compatible=True, clear_exposed_credentials=True)

    values = dict(line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines() if "=" in line)
    assert values["CLOUD_BASE_URL"] == "https://api.openai.com/v1"
    assert values["CLOUD_MODEL"] == "gpt-4o"
    assert values["CLOUD_API_KEY"] == ""
    assert values["CLOUD_EMBEDDING_API_KEY"] == ""
