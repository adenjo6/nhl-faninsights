"""add_mvp_tables_and_enhanced_game_fields

Revision ID: 690dd9f73406
Revises: 5bae33282c94
Create Date: 2025-10-22 14:19:20.807981

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '690dd9f73406'
down_revision: Union[str, Sequence[str], None] = '5bae33282c94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Create users table
    op.create_table(
        'users',
        sa.Column('clerk_id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('profile_image_url', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_banned', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('clerk_id'),
    )
    op.create_index(op.f('ix_users_clerk_id'), 'users', ['clerk_id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)

    # Create player_info table (master player table)
    op.create_table(
        'player_info',
        sa.Column('nhl_player_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('position', sa.String(), nullable=True),
        sa.Column('jersey_number', sa.Integer(), nullable=True),
        sa.Column('birthdate', sa.Date(), nullable=True),
        sa.Column('nhl_profile_url', sa.String(), nullable=True),
        sa.Column('headshot_url', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('nhl_player_id'),
    )
    op.create_index(op.f('ix_player_info_nhl_player_id'), 'player_info', ['nhl_player_id'], unique=False)

    # Create player_team_history table
    op.create_table(
        'player_team_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.String(), nullable=False),
        sa.Column('team_name', sa.String(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['player_id'], ['player_info.nhl_player_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_player_team_history_player_id'), 'player_team_history', ['player_id'], unique=False)
    op.create_index(op.f('ix_player_team_history_team_id'), 'player_team_history', ['team_id'], unique=False)
    op.create_index('ix_current_roster', 'player_team_history', ['team_id', 'end_date'], unique=False)
    op.create_index('ix_player_history', 'player_team_history', ['player_id', 'start_date'], unique=False)

    # Create comments table
    op.create_table(
        'comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_flagged', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('deleted_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['game_id'], ['games.game_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.clerk_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.clerk_id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_comments_id'), 'comments', ['id'], unique=False)
    op.create_index(op.f('ix_comments_game_id'), 'comments', ['game_id'], unique=False)
    op.create_index(op.f('ix_comments_user_id'), 'comments', ['user_id'], unique=False)
    op.create_index(op.f('ix_comments_parent_id'), 'comments', ['parent_id'], unique=False)
    op.create_index(op.f('ix_comments_created_at'), 'comments', ['created_at'], unique=False)
    op.create_index('ix_comments_game_created', 'comments', ['game_id', 'created_at'], unique=False)
    op.create_index('ix_comments_flagged', 'comments', ['is_flagged', 'created_at'], unique=False)

    # Create videos table
    op.create_table(
        'videos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('youtube_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('channel_name', sa.String(), nullable=True),
        sa.Column('thumbnail_url', sa.String(), nullable=True),
        sa.Column('video_type', sa.String(), nullable=False),
        sa.Column('goal_time', sa.String(), nullable=True),
        sa.Column('scorer_name', sa.String(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['game_id'], ['games.game_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('game_id', 'youtube_id', name='uq_game_video'),
    )
    op.create_index(op.f('ix_videos_id'), 'videos', ['id'], unique=False)
    op.create_index(op.f('ix_videos_game_id'), 'videos', ['game_id'], unique=False)
    op.create_index(op.f('ix_videos_youtube_id'), 'videos', ['youtube_id'], unique=False)
    op.create_index(op.f('ix_videos_video_type'), 'videos', ['video_type'], unique=False)
    op.create_index('ix_videos_game_type', 'videos', ['game_id', 'video_type'], unique=False)

    # Create quotes table
    op.create_table(
        'quotes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('speaker_name', sa.String(), nullable=False),
        sa.Column('speaker_role', sa.String(), nullable=True),
        sa.Column('speaker_image_url', sa.String(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.game_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_quotes_id'), 'quotes', ['id'], unique=False)
    op.create_index('ix_quotes_game', 'quotes', ['game_id'], unique=False)

    # Create milestones table
    op.create_table(
        'milestones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('player_name', sa.String(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('milestone_type', sa.String(), nullable=False),
        sa.Column('milestone_value', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('achieved', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('current_value', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['player_id'], ['player_info.nhl_player_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['game_id'], ['games.game_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_milestones_id'), 'milestones', ['id'], unique=False)
    op.create_index(op.f('ix_milestones_player_id'), 'milestones', ['player_id'], unique=False)
    op.create_index('ix_milestones_game', 'milestones', ['game_id'], unique=False)
    op.create_index('ix_milestones_player', 'milestones', ['player_id', 'milestone_type'], unique=False)

    # Add new columns to games table
    op.add_column('games', sa.Column('recap_text', sa.Text(), nullable=True))
    op.add_column('games', sa.Column('recap_generated', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('games', sa.Column('summary_line', sa.String(), nullable=True))
    op.add_column('games', sa.Column('basic_stats_fetched', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('games', sa.Column('reddit_fetched', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('games', sa.Column('videos_fetched', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('games', sa.Column('quotes_fetched', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('games', sa.Column('status_updated_at', sa.DateTime(), nullable=True))
    op.add_column('games', sa.Column('completed_at', sa.DateTime(), nullable=True))
    op.add_column('games', sa.Column('archived_at', sa.DateTime(), nullable=True))
    op.add_column('games', sa.Column('standings_snapshot', sa.JSON(), nullable=True))
    op.add_column('games', sa.Column('next_opponent', sa.String(), nullable=True))
    op.add_column('games', sa.Column('next_game_date', sa.DateTime(), nullable=True))
    op.add_column('games', sa.Column('next_game_storyline', sa.String(), nullable=True))

    # Add new index to games table
    op.create_index('ix_games_status_updated', 'games', ['status', 'status_updated_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""

    # Drop index from games
    op.drop_index('ix_games_status_updated', table_name='games')

    # Drop new columns from games table
    op.drop_column('games', 'next_game_storyline')
    op.drop_column('games', 'next_game_date')
    op.drop_column('games', 'next_opponent')
    op.drop_column('games', 'standings_snapshot')
    op.drop_column('games', 'archived_at')
    op.drop_column('games', 'completed_at')
    op.drop_column('games', 'status_updated_at')
    op.drop_column('games', 'quotes_fetched')
    op.drop_column('games', 'videos_fetched')
    op.drop_column('games', 'reddit_fetched')
    op.drop_column('games', 'basic_stats_fetched')
    op.drop_column('games', 'summary_line')
    op.drop_column('games', 'recap_generated')
    op.drop_column('games', 'recap_text')

    # Drop milestones table
    op.drop_index('ix_milestones_player', table_name='milestones')
    op.drop_index('ix_milestones_game', table_name='milestones')
    op.drop_index(op.f('ix_milestones_player_id'), table_name='milestones')
    op.drop_index(op.f('ix_milestones_id'), table_name='milestones')
    op.drop_table('milestones')

    # Drop quotes table
    op.drop_index('ix_quotes_game', table_name='quotes')
    op.drop_index(op.f('ix_quotes_id'), table_name='quotes')
    op.drop_table('quotes')

    # Drop videos table
    op.drop_index('ix_videos_game_type', table_name='videos')
    op.drop_index(op.f('ix_videos_video_type'), table_name='videos')
    op.drop_index(op.f('ix_videos_youtube_id'), table_name='videos')
    op.drop_index(op.f('ix_videos_game_id'), table_name='videos')
    op.drop_index(op.f('ix_videos_id'), table_name='videos')
    op.drop_table('videos')

    # Drop comments table
    op.drop_index('ix_comments_flagged', table_name='comments')
    op.drop_index('ix_comments_game_created', table_name='comments')
    op.drop_index(op.f('ix_comments_created_at'), table_name='comments')
    op.drop_index(op.f('ix_comments_parent_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_user_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_game_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_id'), table_name='comments')
    op.drop_table('comments')

    # Drop player_team_history table
    op.drop_index('ix_player_history', table_name='player_team_history')
    op.drop_index('ix_current_roster', table_name='player_team_history')
    op.drop_index(op.f('ix_player_team_history_team_id'), table_name='player_team_history')
    op.drop_index(op.f('ix_player_team_history_player_id'), table_name='player_team_history')
    op.drop_table('player_team_history')

    # Drop player_info table
    op.drop_index(op.f('ix_player_info_nhl_player_id'), table_name='player_info')
    op.drop_table('player_info')

    # Drop users table
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_clerk_id'), table_name='users')
    op.drop_table('users')
