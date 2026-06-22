"""add reddit_sentiment column to games

Revision ID: 1ff022067d94
Revises: 96979d8ddd7d
Create Date: 2026-03-22 23:51:16.771799

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1ff022067d94'
down_revision: Union[str, Sequence[str], None] = '96979d8ddd7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('games', sa.Column('reddit_sentiment', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('games', 'reddit_sentiment')
