import pytest
import time

@pytest.fixture
def disable_sleep(monkeypatch):
    monkeypatch.setattr(time,'sleep',lambda x: None)


