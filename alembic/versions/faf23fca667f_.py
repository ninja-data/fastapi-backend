"""empty message

Revision ID: faf23fca667f
Revises: afde03a36522
Create Date: 2025-01-01 17:18:52.815549

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'faf23fca667f'
down_revision: Union[str, None] = 'afde03a36522'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
