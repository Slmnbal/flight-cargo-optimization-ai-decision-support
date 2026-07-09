from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.database.connection import Base


class OptimizationResult(Base):
    __tablename__ = "optimization_results"

    result_id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_name = Column(String, nullable=False)
    request_id = Column(Integer, ForeignKey("cargo_requests.request_id"), nullable=False)
    decision = Column(String, nullable=False)  # accepted / rejected
    revenue = Column(Float, nullable=False)
    run_at = Column(DateTime, default=datetime.utcnow)
