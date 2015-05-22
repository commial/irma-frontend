"""DB revision creation

Revision ID: 2cc69d5c53eb
Revises:
Create Date: 2015-05-20 13:54:25.433439

"""

# revision identifiers, used by Alembic.
revision = '2cc69d5c53eb'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

from config.parser import prefix_table_name

file_table = prefix_table_name("file")
scan_table = prefix_table_name("scan")
submision_table = prefix_table_name("submission")
tag_table = prefix_table_name("tag")
agent_table = prefix_table_name("fileAgent")
probe_table = prefix_table_name("probeResult")
web_table = prefix_table_name("fileWeb")
event_table = prefix_table_name("scanEvents")
tag_file_table = prefix_table_name("tag_file")
result_file_table = prefix_table_name("probeResult_fileWeb")


def upgrade():
    op.create_table(
        file_table,
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=True),
        sa.Column('sha1', sa.String(length=40), nullable=True),
        sa.Column('md5', sa.String(length=32), nullable=True),
        sa.Column('timestamp_first_scan', sa.Float(precision=2), nullable=False),
        sa.Column('timestamp_last_scan', sa.Float(precision=2), nullable=False),
        sa.Column('size', sa.Integer(), nullable=True),
        sa.Column('path', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sqlite_autoincrement=True
    )
    op.create_index(
        op.f('ix_{}_md5'.format(file_table)),
        file_table,
        ['md5'],
        unique=False
    )
    op.create_index(
        op.f('ix_{}_sha1'.format(file_table)),
        file_table,
        ['sha1'],
        unique=False)
    op.create_index(
        op.f('ix_{}_sha256'.format(file_table)),
        file_table,
        ['sha256'],
        unique=False
    )
    op.create_table(
        scan_table,
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=36), nullable=False),
        sa.Column('date', sa.Integer(), nullable=False),
        sa.Column('ip', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sqlite_autoincrement=True
    )
    op.create_index(
        op.f('ix_{}_external_id'.format(scan_table)),
        scan_table,
        ['external_id'],
        unique=False)
    op.create_table(
        submission_table,
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=36), nullable=False),
        sa.Column('os_name', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('ip', sa.String(), nullable=False),
        sa.Column('date', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sqlite_autoincrement=True
    )
    op.create_index(
        op.f('ix_{}_external_id'.format(submission_table)),
        submission_table,
        ['external_id'],
        unique=False
    )
    op.create_table(
        tag_table,
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sqlite_autoincrement=True
    )
    op.create_table(
        agent_table,
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('submission_path', sa.String(length=255), nullable=False),
        sa.Column('id_file', sa.Integer(), nullable=False),
        sa.Column('id_s', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id_file'], ['{}.id'.format(file_table)], ),
        sa.ForeignKeyConstraint(['id_s'], ['{}.id'.format(submission_table)], ),
        sa.PrimaryKeyConstraint('id'),
        sqlite_autoincrement=True
    )
    op.create_table(
        web_table,
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scan_file_idx', sa.Integer(), nullable=False),
        sa.Column('id_file', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('id_scan', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id_file'], ['{}.id'.format(file_table)], ),
        sa.ForeignKeyConstraint(['id_scan'], ['{}.id'.format(scan_table)], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id_scan', 'scan_file_idx')
    )
    op.create_table(
        probe_table,
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('nosql_id', sa.String(), nullable=True),
        sa.Column('status', sa.Integer(), nullable=True),
        sa.Column('id_file', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['id_file'], ['{}.id'.format(file_table)], ),
        sa.PrimaryKeyConstraint('id'),
        sqlite_autoincrement=True
    )
    op.create_table(
        event_table,
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.Float(precision=2), nullable=False),
        sa.Column('id_scan', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id_scan'], ['{}.id'.format(scan_table)], ),
        sa.PrimaryKeyConstraint('id'),
        sqlite_autoincrement=True
    )
    op.create_index(
        op.f('ix_{}_id_scan'.format(event_table)),
        event_table,
        ['id_scan'],
        unique=False
    )
    op.create_table(
        tag_file_table,
        sa.Column('id_tag', sa.Integer(), nullable=True),
        sa.Column('id_file', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['id_file'], ['{}.id'.format(file_table)], ),
        sa.ForeignKeyConstraint(['id_tag'], ['{}.id'.format(tag_table)], )
    )
    op.create_table(
        result_file_table,
        sa.Column('id_fw', sa.Integer(), nullable=True),
        sa.Column('id_pr', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['id_fw'], ['{}.id'.format(web_table)], ),
        sa.ForeignKeyConstraint(['id_pr'], ['{}.id'.format(probe_table)], )
    )


def downgrade():
    op.drop_table(result_file_table)
    op.drop_table(tag_file_table)
    op.drop_index(op.f('ix_{}_id_scan').format(event_table), table_name=event_table)
    op.drop_table(event_table)
    op.drop_table(probe_table)
    op.drop_table(web_table)
    op.drop_table(agent_table)
    op.drop_table(tag_table)
    op.drop_index(op.f('ix_{}_external_id'.format(submission_table)),
                  table_name=submission_table)
    op.drop_table(submission_table)
    op.drop_index(op.f('ix_{}_external_id'.format(scan_table)), table_name=scan_table)
    op.drop_table(scan_table)
    op.drop_index(op.f('ix_{}_sha256'.format(file_table)), table_name=file_table)
    op.drop_index(op.f('ix_{}_sha1'.format(file_table)), table_name=file_table)
    op.drop_index(op.f('ix_{}_md5'.format(file_table)), table_name=file_table)
    op.drop_table(file_table)
