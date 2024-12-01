"""update pet table

Revision ID: 9c481672b76b
Revises: 54410bf7eeca
Create Date: 2024-12-01 17:28:32.744149

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c481672b76b'
down_revision: Union[str, None] = '54410bf7eeca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('pets', 'breed_1',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('users', 'phone',
               existing_type=sa.VARCHAR(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'phone',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('pets', 'breed_1',
               existing_type=sa.VARCHAR(),
               nullable=True)
    # ### end Alembic commands ###
