import pytest
import requests


@pytest.fixture(autouse=True)
def block_real_network(monkeypatch):
    """Fail any test that tries to reach the real internet."""
    def refuse(*args, **kwargs):
        raise RuntimeError("Tests must not make real network calls")
    monkeypatch.setattr(requests.Session, "request", refuse)
