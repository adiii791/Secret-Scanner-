"""add otp_requests and scan_rate_entries tables

Revision ID: a1b2c3d4e5f6
Revises: 92b663a39b74
Create Date: 2026-09-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '92b663a39b74'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'otp_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('identifier', sa.String(length=255), nullable=False),
        sa.Column('otp_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('otp_requests', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_otp_requests_identifier'), ['identifier'], unique=False)

    op.create_table(
        'scan_rate_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_key', sa.String(length=64), nullable=False),
        sa.Column('hit_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('scan_rate_entries', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_scan_rate_entries_client_key'), ['client_key'], unique=False)


def downgrade():
    with op.batch_alter_table('scan_rate_entries', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_scan_rate_entries_client_key'))
    op.drop_table('scan_rate_entries')

    with op.batch_alter_table('otp_requests', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_otp_requests_identifier'))
    op.drop_table('otp_requests')
