import requests

from DaiShanSQL.SQL.sql_utils import MySQLManager


class _FakeResponse:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def test_request_api_sql_returns_payload_when_success(monkeypatch):
    manager = MySQLManager()
    manager.api_url_ds = "http://example.test/sql"

    def _fake_post(url, json, timeout):
        assert url == manager.api_url_ds
        assert json == {"sql": "SELECT 1"}
        assert timeout == manager.request_timeout
        return _FakeResponse(
            status_code=200,
            payload={"code": 200, "msg": "ok", "data": [{"X": 1}]},
        )

    monkeypatch.setattr("DaiShanSQL.SQL.sql_utils.requests.post", _fake_post)

    result = manager.request_api_sql("SELECT 1")

    assert result["code"] == 200
    assert result["msg"] == "ok"
    assert result["data"] == [{"X": 1}]


def test_request_api_sql_wraps_list_payload(monkeypatch):
    manager = MySQLManager()
    manager.api_url_ds = "http://example.test/sql"

    def _fake_post(url, json, timeout):
        return _FakeResponse(status_code=200, payload=[{"X": 1}])

    monkeypatch.setattr("DaiShanSQL.SQL.sql_utils.requests.post", _fake_post)

    result = manager.request_api_sql("SELECT 1")

    assert result["code"] == 200
    assert result["data"] == [{"X": 1}]


def test_request_api_sql_returns_structured_error_on_request_exception(monkeypatch):
    manager = MySQLManager()
    manager.api_url_ds = "http://example.test/sql"

    def _fake_post(url, json, timeout):
        raise requests.RequestException("network down")

    monkeypatch.setattr("DaiShanSQL.SQL.sql_utils.requests.post", _fake_post)

    result = manager.request_api_sql("SELECT 1")

    assert result["code"] == 500
    assert result["data"] == []
    assert "network down" in result["error"]


def test_request_api_sql_returns_structured_error_on_invalid_json(monkeypatch):
    manager = MySQLManager()
    manager.api_url_ds = "http://example.test/sql"

    def _fake_post(url, json, timeout):
        return _FakeResponse(
            status_code=502,
            payload=ValueError("invalid json"),
            text="gateway error",
        )

    monkeypatch.setattr("DaiShanSQL.SQL.sql_utils.requests.post", _fake_post)

    result = manager.request_api_sql("SELECT 1")

    assert result["code"] == 502
    assert result["data"] == []
    assert "invalid json response" in result["msg"]
    assert result["response_text"] == "gateway error"


def test_request_api_sql_returns_error_when_url_missing():
    manager = MySQLManager()
    manager.api_url_ds = ""

    result = manager.request_api_sql("SELECT 1")

    assert result["code"] == 500
    assert result["data"] == []
    assert "not configured" in result["msg"]
