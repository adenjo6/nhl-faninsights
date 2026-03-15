"""split videos_fetched into highlights and professor_hockey flags

Revision ID: 96979d8ddd7d
Revises: 690dd9f73406
Create Date: 2026-03-14 21:32:48.437374

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96979d8ddd7d'
down_revision: Union[str, Sequence[str], None] = '690dd9f73406'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('games', sa.Column('highlights_fetched', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('games', sa.Column('professor_hockey_fetched', sa.Boolean(), server_default='false', nullable=False))
    # Copy existing videos_fetched value to both new columns
    op.execute("UPDATE games SET highlights_fetched = videos_fetched, professor_hockey_fetched = videos_fetched")
    op.drop_column('games', 'videos_fetched')


def downgrade() -> None:
    op.add_column('games', sa.Column('videos_fetched', sa.Boolean(), server_default='false', nullable=False))
    op.execute("UPDATE games SET videos_fetched = highlights_fetched AND professor_hockey_fetched")
    op.drop_column('games', 'highlights_fetched')
    op.drop_column('games', 'professor_hockey_fetched')
