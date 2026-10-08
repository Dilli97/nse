from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from app.database import Base
from datetime import datetime, timezone

class ResearchReport(Base):
    __tablename__ = 'research_reports'
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    report_type = Column(String, nullable=False)
    generated_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    report_json = Column(JSON, nullable=False)
    report_html = Column(Text, nullable=True)
    generation_method = Column(String, nullable=False)
    llm_model = Column(String, nullable=True)
    data_freshness_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
