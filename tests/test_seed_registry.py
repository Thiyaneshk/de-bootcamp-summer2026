from unittest.mock import patch

from scripts.seed_registry import seed


def test_seed_inserts_expected_instruments():
    captured = []

    def fake_add_instrument(**kwargs):
        captured.append(kwargs)
        return {"symbol": kwargs["symbol"]}

    with patch("scripts.seed_registry.add_instrument", side_effect=fake_add_instrument):
        result = seed()

    assert result["inserted"] == len(captured)
    assert result["inserted"] > 0
    assert any(
        item["symbol"] == "^NSEI" and item["instrument_type"] == "index"
        for item in captured
    )
    assert any(
        item["symbol"] == "AAPL" and item["exchange"] == "NASDAQ" for item in captured
    )
