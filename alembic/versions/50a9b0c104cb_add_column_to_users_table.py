"""add column to users table

Revision ID: 50a9b0c104cb
Revises: f05c326eec9f
Create Date: 2024-11-27 08:50:48.528470

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50a9b0c104cb'
down_revision: Union[str, None] = 'f05c326eec9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=False))
    op.create_unique_constraint(None, 'users', ['phone_number'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('users_phone_number_key', 'users', type_='unique')
    op.drop_column('users', 'phone_number')
    # ### end Alembic commands ###
