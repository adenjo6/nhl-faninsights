"""phase1 split reddit pipeline schema

Revision ID: 8f2c1e6b4d7a
Revises: 7e44b2c1d3a9
Create Date: 2026-04-28 00:00:00.000000

Phase 1 of the Reddit sentiment pipeline rewrite.

Adds the schema foundation for splitting the pipeline into separate discovery
and analysis stages:

- reddit_thread_id          : the Reddit Post-Game Thread post ID once found
- reddit_thread_created_at  : when AutoMod posted the PGT (from submission.created_utc)
                              — used by Phase 3 to gate analysis on thread maturity
- reddit_analyzed_at        : when sentiment analysis completed for this game
                              — lets us write "re-analyze rows older than X" queries

Plus one composite index covering the discovery predicate
(status + reddit_thread_id + game_date_utc).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8f2c1e6b4d7a'
down_revision: Union[str, Sequence[str], None] = '7e44b2c1d3a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('games', sa.Column('reddit_thread_id', sa.String(), nullable=True))
    op.add_column('games', sa.Column('reddit_thread_created_at', sa.DateTime(), nullable=True))
    op.add_column('games', sa.Column('reddit_analyzed_at', sa.DateTime(), nullable=True))
    op.create_index(
        'ix_games_reddit_discovery',
        'games',
        ['status', 'reddit_thread_id', 'game_date_utc'],
    )


def downgrade() -> None:
    op.drop_index('ix_games_reddit_discovery', table_name='games')
    op.drop_column('games', 'reddit_analyzed_at')
    op.drop_column('games', 'reddit_thread_created_at')
    op.drop_column('games', 'reddit_thread_id')
