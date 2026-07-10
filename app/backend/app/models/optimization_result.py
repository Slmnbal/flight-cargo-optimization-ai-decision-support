from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.database.connection import Base


class OptimizationResult(Base):
    __tablename__ = "optimization_results"

    result_id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_name = Column(String, nullable=False, index=True)
    request_id = Column(Integer, ForeignKey("cargo_requests.request_id"), nullable=False, index=True)
    decision = Column(String, nullable=False)  # accepted / rejected
    revenue = Column(Float, nullable=False)
    # decision="rejected" olduğunda neden reddedildiğini açıklar, örn.:
    # "capacity_exceeded" / "embargo" / "dangerous_goods_restricted" / "priority_capacity_reserved"
    # decision="accepted" için None kalır.
    reason = Column(String, nullable=True)
    run_at = Column(DateTime, default=datetime.utcnow)
