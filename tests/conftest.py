# tests/conftest.py
import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agents.analyzer import LegalAnalyzer
from core.agents.researcher import LegalResearcher
from core.agents.strategist import LegalStrategist

@pytest.fixture
def analyzer():
    return LegalAnalyzer()

@pytest.fixture
def researcher():
    return LegalResearcher()

@pytest.fixture
def strategist():
    return LegalStrategist()