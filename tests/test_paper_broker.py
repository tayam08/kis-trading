from broker.paper_broker import PaperBroker


def test_paper_broker_buy_order():
    broker = PaperBroker(initial_cash=100_000)
    broker.update_price("005930", 70_000)

    result = broker.buy("005930", 1)

    assert result["status"] == "FILLED"
    assert broker.cash == 30_000
    assert broker.positions["005930"] == 1


def test_paper_broker_rejects_insufficient_cash():
    broker = PaperBroker(initial_cash=50_000)
    broker.update_price("005930", 70_000)

    result = broker.buy("005930", 1)

    assert result["status"] == "REJECTED"
    assert broker.cash == 50_000
    assert broker.positions == {}
