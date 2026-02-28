"""Pytest shared fixtures and configuration for E2E tests.

This module provides:
- Environment variable loading from .env.test file
- Shared fixtures: test_config, base_url, client, event_loop
- Custom command line option: --filter-type
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command line options for E2E tests."""
    parser.addoption(
        "--filter-type",
        action="store",
        default=None,
        type=int,
        help="Filter test cases by intent type ID",
    )


@pytest.fixture(scope="session")
def filter_type(request: pytest.FixtureRequest) -> int | None:
    """Get filter type from command line option."""
    return request.config.getoption("--filter-type")


@dataclass
class TestConfig:
    """Test configuration loaded from environment variables.

    Follows 12-factor app principles - all configuration via environment variables.
    """

    # Service configuration
    base_url: str = "http://localhost:11028"
    timeout: int = 60

    # Test data configuration
    data_path: str = "tests/data/intent_test_cases.xlsx"
    user_id: str = "test_e2e"

    # Test behavior configuration
    skip_e2e: bool = False
    log_level: str = "INFO"
    filter_type: str | None = None

    # Report configuration
    report_path: str | None = None

    @classmethod
    def from_env(cls) -> TestConfig:
        """Load configuration from environment variables.

        Environment variables:
        - TEST_BASE_URL: Test target service address (default: http://localhost:11028)
        - TEST_TIMEOUT: Request timeout in seconds (default: 60)
        - TEST_DATA_PATH: Excel test data file path (default: tests/data/intent_test_cases.xlsx)
        - TEST_USER_ID: Test user ID (default: test_e2e)
        - SKIP_E2E_TEST: Skip E2E tests if set to "1" or "true" (default: False)
        - FILTER_TYPE: Only run specific intent type (used with --filter-type)
        - LOG_LEVEL: Test log level (default: INFO)
        - TEST_REPORT_PATH: Path to save JSON test report (default: None)

        Returns:
            TestConfig instance with values from environment
        """
        # Try to load .env.test file if it exists
        env_test_file = Path(".env.test")
        if env_test_file.exists():
            _load_dotenv(env_test_file)

        # Also try to load regular .env file
        env_file = Path(".env")
        if env_file.exists():
            _load_dotenv(env_file)

        skip_str = os.environ.get("SKIP_E2E_TEST", "").lower()
        skip_e2e = skip_str in ("1", "true", "yes")

        return cls(
            base_url=os.environ.get("TEST_BASE_URL", "http://localhost:11028"),
            timeout=int(os.environ.get("TEST_TIMEOUT", "60")),
            data_path=os.environ.get(
                "TEST_DATA_PATH", "tests/data/intent_test_cases.xlsx"
            ),
            user_id=os.environ.get("TEST_USER_ID", "test_e2e"),
            skip_e2e=skip_e2e,
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
            filter_type=os.environ.get("FILTER_TYPE"),
            report_path=os.environ.get("TEST_REPORT_PATH"),
        )


def _load_dotenv(file_path: Path) -> None:
    """Load environment variables from a .env file.

    Args:
        file_path: Path to the .env file
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    # Only set if not already set in environment
                    if key not in os.environ:
                        os.environ[key] = value
    except Exception:
        pass  # Silently fail if .env file can't be read


@pytest.fixture(scope="session")
def test_config() -> TestConfig:
    """Provide test configuration loaded from environment variables.

    Returns:
        TestConfig instance with all test settings
    """
    return TestConfig.from_env()


@pytest.fixture(scope="session")
def base_url(test_config: TestConfig) -> str:
    """Provide the base URL for API requests.

    Returns:
        Base URL from TEST_BASE_URL environment variable
    """
    return test_config.base_url


@pytest.fixture(scope="session")
async def client(test_config: TestConfig) -> httpx.AsyncClient:
    """Provide configured HTTP client for API requests.

    Args:
        test_config: Test configuration fixture

    Returns:
        Configured httpx.AsyncClient instance
    """
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(test_config.timeout),
        follow_redirects=True,
    ) as client:
        yield client


@pytest.fixture(scope="session")
def event_loop():
    """Provide event loop for async tests.

    Creates a new event loop for the test session to avoid
    'event loop is closed' errors with pytest-asyncio.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def check_skip_e2e(test_config: TestConfig) -> None:
    """Check if E2E tests should be skipped.

    Automatically skips all E2E tests if SKIP_E2E_TEST is set.
    """
    if test_config.skip_e2e:
        pytest.skip("E2E tests skipped (SKIP_E2E_TEST=1)")


# Pytest markers configuration
def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers",
        "e2e: marks tests as end-to-end tests (deselect with '-m \"not e2e\"')",
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
