from __future__ import annotations

import pytest

from tests.security.world import World, build_world


@pytest.fixture
def world() -> World:
    return build_world()
