"""timestamp Float to DateTime

Revision ID: 228e6c7c738c
Revises: 5759246d4f
Create Date: 2015-05-21 16:24:24.865537

"""

# revision identifiers, used by Alembic.
revision = '228e6c7c738c'
down_revision = '2cc69d5c53eb'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

from config.parser import prefix_table_name

file_table = prefix_table_name("file")
scan_table = prefix_table_name("scan")
event_table = prefix_table_name("scanEvents")

def upgrade():
    for column in ['timestamp_first_scan', 'timestamp_last_scan']:
        op.execute('ALTER TABLE {0} ALTER COLUMN {1} TYPE TIMESTAMP WITHOUT TIME ZONE USING to_timestamp({1})'.format(file_table, column))
    op.execute('ALTER TABLE "{0}" ALTER COLUMN timestamp TYPE TIMESTAMP WITHOUT TIME ZONE USING to_timestamp(timestamp)'.format(event_table))
    op.execute('ALTER TABLE "{0}" ALTER COLUMN date TYPE TIMESTAMP WITHOUT TIME ZONE USING to_timestamp(date)'.format(scan_table))


def downgrade():
    for column in ['timestamp_first_scan', 'timestamp_last_scan']:
        op.execute('ALTER TABLE {0} ALTER COLUMN {1} TYPE REAL USING extract(epoch from {1})'.format(file_table, column))
    op.execute('ALTER TABLE "{0}" ALTER COLUMN timestamp TYPE REAL USING extract(epoch from timestamp)'.format(event_table))
    op.execute('ALTER TABLE "{0}" ALTER COLUMN date TYPE REAL USING extract(epoch from date)'.format(scan_table))
