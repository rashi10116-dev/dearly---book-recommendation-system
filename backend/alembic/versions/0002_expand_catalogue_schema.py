"""Add external_url, retrieved_at and discovery indexes to books

Revision ID: 0002_expand_catalogue_schema
Revises: 0001_initial_schema
Create Date: 2026-11-12 23:48:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0002_expand_catalogue_schema'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add external_url and retrieved_at columns to books
    op.add_column('books', sa.Column('external_url', sa.String(length=500), nullable=True))
    op.add_column('books', sa.Column('retrieved_at', sa.DateTime(), nullable=True, server_default=sa.func.now()))
    
    # Add indexes for efficient provider lookup and title/author matching
    op.create_index(op.f('ix_books_source_provider'), 'books', ['source_provider'], unique=False)
    op.create_index('ix_books_title_author', 'books', ['title', 'author'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_books_title_author', table_name='books')
    op.drop_index(op.f('ix_books_source_provider'), table_name='books')
    op.drop_column('books', 'retrieved_at')
    op.drop_column('books', 'external_url')
