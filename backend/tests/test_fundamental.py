"""Tests for fundamental analysis calculations and ratios."""
from datetime import date
import pytest
from app.models.stock import Stock
from app.models.fundamental import FinancialStatement
from app.models.market_data import LatestQuote
from app.services.fundamental import FundamentalService


def test_fundamental_ratios_and_fcf(db_session, sample_financials_data):
    """Test standard corporate fundamental ratios and explicit FCF formula."""
    stock = db_session.query(Stock).filter(Stock.symbol == "RELIANCE").first()

    # Seed statements from fixture
    for stmt in sample_financials_data["statements"]:
        fs = FinancialStatement(
            stock_id=stock.id,
            statement_type=stmt["statement_type"],
            period_type=stmt["period_type"],
            reporting_type=stmt["reporting_type"],
            period_end_date=date.fromisoformat(stmt["period_end_date"]),
            currency="INR",
            unit="crores",
            data_json=stmt["data"],
            provider="test_fixture",
        )
        db_session.add(fs)

    # Seed quote
    quote = LatestQuote(
        stock_id=stock.id,
        price=2950.0,
        change=15.0,
        change_percent=0.51,
        market_cap=1995000.0,
        data_quality="delayed",
        provider="test",
    )
    db_session.add(quote)
    db_session.commit()

    service = FundamentalService(db_session)
    summary = service.get_fundamental_summary(stock)

    assert summary["symbol"] == "RELIANCE"
    assert summary["is_financial_institution"] is False
    assert len(summary["reporting_periods"]) == 4

    ratios_by_key = {r["key"]: r for r in summary["ratios"]}

    # Operating Margin for 2024: (139158 / 997137) * 100 ≈ 13.96%
    op_margin = ratios_by_key["operating_margin"]
    assert op_margin["is_meaningful"] is True
    assert round(op_margin["value"], 1) == 14.0

    # Net Margin for 2024: (79020 / 997137) * 100 ≈ 7.92%
    net_margin = ratios_by_key["net_margin"]
    assert net_margin["is_meaningful"] is True
    assert round(net_margin["value"], 1) == 7.9

    # ROE for 2024: (79020 / 880450) * 100 ≈ 8.97%
    roe = ratios_by_key["roe"]
    assert roe["is_meaningful"] is True
    assert round(roe["value"], 1) == 9.0

    # Debt-to-Equity: 324622 / 880450 ≈ 0.37
    de = ratios_by_key["debt_to_equity"]
    assert de["is_meaningful"] is True
    assert round(de["value"], 2) == 0.37

    # Free Cash Flow for 2024: 145000 (OCF) - 131000 (Capex) = 14000
    fcf = ratios_by_key["free_cash_flow"]
    assert fcf["is_meaningful"] is True
    assert fcf["value"] == 14000.0

    # 3-Year Revenue CAGR from 2021 (539238) to 2024 (997137)
    # (997137 / 539238) ** (1/3) - 1 ≈ 22.74%
    growth = summary["growth"]
    assert growth["revenue_3y_cagr"] is not None
    assert round(growth["revenue_3y_cagr"], 1) == 22.7


def test_bank_fundamental_handling(db_session):
    """Test that banks/NBFCs do not report industrial Debt/Equity or ROCE as meaningful."""
    bank = db_session.query(Stock).filter(Stock.symbol == "HDFCBANK").first()

    # Seed bank statement
    fs_inc = FinancialStatement(
        stock_id=bank.id,
        statement_type="income",
        period_type="annual",
        reporting_type="consolidated",
        period_end_date=date(2024, 3, 31),
        currency="INR",
        unit="crores",
        data_json={"Total Revenue": 150000.0, "Net Income": 64000.0, "Diluted EPS": 85.0},
        provider="test",
    )
    fs_bs = FinancialStatement(
        stock_id=bank.id,
        statement_type="balance_sheet",
        period_type="annual",
        reporting_type="consolidated",
        period_end_date=date(2024, 3, 31),
        currency="INR",
        unit="crores",
        data_json={"Stockholders Equity": 400000.0, "Total Assets": 3600000.0, "Total Debt": 700000.0},
        provider="test",
    )
    db_session.add_all([fs_inc, fs_bs])
    db_session.commit()

    service = FundamentalService(db_session)
    summary = service.get_fundamental_summary(bank)

    assert summary["is_financial_institution"] is True

    ratios_by_key = {r["key"]: r for r in summary["ratios"]}
    # Debt to Equity and ROCE must be marked not meaningful for banks
    assert ratios_by_key["debt_to_equity"]["is_meaningful"] is False
    assert "banks" in ratios_by_key["debt_to_equity"]["explanation"].lower()

    assert ratios_by_key["roce"]["is_meaningful"] is False


def test_negative_equity_not_meaningful(db_session):
    """Verify that negative equity flags ROE as not meaningful rather than fabricating a result."""
    stock = db_session.query(Stock).filter(Stock.symbol == "RELIANCE").first()

    fs = FinancialStatement(
        stock_id=stock.id,
        statement_type="balance_sheet",
        period_type="annual",
        reporting_type="consolidated",
        period_end_date=date(2024, 3, 31),
        currency="INR",
        unit="crores",
        data_json={"Stockholders Equity": -5000.0, "Total Assets": 10000.0},
        provider="test",
    )
    fs_inc = FinancialStatement(
        stock_id=stock.id,
        statement_type="income",
        period_type="annual",
        reporting_type="consolidated",
        period_end_date=date(2024, 3, 31),
        currency="INR",
        unit="crores",
        data_json={"Net Income": -1000.0, "Total Revenue": 10000.0},
        provider="test",
    )
    db_session.add_all([fs, fs_inc])
    db_session.commit()

    service = FundamentalService(db_session)
    summary = service.get_fundamental_summary(stock)

    ratios_by_key = {r["key"]: r for r in summary["ratios"]}
    roe = ratios_by_key["roe"]
    assert roe["is_meaningful"] is False
    assert roe["value"] is None
    assert "negative" in roe["explanation"].lower()


def test_missing_data_not_treated_as_zero(db_session):
    """Verify that missing balance sheet line items return None instead of 0.0."""
    stock = db_session.query(Stock).filter(Stock.symbol == "RELIANCE").first()

    # Statement with only revenue, no debt or equity
    fs = FinancialStatement(
        stock_id=stock.id,
        statement_type="income",
        period_type="annual",
        reporting_type="consolidated",
        period_end_date=date(2024, 3, 31),
        currency="INR",
        unit="crores",
        data_json={"Total Revenue": 10000.0},
        provider="test",
    )
    db_session.add(fs)
    db_session.commit()

    service = FundamentalService(db_session)
    summary = service.get_fundamental_summary(stock)

    ratios_by_key = {r["key"]: r for r in summary["ratios"]}
    # Debt to equity must be None and not meaningful, not 0.0
    de = ratios_by_key["debt_to_equity"]
    assert de["value"] is None
    assert de["is_meaningful"] is False
