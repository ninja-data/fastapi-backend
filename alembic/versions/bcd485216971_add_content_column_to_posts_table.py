"""add content column to posts table

Revision ID: bcd485216971
Revises: 000acdeb5b44
Create Date: 2024-11-27 08:08:55.814104

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bcd485216971'
down_revision: Union[str, None] = '000acdeb5b44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('posts', sa.Column('content', sa.String(), nullable=False))
    pass


def downgrade() -> None:
    op.drop_column('posts', 'content')
    pass
