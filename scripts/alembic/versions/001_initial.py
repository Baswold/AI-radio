# Alembic migration script

"""initial migration

Revision ID: 001
Create Date: 2025-08-06
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create sequences
    op.execute("CREATE SEQUENCE IF NOT EXISTS user_id_seq")
    op.execute("CREATE SEQUENCE IF NOT EXISTS media_id_seq")
    op.execute("CREATE SEQUENCE IF NOT EXISTS playlist_id_seq")
    op.execute("CREATE SEQUENCE IF NOT EXISTS playlist_entry_id_seq")
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, server_default=sa.text("nextval('user_id_seq')")),
        sa.Column('username', sa.String(80), unique=True, nullable=False),
        sa.Column('email', sa.String(120), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(128)),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Create media table
    op.create_table(
        'media',
        sa.Column('id', sa.Integer, primary_key=True, server_default=sa.text("nextval('media_id_seq')")),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('size', sa.Integer),
        sa.Column('duration', sa.Float),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('processed_at', sa.DateTime),
        sa.Column('title', sa.String(255)),
        sa.Column('description', sa.String(1000)),
        sa.Column('tags', sa.String(500)),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'))
    )
    
    # Create playlists table
    op.create_table(
        'playlists',
        sa.Column('id', sa.Integer, primary_key=True, server_default=sa.text("nextval('playlist_id_seq')")),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000)),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'))
    )
    
    # Create playlist_entries table
    op.create_table(
        'playlist_entries',
        sa.Column('id', sa.Integer, primary_key=True, server_default=sa.text("nextval('playlist_entry_id_seq')")),
        sa.Column('playlist_id', sa.Integer, sa.ForeignKey('playlists.id'), nullable=False),
        sa.Column('media_id', sa.Integer, sa.ForeignKey('media.id'), nullable=False),
        sa.Column('position', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Create indexes
    op.create_index('idx_media_user', 'media', ['user_id'])
    op.create_index('idx_playlist_user', 'playlists', ['user_id'])
    op.create_index('idx_playlist_entry_playlist', 'playlist_entries', ['playlist_id'])
    op.create_index('idx_playlist_entry_position', 'playlist_entries', ['position'])
    
    # Create view
    op.execute("""
    CREATE OR REPLACE VIEW current_playlist AS
    SELECT 
        m.filename,
        m.title,
        m.duration,
        pe.position
    FROM playlist_entries pe
    JOIN media m ON pe.media_id = m.id
    JOIN playlists p ON pe.playlist_id = p.id
    WHERE p.name = 'current'
    ORDER BY pe.position
    """)

def downgrade():
    # Drop view
    op.execute("DROP VIEW IF EXISTS current_playlist")
    
    # Drop tables
    op.drop_table('playlist_entries')
    op.drop_table('playlists')
    op.drop_table('media')
    op.drop_table('users')
    
    # Drop sequences
    op.execute("DROP SEQUENCE IF EXISTS playlist_entry_id_seq")
    op.execute("DROP SEQUENCE IF EXISTS playlist_id_seq")
    op.execute("DROP SEQUENCE IF EXISTS media_id_seq")
    op.execute("DROP SEQUENCE IF EXISTS user_id_seq")
