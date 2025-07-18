"""Upgrade countries table

Revision ID: 7cb244298dc2
Revises: 09623cef9298
Create Date: 2025-05-28 13:51:42.852545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7cb244298dc2'
down_revision: Union[str, None] = '09623cef9298'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cities',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('state_id', sa.Integer(), nullable=False),
    sa.Column('state_code', sa.String(length=255), nullable=False),
    sa.Column('country_id', sa.Integer(), nullable=False),
    sa.Column('country_code', sa.String(length=2), nullable=False),
    sa.Column('latitude', sa.Numeric(precision=10, scale=8), nullable=False),
    sa.Column('longitude', sa.Numeric(precision=11, scale=8), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text("'2014-01-01 12:01:01'"), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('flag', sa.SmallInteger(), server_default=sa.text('1'), nullable=False),
    sa.Column('wikiDataId', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['country_id'], ['countries.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('cities')
    # ### end Alembic commands ###
