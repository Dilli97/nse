"""Tests for report generation and security/authentication."""
from datetime import date, datetime, timezone
import pytest
from fastapi import HTTPException
from app.models.stock import Stock
from app.models.market_data import DailyCandle, LatestQuote
from app.models.fundamental import FinancialStatement
from app.services.reports import ReportService
from app.auth import verify_api_key
import os


def test_end_to_end_report_generation(db_session, sample_candles_data, sample_financials_data):
    """Verify end-to-end flow from stored data to complete evidence-based report."""
    stock = db_session.query(Stock).filter(Stock.symbol == "RELIANCE").first()

    # 1. Ingest candles
    for c in sample_candles_data:
        dc = DailyCandle(
            stock_id=stock.id,
            date=date.fromisoformat(c["date"]),
            open=c["open"],
            high=c["high"],
            low=c["low"],
            close=c["close"],
            volume=c["volume"],
            is_adjusted=False,
            provider="fixture",
            fetch_timestamp=datetime.now(timezone.utc),
        )
        db_session.add(dc)

    # 2. Ingest financials
    for s in sample_financials_data["statements"]:
        fs = FinancialStatement(
            stock_id=stock.id,
            statement_type=s["statement_type"],
            period_type=s["period_type"],
            reporting_type=s["reporting_type"],
            period_end_date=date.fromisoformat(s["period_end_date"]),
            currency="INR",
            unit="crores",
            data_json=s["data"],
            provider="fixture",
        )
        db_session.add(fs)

    # 3. Ingest quote
    quote = LatestQuote(
        stock_id=stock.id,
        price=2650.0,
        change=25.0,
        change_percent=0.95,
        market_cap=1790000.0,
        data_quality="delayed",
        provider="yahoo",
        fetch_timestamp=datetime.now(timezone.utc),
    )
    db_session.add(quote)
    db_session.commit()

    # 4. Generate report
    report_svc = ReportService(db_session)
    report = report_svc.generate_report(stock)

    assert report["symbol"] == "RELIANCE"
    assert report["generation_method"] == "template"
    assert "sections" in report
    assert len(report["sections"]) >= 7

    section_titles = [s["title"] for s in report["sections"]]
    assert "Business Overview & Security Profile" in section_titles
    assert "Market Snapshot & Data Provenance" in section_titles
    assert "Technical Indicator Observations" in section_titles
    assert "Fundamental Performance & Ratios" in section_titles
    assert "Evidence-Based Scenario Analysis" in section_titles
    assert "Catalysts and Material Risks" in section_titles
    assert "Data Limitations & Analytical Disclaimers" in section_titles

    # Verify scenario analysis contains explicit targets
    scenario_sec = next(s for s in report["sections"] if "Scenario Analysis" in s["title"])
    assert "Bull Scenario" in scenario_sec["content"]
    assert "Bear Scenario" in scenario_sec["content"]


def test_auth_verification(monkeypatch):
    """Test API key verification when auth is enabled and disabled."""
    # When auth is disabled (default in local MVP), any request passes
    monkeypatch.setenv("AUTH_ENABLED", "false")
    assert verify_api_key(x_api_key=None, authorization=None) is True

    # When auth is enabled with a secret token
    monkeypatch.setattr("app.auth.REQUIRE_AUTH", True)
    monkeypatch.setattr("app.auth.AUTH_TOKEN", "supersecret123")

    # Matching header passes
    assert verify_api_key(x_api_key="supersecret123", authorization=None) is True
    assert verify_api_key(x_api_key=None, authorization="Bearer supersecret123") is True

    # Wrong or missing header raises 401
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key(x_api_key="wrong_key", authorization=None)
    assert exc_info.value.status_code == 401
