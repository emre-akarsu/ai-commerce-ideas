"""Pricing tests run offline and deterministically: any network use fails the test."""

from __future__ import annotations

import socket
from typing import Any, NoReturn

import pytest

from components.core.fakes import FakeClock
from components.pricing import PricingConfig

from .factories import NOW, config


def _blocked(*_args: Any, **_kwargs: Any) -> NoReturn:
    raise AssertionError("network access attempted in a pricing test")


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture
def cfg() -> PricingConfig:
    return config()
