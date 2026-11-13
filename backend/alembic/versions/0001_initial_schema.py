"""Initial DEARLY database schema with PostgreSQL compatibility

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-11-12 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # User Preferences table
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('favorite_genres', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('favorite_tropes', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('favorite_themes', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('preferred_writing_style', sa.String(length=100), nullable=True),
        sa.Column('preferred_pacing', sa.String(length=50), nullable=True),
        sa.Column('preferred_emotional_tone', sa.String(length=50), nullable=True),
        sa.Column('preferred_book_length', sa.String(length=50), nullable=True),
        sa.Column('favorite_authors', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('disliked_elements', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('reading_difficulty', sa.String(length=50), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_preferences_id'), 'user_preferences', ['id'], unique=False)
    op.create_index(op.f('ix_user_preferences_user_id'), 'user_preferences', ['user_id'], unique=True)

    # Books table
    op.create_table(
        'books',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True, server_default=''),
        sa.Column('genre', sa.String(length=100), nullable=True, server_default='General'),
        sa.Column('subgenre', sa.String(length=100), nullable=True),
        sa.Column('tropes', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('themes', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('writing_style', sa.String(length=100), nullable=True),
        sa.Column('pacing', sa.String(length=50), nullable=True),
        sa.Column('emotional_tone', sa.String(length=50), nullable=True),
        sa.Column('book_length_category', sa.String(length=50), nullable=True),
        sa.Column('pages', sa.Integer(), nullable=True),
        sa.Column('publication_year', sa.Integer(), nullable=True),
        sa.Column('cover_image', sa.String(length=500), nullable=True),
        sa.Column('isbn', sa.String(length=50), nullable=True),
        sa.Column('isbn_10', sa.String(length=20), nullable=True),
        sa.Column('isbn_13', sa.String(length=20), nullable=True),
        sa.Column('publisher', sa.String(length=255), nullable=True),
        sa.Column('categories', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('source_provider', sa.String(length=50), nullable=True),
        sa.Column('external_id', sa.String(length=100), nullable=True),
        sa.Column('popularity_score', sa.Float(), nullable=True, server_default='50.0'),
        sa.Column('average_rating', sa.Float(), nullable=True, server_default='4.0'),
        sa.Column('ratings_count', sa.Integer(), nullable=True, server_default='50'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_books_id'), 'books', ['id'], unique=False)
    op.create_index(op.f('ix_books_title'), 'books', ['title'], unique=False)
    op.create_index(op.f('ix_books_author'), 'books', ['author'], unique=False)
    op.create_index(op.f('ix_books_genre'), 'books', ['genre'], unique=False)
    op.create_index(op.f('ix_books_isbn'), 'books', ['isbn'], unique=False)
    op.create_index(op.f('ix_books_isbn_10'), 'books', ['isbn_10'], unique=False)
    op.create_index(op.f('ix_books_isbn_13'), 'books', ['isbn_13'], unique=False)
    op.create_index(op.f('ix_books_external_id'), 'books', ['external_id'], unique=False)

    # Reading Entries table
    op.create_table(
        'reading_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='want_to_read'),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('review', sa.Text(), nullable=True),
        sa.Column('liked_elements', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('disliked_elements', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('favorite_tropes_themes', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'book_id', name='uq_user_book_reading')
    )
    op.create_index(op.f('ix_reading_entries_id'), 'reading_entries', ['id'], unique=False)
    op.create_index(op.f('ix_reading_entries_book_id'), 'reading_entries', ['book_id'], unique=False)
    op.create_index(op.f('ix_reading_entries_user_id'), 'reading_entries', ['user_id'], unique=False)

def downgrade() -> None:
    op.drop_table('reading_entries')
    op.drop_table('books')
    op.drop_table('user_preferences')
    op.drop_table('users')

