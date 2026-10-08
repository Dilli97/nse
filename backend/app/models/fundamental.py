from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey, Date, JSON, UniqueConstraint
from app.database import Base
from datetime import datetime, timezone

class FinancialStatement(Base):
    __tablename__ = 'financial_statements'
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), index=True, nullable=False)
    statement_type = Column(String, nullable=False)
    period_type = Column(String, nullable=False)
    reporting_type = Column(String, nullable=False)
    period_end_date = Column(Date, nullable=False)
    publication_date = Column(Date, nullable=True)
    currency = Column(String, default='INR', nullable=False)
    unit = Column(String, default='crores', nullable=False)
    data_json = Column(JSON, nullable=False)
    source_url = Column(String, nullable=True)
    provider = Column(String, nullable=False)
    fetch_timestamp = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint('stock_id', 'statement_type', 'period_type', 'reporting_type', 'period_end_date', name='_fs_unique'),)

class CalculatedRatio(Base):
    __tablename__ = 'calculated_ratios'
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), index=True, nullable=False)
    period_end_date = Column(Date, nullable=False)
    period_type = Column(String, nullable=False)
    ratio_name = Column(String, nullable=False)
    value = Column(Numeric(18,6), nullable=True)
    is_meaningful = Column(Boolean, default=True)
    formula_used = Column(String, nullable=False)
    inputs_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

class ShareholdingPattern(Base):
    __tablename__ = 'shareholding_patterns'
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    quarter_end_date = Column(Date, nullable=False)
    promoter_holding_pct = Column(Numeric(8,4), nullable=True)
    promoter_pledged_pct = Column(Numeric(8,4), nullable=True)
    fii_holding_pct = Column(Numeric(8,4), nullable=True)
    dii_holding_pct = Column(Numeric(8,4), nullable=True)
    public_holding_pct = Column(Numeric(8,4), nullable=True)
    source_url = Column(String, nullable=True)
    provider = Column(String, nullable=False)
    fetch_timestamp = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
