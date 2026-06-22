"""phase0 reset broken reddit sentiment stubs

Revision ID: 7e44b2c1d3a9
Revises: 1ff022067d94
Create Date: 2026-04-28 00:00:00.000000

Phase 0 of the Reddit sentiment pipeline rewrite.

Background: the previous job marked a game as `reddit_fetched=true` and stored a
"quiet" stub in `reddit_sentiment` whenever discovery returned no comments. Discovery
itself was broken (search query used team abbreviations that never appear in real
r/SanJoseSharks PGT titles), so essentially every Sharks game ended up with a stub
masquerading as analyzed data.

This migration unsticks those rows so the rewritten pipeline (Phase 2 onward) can
re-process them. Real analyzed rows (non-stub `summary`) are left alone.
"""
from typing import Sequence, Union

from alembic import op


revision: str = '7e44b2c1d3a9'
down_revision: Union[str, Sequence[str], None] = '1ff022067d94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE games
        SET reddit_fetched = false,
            reddit_sentiment = NULL
        WHERE reddit_fetched = true
          AND (
              reddit_sentiment IS NULL
              OR reddit_sentiment->>'summary' = 'No Reddit game thread found.'
          );
        """
    )


def downgrade() -> None:
    # No-op: the data we removed was intentionally-fake stubs and cannot be reconstructed.
    pass
