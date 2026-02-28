"""
E2E test for /api/general endpoint.

Tests the complete flow:
1. Start local uvicorn server
2. Load test cases from Excel
3. Call /api/general with each test case
4. Verify streaming response
5. Parse intent classification logs
6. Generate test report
"""

from __future__ import annotations

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx


# Constants
DEFAULT_TIMEOUT = 30
HEALTH_CHECK_INTERVAL = 1
HEALTH_CHECK_MAX_RETRIES = 30
BASE_URL = "http://127.0.0.1:8000"
TEST_USER_ID = "test_e2e"


@dataclass
class TestCase:
    """Test case data class."""

    question: str
    expected_type: int
    description: str
    notes: str = ""


@dataclass
class TestResult:
    """Single test result."""

    test_case: TestCase
    success: bool
    status_code: int | None = None
    response_time_ms: float = 0.0
    stream_events: list[dict] = field(default_factory=list)
    error_message: str = ""
    classification_type: int | None = None
    classification_confidence: float | None = None


@dataclass
class TestReport:
    """Complete test report."""

    total: int = 0
    passed: int = 0
    failed: int = 0
    results: list[TestResult] = field(default_factory=list)
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "summary": {
                "total": self.total,
                "passed": self.passed,
                "failed": self.failed,
                "pass_rate": f"{self.passed / self.total * 100:.1f}%" if self.total > 0 else "0%",
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
                    "response_time_ms": r.response_time_ms,
                    "stream_event_count": len(r.stream_events),
                    "error_message": r.error_message,
                    "classification_type": r.classification_type,
                    "classification_confidence": r.classification_confidence,
                }
                for r in self.results
            ],
        }


def load_test_cases(filter_type: int | None = None) -> list[TestCase]:
    """Load test cases from Excel file.

    Args:
        filter_type: Optional filter by expected_type

    Returns:
        List of test cases
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required. Install with: uv add --dev pandas openpyxl")

    data_dir = Path(__file__).parent / "data"
    excel_path = data_dir / "intent_test_cases.xlsx"

    if not excel_path.exists():
        raise FileNotFoundError(f"Test cases file not found: {excel_path}")

    df = pd.read_excel(excel_path)
    cases = []

    for _, row in df.iterrows():
        case = TestCase(
            question=str(row["question"]),
            expected_type=int(row["expected_type"]),
            description=str(row["description"]),
            notes=str(row.get("notes", "")),
        )
        if filter_type is None or case.expected_type == filter_type:
            cases.append(case)

    return cases


def find_latest_log_file(log_dir: Path) -> Path | None:
    """Find the latest log file in the log directory."""
    if not log_dir.exists():
        return None

    log_files = list(log_dir.glob("*.log"))
    if not log_files:
        return None

    return max(log_files, key=lambda p: p.stat().st_mtime)


def parse_intent_classification_logs(log_dir: Path) -> list[dict[str, Any]]:
    """Parse intent classification logs from log files.

    Args:
        log_dir: Directory containing log files

    Returns:
        List of classification log entries
    """
    latest_log = find_latest_log_file(log_dir)
    if not latest_log:
        return []

    classifications = []
    try:
        with open(latest_log, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                    marker_type = entry.get("marker", "")
                    if marker_type in ("classifier.attempt", "classifier.success",
                                       "classifier.degraded_fallback", "classifier.low_confidence_fallback"):
                        classifications.append(entry)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    return classifications


def extract_classification_result(logs: list[dict[str, Any]]) -> tuple[int | None, float | None]:
    """Extract classification type and confidence from logs.

    Args:
        logs: List of classification log entries

    Returns:
        Tuple of (type_id, confidence) or (None, None)
    """
    for entry in reversed(logs):
        if entry.get("marker") == "classifier.success":
            data = entry.get("data", {})
            return data.get("type_id"), data.get("confidence")
    return None, None


class ServerManager:
    """Manages the uvicorn server lifecycle."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.host = host
        self.port = port
        self.process: subprocess.Popen | None = None
        self.base_url = f"http://{host}:{port}"

    def start(self) -> None:
        """Start the uvicorn server."""
        project_root = Path(__file__).parent.parent.parent.parent
        main_file = project_root / "src" / "rag_stream" / "main.py"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root / "src")

        cmd = [
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", self.host,
            "--port", str(self.port),
            "--app-dir", str(main_file.parent),
        ]

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

    async def wait_for_healthy(self, timeout: int = DEFAULT_TIMEOUT) -> bool:
        """Wait for server to be healthy."""
        start_time = time.time()
        retries = 0

        while time.time() - start_time < timeout and retries < HEALTH_CHECK_MAX_RETRIES:
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.get(f"{self.base_url}/health")
                    if response.status_code == 200:
                        return True
            except Exception:
                pass

            await asyncio.sleep(HEALTH_CHECK_INTERVAL)
            retries += 1

        return False

    def stop(self) -> None:
        """Stop the uvicorn server."""
        if self.process is None:
            return

        try:
            self.process.send_signal(signal.SIGTERM)
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        except Exception:
            pass

        self.process = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


async def call_api_general(
    client: httpx.AsyncClient,
    base_url: str,
    question: str,
    user_id: str = TEST_USER_ID,
) -> tuple[int, list[dict], float]:
    """Call /api/general endpoint.

    Args:
        client: HTTP client
        base_url: Server base URL
        question: Question text
        user_id: User ID

    Returns:
        Tuple of (status_code, stream_events, response_time_ms)
    """
    url = f"{base_url}/api/general"
    payload = {
        "question": question,
        "user_id": user_id,
        "stream": True,
    }

    start_time = time.time()
    events = []

    async with client.stream("POST", url, json=payload, timeout=60.0) as response:
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


async def run_single_test(
    client: httpx.AsyncClient,
    base_url: str,
    test_case: TestCase,
) -> TestResult:
    """Run a single test case."""
    result = TestResult(test_case=test_case, success=False)

    try:
        status_code, events, response_time = await call_api_general(
            client, base_url, test_case.question
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

    except Exception as e:
        result.error_message = str(e)

    return result


async def run_e2e_tests(
    filter_type: int | None = None,
    base_url: str = BASE_URL,
) -> TestReport:
    """Run E2E tests.

    Args:
        filter_type: Optional filter by expected_type
        base_url: Server base URL

    Returns:
        Test report
    """
    report = TestReport()
    report.start_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    test_cases = load_test_cases(filter_type)
    report.total = len(test_cases)

    log_dir = Path(".log-manager") / "runs"

    async with httpx.AsyncClient() as client:
        for test_case in test_cases:
            result = await run_single_test(client, base_url, test_case)

            if result.success:
                report.passed += 1
            else:
                report.failed += 1

            report.results.append(result)

    report.end_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    return report


def print_report(report: TestReport) -> None:
    """Print test report to console."""
    print("\n" + "=" * 60)
    print("E2E Test Report - /api/general")
    print("=" * 60)
    print(f"Total: {report.total}, Passed: {report.passed}, Failed: {report.failed}")
    if report.total > 0:
        print(f"Pass Rate: {report.passed / report.total * 100:.1f}%")
    print("-" * 60)

    for result in report.results:
        status = "PASS" if result.success else "FAIL"
        print(f"\n[{status}] {result.test_case.description}")
        print(f"  Question: {result.test_case.question}")
        print(f"  Expected Type: {result.test_case.expected_type}")
        print(f"  Status Code: {result.status_code}")
        print(f"  Response Time: {result.response_time_ms:.1f}ms")
        print(f"  Stream Events: {len(result.stream_events)}")

        if result.classification_type is not None:
            print(f"  Classification Type: {result.classification_type}")
            print(f"  Classification Confidence: {result.classification_confidence}")

        if result.error_message:
            print(f"  Error: {result.error_message}")

    print("\n" + "=" * 60)


def save_report(report: TestReport, output_path: Path | None = None) -> Path:
    """Save report to JSON file."""
    if output_path is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"e2e_report_{timestamp}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)

    return output_path


async def main() -> int:
    """Main entry point."""
    if os.environ.get("SKIP_E2E_TEST") == "1":
        print("E2E tests skipped (SKIP_E2E_TEST=1)")
        return 0

    server_manager = ServerManager()

    try:
        print("Starting server...")
        server_manager.start()

        print("Waiting for server to be healthy...")
        healthy = await server_manager.wait_for_healthy()
        if not healthy:
            print("ERROR: Server failed to start within timeout")
            return 1

        print("Server is healthy, running tests...")
        report = await run_e2e_tests()

        print_report(report)

        report_path = save_report(report)
        print(f"\nReport saved to: {report_path}")

        return 0 if report.failed == 0 else 1

    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 130
    finally:
        print("Stopping server...")
        server_manager.stop()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
