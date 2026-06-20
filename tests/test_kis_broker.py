from unittest.mock import MagicMock, patch

import pytest

from broker.kis_broker import KISAPIError, KISBroker


@pytest.fixture
def kis_env(monkeypatch):
    monkeypatch.setenv("KIS_APP_KEY", "test_key")
    monkeypatch.setenv("KIS_APP_SECRET", "test_secret")
    monkeypatch.setenv("KIS_ACCOUNT_NO", "12345678-01")
    monkeypatch.setenv("KIS_BASE_URL", "https://openapivts.koreainvestment.com:29443")


def _mock_response(json_data, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data
    response.text = str(json_data)
    return response


def test_init_parses_account_number_and_detects_mock_server(kis_env):
    broker = KISBroker()

    assert broker.cano == "12345678"
    assert broker.acnt_prdt_cd == "01"
    assert broker.is_mock is True


def test_init_requires_all_credentials(monkeypatch):
    monkeypatch.delenv("KIS_APP_KEY", raising=False)

    with pytest.raises(ValueError):
        KISBroker()


@patch("broker.kis_broker.requests.post")
def test_authenticate_caches_token(mock_post, kis_env):
    mock_post.return_value = _mock_response({"access_token": "abc123", "expires_in": 86400})

    broker = KISBroker()
    token1 = broker.authenticate()
    token2 = broker.authenticate()

    assert token1 == "abc123"
    assert token2 == "abc123"
    assert mock_post.call_count == 1


@patch("broker.kis_broker.requests.get")
@patch("broker.kis_broker.requests.post")
def test_get_current_price(mock_post, mock_get, kis_env):
    mock_post.return_value = _mock_response({"access_token": "abc123", "expires_in": 86400})
    mock_get.return_value = _mock_response({"rt_cd": "0", "output": {"stck_prpr": "72500"}})

    broker = KISBroker()
    price = broker.get_current_price("005930")

    assert price == 72500.0


@patch("broker.kis_broker.requests.get")
@patch("broker.kis_broker.requests.post")
def test_get_balance(mock_post, mock_get, kis_env):
    mock_post.return_value = _mock_response({"access_token": "abc123", "expires_in": 86400})
    mock_get.return_value = _mock_response({
        "rt_cd": "0",
        "output1": [{"pdno": "005930", "hldg_qty": "3"}],
        "output2": [{"dnca_tot_amt": "500000", "scts_evlu_amt": "220000", "tot_evlu_amt": "720000"}],
    })

    broker = KISBroker()
    balance = broker.get_balance()

    assert balance["cash"] == 500000.0
    assert balance["positions"] == {"005930": 3}
    assert balance["total_equity"] == 720000.0


@patch("broker.kis_broker.requests.post")
def test_buy_sends_order_with_hashkey(mock_post, kis_env):
    def post_side_effect(url, **kwargs):
        if "tokenP" in url:
            return _mock_response({"access_token": "abc123", "expires_in": 86400})
        if "hashkey" in url:
            return _mock_response({"HASH": "hashed"})
        return _mock_response({
            "rt_cd": "0",
            "msg1": "order accepted",
            "output": {"ODNO": "1234", "ORD_TMD": "101500"},
        })

    mock_post.side_effect = post_side_effect

    broker = KISBroker()
    result = broker.buy("005930", 1)

    assert result["status"] == "FILLED"
    assert result["side"] == "BUY"
    assert result["mode"] == "MOCK"
    assert result["order_no"] == "1234"


@patch("broker.kis_broker.requests.post")
def test_parse_response_raises_on_api_error(mock_post, kis_env):
    mock_post.return_value = _mock_response({"rt_cd": "1", "msg_cd": "EGW00123", "msg1": "invalid key"})

    broker = KISBroker()

    with pytest.raises(KISAPIError):
        broker.authenticate()
