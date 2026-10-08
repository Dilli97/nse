"""Fundamental analysis service.

Calculates key financial ratios, growth rates, CAGRs, valuation metrics,
and cash-flow health from stored financial statements.

Rules:
- Never treat missing values as zero. Missing inputs yield None / "unavailable".
- If equity <= 0 or denominator <= 0 where invalid (e.g. ROE with negative equity),
  the ratio is marked as is_meaningful=False with an explicit explanation.
- Free Cash Flow is explicitly calculated as:
    FCF = Operating Cash Flow - Capital Expenditure (or purchase of PPE).
- CAGR is calculated as:
    CAGR = (End Value / Start Value) ** (1 / years) - 1.
- Financial institutions (Banks, NBFCs, Insurers) are handled with distinct logic,
  noting that industrial leverage metrics like Debt-to-Equity are not meaningful.
- Fundamental scoring provides full transparency: weights, input coverage, and limitations.
"""
from datetime import date
from typing import Any, Dict, List, Optional
import numpy as np
import structlog
from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.models.fundamental import FinancialStatement, CalculatedRatio, ShareholdingPattern
from app.models.market_data import LatestQuote

logger = structlog.get_logger(__name__)

BANK_SECTORS = {"Financial Services", "Banks", "Banking", "NBFC", "Insurance"}


class FundamentalService:
    """Service to process and compute fundamental ratios and performance scores."""

    def __init__(self, db: Session):
        self.db = db

    def get_statements(
        self, stock_id: int, statement_type: Optional[str] = None, period_type: str = "annual"
    ) -> List[FinancialStatement]:
        """Fetch stored statements ordered by period_end_date ascending."""
        query = self.db.query(FinancialStatement).filter(
            FinancialStatement.stock_id == stock_id,
            FinancialStatement.period_type == period_type,
        )
        if statement_type:
            query = query.filter(FinancialStatement.statement_type == statement_type)
        return query.order_by(FinancialStatement.period_end_date.asc()).all()

    def get_fundamental_summary(self, stock: Stock) -> Dict[str, Any]:
        """Generate comprehensive fundamental report with ratios, statements, and score."""
        is_financial = stock.sector in BANK_SECTORS if stock.sector else False

        # Load annual statements
        income_stmts = self.get_statements(stock.id, "income", "annual")
        bs_stmts = self.get_statements(stock.id, "balance_sheet", "annual")
        cf_stmts = self.get_statements(stock.id, "cash_flow", "annual")

        # Load quote for market-based valuation ratios
        quote = self.db.query(LatestQuote).filter(LatestQuote.stock_id == stock.id).first()
        current_price = float(quote.price) if quote and quote.price else None
        market_cap = float(quote.market_cap) if quote and quote.market_cap else None

        # Build year-by-year financial history
        periods = sorted(
            list(
                set(
                    [s.period_end_date.isoformat() for s in income_stmts]
                    + [s.period_end_date.isoformat() for s in bs_stmts]
                    + [s.period_end_date.isoformat() for s in cf_stmts]
                )
            )
        )

        history = self._extract_financial_history(periods, income_stmts, bs_stmts, cf_stmts)

        # Calculate key ratios
        ratios = self._calculate_all_ratios(stock, history, current_price, market_cap, is_financial)

        # Calculate growth rates & CAGRs
        growth = self._calculate_growth_metrics(history)

        # Cash flow consistency
        cf_consistency = self._calculate_cash_flow_consistency(history)

        # Shareholding pattern
        shareholding = (
            self.db.query(ShareholdingPattern)
            .filter(ShareholdingPattern.stock_id == stock.id)
            .order_by(ShareholdingPattern.quarter_end_date.desc())
            .first()
        )
        shareholding_data = None
        if shareholding:
            shareholding_data = {
                "quarter_end_date": shareholding.quarter_end_date.isoformat(),
                "promoter_holding_pct": float(shareholding.promoter_holding_pct) if shareholding.promoter_holding_pct is not None else None,
                "promoter_pledged_pct": float(shareholding.promoter_pledged_pct) if shareholding.promoter_pledged_pct is not None else None,
                "fii_holding_pct": float(shareholding.fii_holding_pct) if shareholding.fii_holding_pct is not None else None,
                "dii_holding_pct": float(shareholding.dii_holding_pct) if shareholding.dii_holding_pct is not None else None,
                "public_holding_pct": float(shareholding.public_holding_pct) if shareholding.public_holding_pct is not None else None,
            }

        # Fundamental Score
        score = self._compute_fundamental_score(ratios, growth, cf_consistency, is_financial)

        return {
            "symbol": stock.symbol,
            "name": stock.name,
            "sector": stock.sector,
            "is_financial_institution": is_financial,
            "currency": "INR",
            "unit": "crores",
            "reporting_periods": periods,
            "ratios": ratios,
            "growth": growth,
            "cash_flow_consistency": cf_consistency,
            "shareholding": shareholding_data,
            "score": score,
            "statements_available": {
                "income": len(income_stmts),
                "balance_sheet": len(bs_stmts),
                "cash_flow": len(cf_stmts),
            },
        }

    def _extract_financial_history(
        self,
        periods: List[str],
        income_stmts: List[FinancialStatement],
        bs_stmts: List[FinancialStatement],
        cf_stmts: List[FinancialStatement],
    ) -> List[Dict[str, Any]]:
        """Consolidate standard line items across periods with exact key mappings."""
        history = []
        inc_map = {s.period_end_date.isoformat(): s.data_json for s in income_stmts}
        bs_map = {s.period_end_date.isoformat(): s.data_json for s in bs_stmts}
        cf_map = {s.period_end_date.isoformat(): s.data_json for s in cf_stmts}

        for p in periods:
            inc = inc_map.get(p, {})
            bs = bs_map.get(p, {})
            cf = cf_map.get(p, {})

            # Revenue extraction
            revenue = self._get_first(inc, ["Total Revenue", "Operating Revenue", "total_revenue", "revenue"])
            op_profit = self._get_first(inc, ["Operating Income", "Operating Profit", "EBIT", "operating_profit"])
            net_income = self._get_first(inc, ["Net Income", "Net Income Common Stockholders", "net_income"])
            interest_exp = self._get_first(inc, ["Interest Expense", "Interest Expense Non Operating", "interest_expense"])
            ebitda = self._get_first(inc, ["EBITDA", "Normalized EBITDA", "ebitda"])
            eps = self._get_first(inc, ["Diluted EPS", "Basic EPS", "eps"])

            # Balance sheet extraction
            total_equity = self._get_first(bs, ["Stockholders Equity", "Total Stockholders Equity", "Common Stock Equity", "total_equity"])
            total_debt = self._get_first(bs, ["Total Debt", "Long Term Debt", "total_debt"])
            cash = self._get_first(bs, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments", "cash"])
            total_assets = self._get_first(bs, ["Total Assets", "total_assets"])
            curr_liabilities = self._get_first(bs, ["Current Liabilities", "Total Current Liabilities", "current_liabilities"])
            shares = self._get_first(bs, ["Share Issued", "Ordinary Shares Number", "shares_outstanding"])

            # Cash flow extraction
            cfo = self._get_first(cf, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities", "operating_cash_flow"])
            capex = self._get_first(cf, ["Capital Expenditure", "Purchase Of PPE", "capital_expenditure"])
            if capex is not None:
                # Capex is often reported as negative in CF statements, take positive magnitude
                capex = abs(capex)

            # FCF = OCF - Capex (formula explicit)
            fcf = None
            if cfo is not None and capex is not None:
                fcf = cfo - capex

            history.append({
                "period": p,
                "revenue": revenue,
                "operating_profit": op_profit,
                "net_income": net_income,
                "interest_expense": interest_exp,
                "ebitda": ebitda,
                "eps": eps,
                "total_equity": total_equity,
                "total_debt": total_debt,
                "cash": cash,
                "total_assets": total_assets,
                "current_liabilities": curr_liabilities,
                "shares_outstanding": shares,
                "operating_cash_flow": cfo,
                "capex": capex,
                "free_cash_flow": fcf,
            })
        return history

    def _get_first(self, data_dict: dict, keys: List[str]) -> Optional[float]:
        """Get the first matching key from dictionary; return float or None. Never returns 0 for missing."""
        if not data_dict or not isinstance(data_dict, dict):
            return None
        for k in keys:
            if k in data_dict and data_dict[k] is not None:
                try:
                    val = float(data_dict[k])
                    if not np.isnan(val):
                        return val
                except (ValueError, TypeError):
                    continue
            # Case-insensitive lookup
            for d_key, d_val in data_dict.items():
                if d_key.lower().replace(" ", "_") == k.lower().replace(" ", "_") and d_val is not None:
                    try:
                        val = float(d_val)
                        if not np.isnan(val):
                            return val
                    except (ValueError, TypeError):
                        continue
        return None

    def _calculate_all_ratios(
        self,
        stock: Stock,
        history: List[Dict[str, Any]],
        current_price: Optional[float],
        market_cap: Optional[float],
        is_financial: bool,
    ) -> List[Dict[str, Any]]:
        """Compute key fundamental ratios for latest available annual period."""
        if not history:
            return []

        latest = history[-1]
        period = latest["period"]
        results = []

        # 1. Operating Margin = Operating Profit / Revenue
        rev = latest["revenue"]
        op = latest["operating_profit"]
        if rev and rev > 0 and op is not None:
            val = round((op / rev) * 100, 2)
            results.append({
                "name": "Operating Margin (%)",
                "key": "operating_margin",
                "value": val,
                "period": period,
                "is_meaningful": True,
                "formula": "(Operating Profit / Revenue) * 100",
                "explanation": "Percentage of revenue left after paying operating expenses.",
            })
        else:
            results.append({
                "name": "Operating Margin (%)",
                "key": "operating_margin",
                "value": None,
                "period": period,
                "is_meaningful": False,
                "formula": "(Operating Profit / Revenue) * 100",
                "explanation": "Revenue or operating profit unavailable.",
            })

        # 2. Net Profit Margin = Net Income / Revenue
        ni = latest["net_income"]
        if rev and rev > 0 and ni is not None:
            val = round((ni / rev) * 100, 2)
            results.append({
                "name": "Net Profit Margin (%)",
                "key": "net_margin",
                "value": val,
                "period": period,
                "is_meaningful": True,
                "formula": "(Net Income / Revenue) * 100",
                "explanation": "Percentage of revenue translated into bottom-line profit.",
            })
        else:
            results.append({
                "name": "Net Profit Margin (%)",
                "key": "net_margin",
                "value": None,
                "period": period,
                "is_meaningful": False,
                "formula": "(Net Income / Revenue) * 100",
                "explanation": "Revenue or net income unavailable.",
            })

        # 3. Return on Equity (ROE) = Net Income / Total Equity
        eq = latest["total_equity"]
        if eq is not None and eq > 0 and ni is not None:
            val = round((ni / eq) * 100, 2)
            results.append({
                "name": "Return on Equity - ROE (%)",
                "key": "roe",
                "value": val,
                "period": period,
                "is_meaningful": True,
                "formula": "(Net Income / Total Equity) * 100",
                "explanation": "Return generated on shareholders' invested equity.",
            })
        elif eq is not None and eq <= 0:
            results.append({
                "name": "Return on Equity - ROE (%)",
                "key": "roe",
                "value": None,
                "period": period,
                "is_meaningful": False,
                "formula": "(Net Income / Total Equity) * 100",
                "explanation": "Not meaningful: Equity is negative or zero.",
            })
        else:
            results.append({
                "name": "Return on Equity - ROE (%)",
                "key": "roe",
                "value": None,
                "period": period,
                "is_meaningful": False,
                "formula": "(Net Income / Total Equity) * 100",
                "explanation": "Equity or net income unavailable.",
            })

        # 4. ROCE = EBIT / Capital Employed
        # Capital Employed = Total Assets - Current Liabilities OR Equity + Debt
        ebit = op or ni
        tot_assets = latest["total_assets"]
        curr_liab = latest["current_liabilities"]
        cap_employed = None
        if tot_assets and curr_liab:
            cap_employed = tot_assets - curr_liab
        elif eq is not None and latest["total_debt"] is not None:
            cap_employed = eq + latest["total_debt"]

        if not is_financial and cap_employed and cap_employed > 0 and ebit is not None:
            val = round((ebit / cap_employed) * 100, 2)
            results.append({
                "name": "Return on Capital Employed - ROCE (%)",
                "key": "roce",
                "value": val,
                "period": period,
                "is_meaningful": True,
                "formula": "(EBIT / (Total Assets - Current Liabilities)) * 100",
                "explanation": "Efficiency of total capital allocation (debt + equity).",
            })
        elif is_financial:
            results.append({
                "name": "Return on Capital Employed - ROCE (%)",
                "key": "roce",
                "value": None,
                "period": period,
                "is_meaningful": False,
                "formula": "EBIT / Capital Employed",
                "explanation": "Not applicable to banks/financial institutions (deposits are operating leverage, not capital).",
            })
        else:
            results.append({
                "name": "Return on Capital Employed - ROCE (%)",
                "key": "roce",
                "value": None,
                "period": period,
                "is_meaningful": False,
                "formula": "EBIT / Capital Employed",
                "explanation": "Capital employed or EBIT unavailable or non-positive.",
            })

        # 5. Debt to Equity = Total Debt / Total Equity
        debt = latest["total_debt"]
        if is_financial:
            results.append({
                "name": "Debt to Equity",
                "key": "debt_to_equity",
                "value": None,
                "period": period,
                "is_meaningful": False,
                "formula": "Total Debt / Total Equity",
                "explanation": "Not meaningful for banks/NBFCs where deposits and borrowings constitute standard operational funding.",
            })
        elif debt is not None and eq and eq > 0:
            val = round(debt / eq, 2)
            results.append({
                "name": "Debt to Equity",
                "key": "debt_to_equity",
                "value": val,
                "period": period,
                "is_meaningful": True,
                "formula": "Total Debt / Total Equity",
                "explanation": "Measure of financial leverage. Lower is typically safer.",
            })
        elif eq is not None and eq <= 0:
            results.append({
                "name": "Debt to Equity",
                "key": "debt_to_equity",
                "value": None,
                "period": period,
                "is_meaningful": False,
                "formula": "Total Debt / Total Equity",
                "explanation": "Not meaningful: Negative or zero equity.",
            })
        else:
            results.append({
                "name": "Debt to Equity",
                "key": "debt_to_equity",
                "value": None,
                "period": period,
                "is_meaningful": False,
                "formula": "Total Debt / Total Equity",
                "explanation": "Debt or equity data unavailable.",
            })

        # 6. Interest Coverage = EBIT / Interest Expense
        inte = latest["interest_expense"]
        if is_financial:
            results.append({
                "name": "Interest Coverage",
                "key": "interest_coverage",
                "value": None,
                "period": period,
                "is_meaningful": False,
                "formula": "EBIT / Interest Expense",
                "explanation": "Not applicable to banks (interest is direct cost of goods sold).",
            })
        elif ebit is not None and inte and inte > 0:
            val = round(ebit / inte, 2)
            results.append({
                "name": "Interest Coverage Ratio",
                "key": "interest_coverage",
                "value": val,
                "period": period,
                "is_meaningful": True,
                "formula": "EBIT / Interest Expense",
                "explanation": "Ability to service interest payments from earnings.",
            })
        elif inte is not None and inte <= 0:
            results.append({
                "name": "Interest Coverage Ratio",
                "key": "interest_coverage",
                "value": None,
                "period": period,
                "is_meaningful": False,
                "formula": "EBIT / Interest Expense",
                "explanation": "Zero or negligible interest expense (essentially debt-free).",
            })
        else:
            results.append({
                "name": "Interest Coverage Ratio",
                "key": "interest_coverage",
                "value": None,
                "period": period,
                "is_meaningful": False,
                "formula": "EBIT / Interest Expense",
                "explanation": "Interest expense or EBIT data unavailable.",
            })

        # 7. Price to Earnings (P/E)
        eps = latest["eps"]
        if current_price and eps and eps > 0:
            val = round(current_price / eps, 2)
            results.append({
                "name": "Price to Earnings (P/E)",
                "key": "pe_ratio",
                "value": val,
                "period": period,
                "is_meaningful": True,
                "formula": "Current Market Price / Annual EPS",
                "explanation": "Valuation relative to annual earnings per share.",
            })
        elif eps is not None and eps <= 0:
            results.append({
                "name": "Price to Earnings (P/E)",
                "key": "pe_ratio",
                "value": None,
                "period": period,
                "is_meaningful": False,
                "formula": "Price / EPS",
                "explanation": "Not meaningful: Earnings per share are negative or zero.",
            })
        else:
            results.append({
                "name": "Price to Earnings (P/E)",
                "key": "pe_ratio",
                "value": None,
                "period": period,
                "is_meaningful": False,
                "formula": "Price / EPS",
                "explanation": "Price or EPS unavailable.",
            })

        # 8. Price to Book (P/B)
        shares = latest["shares_outstanding"]
        bvps = None
        if eq and eq > 0 and shares and shares > 0:
            bvps = eq / shares
        elif eq and eq > 0 and market_cap and current_price and current_price > 0:
            # Implied shares = market_cap / current_price
            implied_shares = market_cap / current_price
            bvps = eq / implied_shares if implied_shares > 0 else None

        if current_price and bvps and bvps > 0:
            val = round(current_price / bvps, 2)
            results.append({
                "name": "Price to Book (P/B)",
                "key": "pb_ratio",
                "value": val,
                "period": period,
                "is_meaningful": True,
                "formula": "Current Market Price / Book Value Per Share",
                "explanation": "Valuation relative to net accounting asset value.",
            })
        elif eq is not None and eq <= 0:
            results.append({
                "name": "Price to Book (P/B)",
                "key": "pb_ratio",
                "value": None,
                "period": period,
                "is_meaningful": False,
                "formula": "Price / Book Value",
                "explanation": "Not meaningful: Book value is negative or zero.",
            })
        else:
            results.append({
                "name": "Price to Book (P/B)",
                "key": "pb_ratio",
                "value": None,
                "period": period,
                "is_meaningful": False,
                "formula": "Price / Book Value",
                "explanation": "Book value per share or price unavailable.",
            })

        # 9. Free Cash Flow
        fcf = latest["free_cash_flow"]
        results.append({
            "name": "Free Cash Flow (FCF)",
            "key": "free_cash_flow",
            "value": round(fcf, 2) if fcf is not None else None,
            "period": period,
            "is_meaningful": fcf is not None,
            "formula": "Operating Cash Flow - Capital Expenditure",
            "explanation": "Cash remaining after sustaining or expanding physical assets.",
        })

        # 10. EV / EBITDA
        cash = latest["cash"] or 0
        ebitda = latest["ebitda"] or op
        if not is_financial and market_cap and debt is not None and ebitda and ebitda > 0:
            ev = market_cap + debt - cash
            val = round(ev / ebitda, 2)
            results.append({
                "name": "EV / EBITDA",
                "key": "ev_ebitda",
                "value": val,
                "period": period,
                "is_meaningful": True,
                "formula": "(Market Cap + Total Debt - Cash) / EBITDA",
                "explanation": "Capital-structure-neutral enterprise valuation multiple.",
            })
        elif is_financial:
            results.append({
                "name": "EV / EBITDA",
                "key": "ev_ebitda",
                "value": None,
                "period": period,
                "is_meaningful": False,
                "formula": "Enterprise Value / EBITDA",
                "explanation": "Not standard for financial institutions.",
            })
        else:
            results.append({
                "name": "EV / EBITDA",
                "key": "ev_ebitda",
                "value": None,
                "period": period,
                "is_meaningful": False,
                "formula": "EV / EBITDA",
                "explanation": "EBITDA, Debt, or Market Cap unavailable.",
            })

        return results

    def _calculate_growth_metrics(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute 1-year YoY, 3-year CAGR, and 5-year CAGR for Revenue and Net Income."""
        if len(history) < 2:
            return {
                "revenue_yoy": None,
                "net_income_yoy": None,
                "revenue_3y_cagr": None,
                "net_income_3y_cagr": None,
                "revenue_5y_cagr": None,
                "net_income_5y_cagr": None,
                "note": "Insufficient annual history (need at least 2 periods for YoY, 4 for 3Y CAGR, 6 for 5Y CAGR)",
            }

        rev_vals = [h["revenue"] for h in history if h["revenue"] is not None]
        ni_vals = [h["net_income"] for h in history if h["net_income"] is not None]

        # YoY
        rev_yoy = None
        if len(rev_vals) >= 2 and rev_vals[-2] > 0:
            rev_yoy = round(((rev_vals[-1] - rev_vals[-2]) / rev_vals[-2]) * 100, 2)

        ni_yoy = None
        if len(ni_vals) >= 2 and ni_vals[-2] > 0:
            ni_yoy = round(((ni_vals[-1] - ni_vals[-2]) / ni_vals[-2]) * 100, 2)

        # 3Y CAGR = (val[-1] / val[-4]) ** (1/3) - 1
        rev_3y_cagr = self._calculate_cagr(rev_vals, 3)
        ni_3y_cagr = self._calculate_cagr(ni_vals, 3)

        # 5Y CAGR = (val[-1] / val[-6]) ** (1/5) - 1
        rev_5y_cagr = self._calculate_cagr(rev_vals, 5)
        ni_5y_cagr = self._calculate_cagr(ni_vals, 5)

        return {
            "revenue_yoy": rev_yoy,
            "net_income_yoy": ni_yoy,
            "revenue_3y_cagr": rev_3y_cagr,
            "net_income_3y_cagr": ni_3y_cagr,
            "revenue_5y_cagr": rev_5y_cagr,
            "net_income_5y_cagr": ni_5y_cagr,
        }

    def _calculate_cagr(self, values: List[float], years: int) -> Optional[float]:
        """Compute compound annual growth rate if sufficient positive baseline data exists."""
        if len(values) < years + 1:
            return None
        start = values[-(years + 1)]
        end = values[-1]
        if start is None or end is None or start <= 0 or end <= 0:
            # Negative or zero baseline breaks geometric CAGR definition
            return None
        try:
            cagr = ((end / start) ** (1.0 / years) - 1.0) * 100
            return round(float(cagr), 2)
        except Exception:
            return None

    def _calculate_cash_flow_consistency(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze cash flow reliability across available statements."""
        fcf_list = [h["free_cash_flow"] for h in history if h["free_cash_flow"] is not None]
        cfo_list = [h["operating_cash_flow"] for h in history if h["operating_cash_flow"] is not None]

        if not cfo_list:
            return {
                "positive_cfo_years": 0,
                "total_cfo_years": 0,
                "positive_fcf_years": 0,
                "total_fcf_years": 0,
                "assessment": "No cash flow statement data available",
            }

        pos_cfo = sum(1 for v in cfo_list if v > 0)
        pos_fcf = sum(1 for v in fcf_list if v > 0)
        total = len(cfo_list)

        if pos_fcf == total and total >= 3:
            assessment = "Excellent: Consistently generated positive Free Cash Flow every year."
        elif pos_cfo == total and total >= 3:
            assessment = "Strong: Consistently generated positive operating cash flow, though Capex fluctuates."
        elif pos_cfo >= total * 0.6:
            assessment = "Moderate: Operating cash generation has been positive in most years."
        else:
            assessment = "Caution: Operating cash generation has been negative or volatile."

        return {
            "positive_cfo_years": pos_cfo,
            "total_cfo_years": total,
            "positive_fcf_years": pos_fcf,
            "total_fcf_years": len(fcf_list),
            "assessment": assessment,
        }

    def _compute_fundamental_score(
        self,
        ratios: List[Dict[str, Any]],
        growth: Dict[str, Any],
        cf_consistency: Dict[str, Any],
        is_financial: bool,
    ) -> Dict[str, Any]:
        """Compute an evidence-based fundamental health score (0-100).

        Weights:
        - Profitability & Return: 25% (ROE, Margins)
        - Solvency & Financial Health: 25% (Debt/Equity, Interest Coverage)
        - Growth Performance: 20% (Revenue & Earnings YoY / CAGR)
        - Cash Flow Strength: 15% (Free Cash Flow, CFO consistency)
        - Valuation Realism: 15% (P/E, P/B)
        """
        ratio_dict = {r["key"]: r["value"] for r in ratios if r.get("is_meaningful") and r.get("value") is not None}

        total_weight = 0.0
        earned_score = 0.0

        # 1. Profitability (Weight: 25)
        prof_sub = 0.0
        prof_avail = 0
        roe = ratio_dict.get("roe")
        if roe is not None:
            prof_avail += 1
            if roe >= 20: prof_sub += 10
            elif roe >= 15: prof_sub += 8
            elif roe >= 10: prof_sub += 5
            elif roe > 0: prof_sub += 2

        op_margin = ratio_dict.get("operating_margin")
        if op_margin is not None:
            prof_avail += 1
            if op_margin >= 20: prof_sub += 10
            elif op_margin >= 12: prof_sub += 7
            elif op_margin >= 5: prof_sub += 4

        net_margin = ratio_dict.get("net_margin")
        if net_margin is not None:
            prof_avail += 1
            if net_margin >= 15: prof_sub += 5
            elif net_margin >= 8: prof_sub += 3
            elif net_margin > 0: prof_sub += 1

        if prof_avail > 0:
            earned_score += (prof_sub / (prof_avail * 10)) * 25.0
            total_weight += 25.0

        # 2. Solvency (Weight: 25)
        if not is_financial:
            solv_sub = 0.0
            solv_avail = 0
            de = ratio_dict.get("debt_to_equity")
            if de is not None:
                solv_avail += 1
                if de <= 0.3: solv_sub += 15
                elif de <= 0.8: solv_sub += 10
                elif de <= 1.5: solv_sub += 5

            ic = ratio_dict.get("interest_coverage")
            if ic is not None:
                solv_avail += 1
                if ic >= 5.0: solv_sub += 10
                elif ic >= 2.5: solv_sub += 6
                elif ic >= 1.2: solv_sub += 2

            if solv_avail > 0:
                earned_score += (solv_sub / 25.0) * 25.0
                total_weight += 25.0
        else:
            # For banks, solvency is assessed via ROE stability rather than industrial D/E
            if roe is not None:
                earned_score += min(25.0, (roe / 15.0) * 25.0)
                total_weight += 25.0

        # 3. Growth (Weight: 20)
        growth_sub = 0.0
        growth_avail = 0
        rev_grow = growth.get("revenue_3y_cagr") or growth.get("revenue_yoy")
        if rev_grow is not None:
            growth_avail += 1
            if rev_grow >= 15: growth_sub += 10
            elif rev_grow >= 8: growth_sub += 6
            elif rev_grow > 0: growth_sub += 3

        ni_grow = growth.get("net_income_3y_cagr") or growth.get("net_income_yoy")
        if ni_grow is not None:
            growth_avail += 1
            if ni_grow >= 15: growth_sub += 10
            elif ni_grow >= 8: growth_sub += 6
            elif ni_grow > 0: growth_sub += 3

        if growth_avail > 0:
            earned_score += (growth_sub / 20.0) * 20.0
            total_weight += 20.0

        # 4. Cash Flow (Weight: 15)
        cfo_tot = cf_consistency.get("total_cfo_years", 0)
        if cfo_tot > 0:
            cfo_pos = cf_consistency.get("positive_cfo_years", 0)
            fcf_pos = cf_consistency.get("positive_fcf_years", 0)
            earned_score += ((cfo_pos + fcf_pos) / (cfo_tot * 2)) * 15.0
            total_weight += 15.0

        # 5. Valuation (Weight: 15)
        pe = ratio_dict.get("pe_ratio")
        if pe is not None:
            val_sub = 0.0
            if 10 <= pe <= 25: val_sub = 15.0
            elif 25 < pe <= 40: val_sub = 10.0
            elif pe < 10: val_sub = 8.0  # Could be value trap
            else: val_sub = 4.0  # High valuation
            earned_score += val_sub
            total_weight += 15.0

        coverage_pct = round((total_weight / 100.0) * 100, 1)
        final_score = round((earned_score / total_weight) * 100, 1) if total_weight > 0 else None

        rating = "Neutral"
        if final_score is not None:
            if final_score >= 75: rating = "Strong Fundamental Quality"
            elif final_score >= 55: rating = "Satisfactory Quality"
            elif final_score >= 40: rating = "Moderate / Mixed Fundamentals"
            else: rating = "Weak / Vulnerable Financials"

        return {
            "score": final_score,
            "rating": rating,
            "data_coverage_percent": coverage_pct,
            "weights": {
                "profitability": "25%",
                "solvency": "25%",
                "growth": "20%",
                "cash_flow": "15%",
                "valuation": "15%",
            },
            "limitations": [
                "Score is purely backward-looking and derived from reported past financials.",
                "Does not forecast future regulatory, management, or economic shifts.",
                "Bank/NBFC models omit traditional industrial Debt-to-Equity and Capex metrics.",
                f"Evaluation is based on {coverage_pct}% available model parameters.",
            ],
        }
