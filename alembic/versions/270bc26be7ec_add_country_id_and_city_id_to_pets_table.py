"""Add country_id and city_id to Pets table

Revision ID: 270bc26be7ec
Revises: 7cb244298dc2
Create Date: 2025-05-28 14:23:11.656300

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '270bc26be7ec'
down_revision: Union[str, None] = '7cb244298dc2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pets', sa.Column('counrty_id', sa.Integer(), nullable=True))
    op.add_column('pets', sa.Column('city_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'pets', 'countries', ['counrty_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(None, 'pets', 'cities', ['city_id'], ['id'], ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'pets', type_='foreignkey')
    op.drop_constraint(None, 'pets', type_='foreignkey')
    op.drop_column('pets', 'city_id')
    op.drop_column('pets', 'counrty_id')
    # ### end Alembic commands ###
