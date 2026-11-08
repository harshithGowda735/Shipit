"""Create a disposable table to test Alembic upgrade and downgrade."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_test_migration"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "phase1_migration_smoke",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("label", sa.String(length=50), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("phase1_migration_smoke")
