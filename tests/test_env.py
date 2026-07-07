from __future__ import annotations

import os

from isms.env import load_env_file


def test_load_env_file(tmp_path, monkeypatch):
    monkeypatch.delenv("ISMS_API_URL", raising=False)
    monkeypatch.delenv("ISMS_API_TOKEN", raising=False)
    f = tmp_path / "isms.env"
    f.write_text(
        """
        # comment line
        ISMS_API_URL=https://example.isms.sh
        ISMS_API_TOKEN="secret-token"
        ISMS_ORGANIZATION='acme'

        BLANK_LINE_ABOVE=ok
        """.strip()
    )

    result = load_env_file(f)

    assert result == {
        "ISMS_API_URL": "https://example.isms.sh",
        "ISMS_API_TOKEN": "secret-token",
        "ISMS_ORGANIZATION": "acme",
        "BLANK_LINE_ABOVE": "ok",
    }
    assert os.environ["ISMS_API_URL"] == "https://example.isms.sh"
    assert os.environ["ISMS_API_TOKEN"] == "secret-token"


def test_load_env_file_missing(tmp_path):
    result = load_env_file(tmp_path / "does-not-exist.env")
    assert result == {}


def test_load_env_file_no_override(tmp_path, monkeypatch):
    monkeypatch.setenv("KEEP_ME", "original")
    f = tmp_path / "isms.env"
    f.write_text("KEEP_ME=changed\n")

    load_env_file(f, override=False)

    assert os.environ["KEEP_ME"] == "original"
