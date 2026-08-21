import os
import time

import pytest


@pytest.fixture
def disable_sleep(monkeypatch):
    monkeypatch.setattr(time,'sleep',lambda x: None)


def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kuma.settings')