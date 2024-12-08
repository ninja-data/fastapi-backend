"""add new columns to a users table

Revision ID: e777f0b08463
Revises: f05c326eec9f
Create Date: 2024-11-28 23:12:22.304927

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e777f0b08463'
down_revision: Union[str, None] = 'f05c326eec9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('surname', sa.String(), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(), nullable=True))
    op.add_column('users', sa.Column('profile_picture', sa.String(), nullable=True))
    op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('location', sa.String(), nullable=True))
    op.add_column('users', sa.Column('date_of_birth', sa.Date(), nullable=True))
    op.add_column('users', sa.Column('gender', sa.String(length=1), nullable=True))
    op.add_column('users', sa.Column('role', sa.String(), nullable=True))
    op.add_column('users', sa.Column('status', sa.String(), nullable=True))
    op.add_column('users', sa.Column('last_login', sa.TIMESTAMP(), nullable=True))
    op.add_column('users', sa.Column('two_factor_enabled', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('is_premium', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('premium_expires_at', sa.TIMESTAMP(), nullable=True))
    op.create_unique_constraint(None, 'users', ['phone'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='unique')
    op.drop_column('users', 'premium_expires_at')
    op.drop_column('users', 'is_premium')
    op.drop_column('users', 'two_factor_enabled')
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'status')
    op.drop_column('users', 'role')
    op.drop_column('users', 'gender')
    op.drop_column('users', 'date_of_birth')
    op.drop_column('users', 'location')
    op.drop_column('users', 'bio')
    op.drop_column('users', 'profile_picture')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'surname')
    op.drop_column('users', 'name')
    # ### end Alembic commands ###
