"""add performance indexes

Revision ID: 3a1c9f2e8b4d
Revises: 7f5939024c4a
Create Date: 2026-07-10 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a1c9f2e8b4d'
down_revision: Union[str, Sequence[str], None] = '7f5939024c4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Çok günlük veri ile flights/cargo_requests/optimization_results artık
    # binlerce/on binlerce satır içeriyor -- optimizer'ın "status == pending"
    # filtresi, dashboard'un tarih aralığı filtreleri ve senaryo bazlı
    # sorgular bu index'ler olmadan tam tablo taraması yapar.
    op.create_index(op.f('ix_flights_flight_number'), 'flights', ['flight_number'], unique=False)
    op.create_index(op.f('ix_flights_departure_scheduled'), 'flights', ['departure_scheduled'], unique=False)
    op.create_index(op.f('ix_cargo_requests_flight_id'), 'cargo_requests', ['flight_id'], unique=False)
    op.create_index(op.f('ix_cargo_requests_status'), 'cargo_requests', ['status'], unique=False)
    op.create_index(op.f('ix_optimization_results_request_id'), 'optimization_results', ['request_id'], unique=False)
    op.create_index(op.f('ix_optimization_results_scenario_name'), 'optimization_results', ['scenario_name'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_optimization_results_scenario_name'), table_name='optimization_results')
    op.drop_index(op.f('ix_optimization_results_request_id'), table_name='optimization_results')
    op.drop_index(op.f('ix_cargo_requests_status'), table_name='cargo_requests')
    op.drop_index(op.f('ix_cargo_requests_flight_id'), table_name='cargo_requests')
    op.drop_index(op.f('ix_flights_departure_scheduled'), table_name='flights')
    op.drop_index(op.f('ix_flights_flight_number'), table_name='flights')
