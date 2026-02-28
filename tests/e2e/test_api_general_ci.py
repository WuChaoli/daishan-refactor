"""CI/CD Ready E2E Test Suite for /api/general endpoint.

This module provides:
- Environment-based configuration (no local development assumptions)
- Pytest-discoverable test functions
- JSON test report generation
- Intent type filtering support
- Detailed diagnostic output on failure

Usage:
    # Run all E2E tests
    pytest tests/e2e/test_api_general_ci.py -v

    # Run specific intent type only
    pytest tests/e2e/test_api_general_ci.py -v --filter-type=1

    # Run from command line (without pytest)
    python tests/e2e/test_api_general_ci.py

    # Skip E2E tests
    SKIP_E2E_TEST=1 pytest tests/e2e/test_api_general_ci.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
import pytest

if TYPE_CHECKING:
    from conftest import TestConfig

if TYPE_CHECKING:
    from conftest import TestConfig


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class ApiApiTestCase:
    """Test case data class."""

    question: str
    expected_type: int
    description: str
    notes: str = ""


@dataclass
class ApiApiTestResult:
    """Single test result."""

    test_case: ApiApiTestCase
    success: bool
    status_code: int | None = None
    response_time_ms: float = 0.0
    stream_events: list[dict] = field(default_factory=list)
    error_message: str = ""
    classification_type: int | None = None
    classification_confidence: float | None = None


@dataclass
class ApiApiTestReport:
    """Complete test report."""

    total: int = 0
    passed: int = 0
    failed: int = 0
    results: list[ApiApiTestResult] = field(default_factory=list)
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary for JSON serialization."""
        return {
            "summary": {
                "total": self.total,
                "passed": self.passed,
                "failed": self.failed,
                "pass_rate": (
                    f"{self.passed / self.total * 100:.1f}%" if self.total > 0 else "0%"
                ),
            },
            "timing": {
                "start_time": self.start_time,
                "end_time": self.end_time,
                "duration_seconds": self.duration_seconds,
            },
            "results": [
                {
                    "description": r.test_case.description,
                    "question": r.test_case.question,
                    "expected_type": r.test_case.expected_type,
                    "success": r.success,
                    "status_code": r.status_code,
                    "response_time_ms": round(r.response_time_ms, 2),
                    "stream_event_count": len(r.stream_events),
                    "error_message": r.error_message,
                    "classification_type": r.classification_type,
                    "classification_confidence": r.classification_confidence,
                }
                for r in self.results
            ],
        }


# =============================================================================
# Configuration Functions
# =============================================================================


def load_config_from_env() -> dict[str, Any]:
    """Load configuration from environment variables.

    Returns:
        Dictionary with configuration values
    """
    return {
        "base_url": os.environ.get("TEST_BASE_URL", "http://localhost:11028"),
        "timeout": int(os.environ.get("TEST_TIMEOUT", "60")),
        "data_path": os.environ.get(
            "TEST_DATA_PATH", "tests/data/intent_test_cases.xlsx"
        ),
        "user_id": os.environ.get("TEST_USER_ID", "test_e2e"),
        "report_path": os.environ.get("TEST_REPORT_PATH"),
        "filter_type": os.environ.get("FILTER_TYPE"),
    }


# =============================================================================
# Test Data Loading
# =============================================================================


def load_test_cases(data_path: str, filter_type: int | None = None) -> list[ApiTestCase]:
    """Load test cases from Excel file.

    Args:
        data_path: Path to Excel file with test cases
        filter_type: Optional filter by expected_type

    Returns:
        List of test cases

    Raises:
        ImportError: If pandas is not installed
        FileNotFoundError: If test cases file not found
    """
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError(
            "pandas is required for loading test cases. "
            "Install with: uv add --dev pandas openpyxl"
        ) from e

    excel_path = Path(data_path)
    if not excel_path.exists():
        raise FileNotFoundError(f"Test cases file not found: {excel_path}")

    df = pd.read_excel(excel_path)
    cases = []

    required_columns = {"question", "expected_type", "description"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in test data: {missing}")

    for _, row in df.iterrows():
        try:
            case = ApiTestCase(
                question=str(row["question"]),
                expected_type=int(row["expected_type"]),
                description=str(row["description"]),
                notes=str(row.get("notes", "")),
            )
            if filter_type is None or case.expected_type == filter_type:
                cases.append(case)
        except (ValueError, TypeError) as e:
            print(f"Warning: Skipping invalid row: {e}")
            continue

    return cases


# =============================================================================
# API Call Functions
# =============================================================================


async def call_api_general(
    client: httpx.AsyncClient,
    base_url: str,
    question: str,
    user_id: str = "test_e2e",
) -> tuple[int, list[dict], float]:
    """Call /api/general endpoint with streaming response.

    Args:
        client: HTTP client
        base_url: Server base URL
        question: Question text
        user_id: User ID

    Returns:
        Tuple of (status_code, stream_events, response_time_ms)

    Raises:
        httpx.HTTPError: On HTTP errors
        Exception: On other errors
    """
    url = f"{base_url}/api/general"
    payload = {
        "question": question,
        "user_id": user_id,
        "stream": True,
    }

    start_time = time.time()
    events = []

    try:
        async with client.stream("POST", url, json=payload) as response:
            status_code = response.status_code

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        event_data = json.loads(data)
                        events.append(event_data)
                    except json.JSONDecodeError:
                        events.append({"raw": data})

        response_time = (time.time() - start_time) * 1000
        return status_code, events, response_time

    except Exception:
        response_time = (time.time() - start_time) * 1000
        raise


async def run_single_test(
    client: httpx.AsyncClient,
    base_url: str,
    test_case: ApiTestCase,
    user_id: str = "test_e2e",
) -> ApiTestResult:
    """Run a single test case.

    Args:
        client: HTTP client
        base_url: Server base URL
        test_case: Test case to run
        user_id: User ID for the request

    Returns:
        ApiTestResult with all test details
    """
    result = ApiTestResult(test_case=test_case, success=False)

    try:
        status_code, events, response_time = await call_api_general(
            client, base_url, test_case.question, user_id
        )

        result.status_code = status_code
        result.response_time_ms = response_time
        result.stream_events = events

        if status_code != 200:
            result.error_message = f"HTTP {status_code}"
            return result

        if not events:
            result.error_message = "Empty stream response"
            return result

        result.success = True

    except httpx.TimeoutException:
        result.error_message = f"Request timeout after {result.response_time_ms:.0f}ms"
    except httpx.ConnectError as e:
        result.error_message = f"Connection error: {e}"
    except Exception as e:
        result.error_message = f"Error: {type(e).__name__}: {e}"

    return result


# =============================================================================
# Test Report Functions
# =============================================================================


def print_report(report: ApiTestReport) -> None:
    """Print test report to console in human-readable format.

    Args:
        report: Test report to print
    """
    print("\n" + "=" * 70)
    print("E2E Test Report - /api/general")
    print("=" * 70)
    print(f"Total: {report.total}, Passed: {report.passed}, Failed: {report.failed}")
    if report.total > 0:
        print(f"Pass Rate: {report.passed / report.total * 100:.1f}%")
    print(f"Duration: {report.duration_seconds:.1f}s")
    print("-" * 70)

    for result in report.results:
        status = "PASS" if result.success else "FAIL"
        icon = "✓" if result.success else "✗"
        print(f"\n[{icon}] {status}: {result.test_case.description}")
        print(f"    Question: {result.test_case.question}")
        print(f"    Expected Type: {result.test_case.expected_type}")
        print(f"    Status Code: {result.status_code}")
        print(f"    Response Time: {result.response_time_ms:.1f}ms")
        print(f"    Stream Events: {len(result.stream_events)}")

        if result.error_message:
            print(f"    Error: {result.error_message}")

    print("\n" + "=" * 70)


def save_report(report: ApiTestReport, output_path: Path | None = None) -> Path:
    """Save report to JSON file.

    Args:
        report: Test report to save
        output_path: Optional path for output file

    Returns:
        Path to saved report file
    """
    if output_path is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"e2e_report_{timestamp}.json")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)

    return output_path


# =============================================================================
# Pytest Test Functions
# =============================================================================


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_api_general_health(
    client: httpx.AsyncClient,
    base_url: str,
) -> None:
    """Test health endpoint is accessible.

    Verifies:
    - Service is running and responsive
    - Health endpoint returns 200 OK
    - Response time is reasonable (< 5 seconds)
    """
    health_url = f"{base_url}/health"

    response = await client.get(health_url, timeout=5.0)

    assert response.status_code == 200, (
        f"Health check failed: expected 200, got {response.status_code}. "
        f"Response: {response.text}"
    )

    # Try to parse JSON response
    try:
        data = response.json()
        assert "status" in data or "healthy" in str(data).lower(), (
            f"Health response missing status field: {data}"
        )
    except json.JSONDecodeError:
        # Some health endpoints return plain text
        pass


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_api_general_all_cases(
    client: httpx.AsyncClient,
    base_url: str,
    test_config: TestConfig,
    filter_type: int | None,
) -> None:
    """Run all E2E test cases from Excel file.

    This test:
    1. Loads test cases from Excel file
    2. Calls /api/general for each test case
    3. Verifies streaming response
    4. Generates JSON test report

    Args:
        client: HTTP client fixture
        base_url: Service base URL
        test_config: Test configuration
        filter_type: Optional filter for specific intent type

    Raises:
        pytest.skip: If SKIP_E2E_TEST is set
        AssertionError: If any test case fails
    """
    if test_config.skip_e2e:
        pytest.skip("E2E tests skipped (SKIP_E2E_TEST=1)")

    # Use filter from command line or environment
    filter_value = filter_type
    if filter_value is None and test_config.filter_type:
        try:
            filter_value = int(test_config.filter_type)
        except (ValueError, TypeError):
            pass

    # Load test cases
    try:
        test_cases = load_test_cases(test_config.data_path, filter_value)
    except FileNotFoundError as e:
        pytest.skip(f"Test data file not found: {e}")
    except ImportError as e:
        pytest.skip(f"Required dependencies not installed: {e}")

    if not test_cases:
        pytest.skip("No test cases found (check filter or data file)")

    # Run tests
    report = ApiTestReport()
    report.start_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    report.total = len(test_cases)

    for test_case in test_cases:
        result = await run_single_test(client, base_url, test_case, test_config.user_id)

        if result.success:
            report.passed += 1
        else:
            report.failed += 1

        report.results.append(result)

    report.end_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Print detailed report
    print_report(report)

    # Save report to file
    report_path = test_config.report_path
    if report_path:
        saved_path = save_report(report, Path(report_path))
        print(f"\nReport saved to: {saved_path}")

    # Assert all tests passed
    if report.failed > 0:
        failed_cases = [
            f"  - {r.test_case.description}: {r.error_message}"
            for r in report.results
            if not r.success
        ]
        assert report.failed == 0, (
            f"{report.failed} of {report.total} test cases failed:\n"
            + "\n".join(failed_cases[:10])  # Show first 10 failures
        )


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
@pytest.mark.parametrize("intent_type", [1, 2, 3])
async def test_api_general_by_type(
    client: httpx.AsyncClient,
    base_url: str,
    test_config: TestConfig,
    intent_type: int,
) -> None:
    """Test API with specific intent types.

    Parameterized test that runs separately for each intent type:
    - Type 1: Enterprise Query (企业查询)
    - Type 2: Data Analysis (数据分析)
    - Type 3: Intent Classification (意图分类)

    Args:
        client: HTTP client fixture
        base_url: Service base URL
        test_config: Test configuration
        intent_type: Intent type ID to test
    """
    if test_config.skip_e2e:
        pytest.skip("E2E tests skipped (SKIP_E2E_TEST=1)")

    # Load test cases for this specific type
    try:
        test_cases = load_test_cases(test_config.data_path, intent_type)
    except FileNotFoundError as e:
        pytest.skip(f"Test data file not found: {e}")
    except ImportError as e:
        pytest.skip(f"Required dependencies not installed: {e}")

    if not test_cases:
        pytest.skip(f"No test cases found for intent type {intent_type}")

    # Run at least one test case for this type
    test_case = test_cases[0]
    result = await run_single_test(client, base_url, test_case, test_config.user_id)

    assert result.success, (
        f"Intent type {intent_type} test failed for '{test_case.description}': "
        f"{result.error_message} (HTTP {result.status_code})"
    )


# =============================================================================
# Command Line Entry Point
# =============================================================================


async def main() -> int:
    """Main entry point for running tests outside of pytest.

    Returns:
        Exit code: 0 for success, 1 for failure
    """
    config = load_config_from_env()

    if os.environ.get("SKIP_E2E_TEST") == "1":
        print("E2E tests skipped (SKIP_E2E_TEST=1)")
        return 0

    # Check if service is healthy first
    base_url = config["base_url"]
    print(f"Checking service health at {base_url}/health...")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/health")
            if response.status_code != 200:
                print(
                    f"ERROR: Service health check failed: HTTP {response.status_code}"
                )
                return 1
    except Exception as e:
        print(f"ERROR: Cannot connect to service at {base_url}: {e}")
        print("Make sure the service is running (e.g., via Docker Compose)")
        return 1

    print("Service is healthy, running tests...")

    # Load and run tests
    filter_type = config.get("filter_type")
    if filter_type:
        try:
            filter_type = int(filter_type)
        except (ValueError, TypeError):
            filter_type = None

    try:
        test_cases = load_test_cases(config["data_path"], filter_type)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1
    except ImportError as e:
        print(f"ERROR: {e}")
        return 1

    if not test_cases:
        print("No test cases found")
        return 0

    # Run tests
    report = ApiTestReport()
    report.start_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    report.total = len(test_cases)

    timeout = config.get("timeout", 60)
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        for test_case in test_cases:
            result = await run_single_test(
                client, base_url, test_case, config["user_id"]
            )

            if result.success:
                report.passed += 1
            else:
                report.failed += 1

            report.results.append(result)

    report.end_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Print and save report
    print_report(report)

    if config["report_path"]:
        saved_path = save_report(report, Path(config["report_path"]))
        print(f"\nReport saved to: {saved_path}")
    else:
        saved_path = save_report(report)
        print(f"\nReport saved to: {saved_path}")

    return 0 if report.failed == 0 else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        exit_code = 130
    sys.exit(exit_code)
