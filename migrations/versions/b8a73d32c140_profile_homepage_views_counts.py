"""profile homepage: users冗余计数 + 作品/项目浏览记录

Revision ID: b8a73d32c140
Revises: f5e51486cc72
Create Date: 2026-09-04 23:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'b8a73d32c140'
down_revision = 'f5e51486cc72'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 建 work_view_history
    op.create_table(
        'work_view_history',
        sa.Column('id',              sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id',         sa.Integer(), nullable=False, comment='浏览者'),
        sa.Column('work_id',         sa.Integer(), nullable=False, comment='被浏览作品'),
        sa.Column('author_id',       sa.Integer(), nullable=False, comment='作品作者（冗余）'),
        sa.Column('view_count',      sa.Integer(), nullable=False, server_default='1', comment='累计浏览次数'),
        sa.Column('last_viewed_at',  sa.DateTime(), nullable=True,  comment='最近一次浏览时间（排序）'),
        sa.Column('created_at',      sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_work_view_history')),
        sa.UniqueConstraint('user_id', 'work_id', name='uq_user_work_view'),
        sa.ForeignKeyConstraint(['user_id'],   ['users.id'],   name=op.f('fk_work_view_history_user_id_users')),
        sa.ForeignKeyConstraint(['work_id'],   ['works.id'],   name=op.f('fk_work_view_history_work_id_works')),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'],   name=op.f('fk_work_view_history_author_id_users')),
    )
    with op.batch_alter_table('work_view_history', schema=None) as batch_op:
        batch_op.create_index('ix_user_last_view_work',   ['user_id',   'last_viewed_at'], unique=False)
        batch_op.create_index('ix_author_last_view_work', ['author_id', 'last_viewed_at'], unique=False)

    # 2. 建 project_view_history
    op.create_table(
        'project_view_history',
        sa.Column('id',              sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id',         sa.Integer(), nullable=False, comment='浏览者'),
        sa.Column('project_id',      sa.Integer(), nullable=False, comment='被浏览项目'),
        sa.Column('author_id',       sa.Integer(), nullable=False, comment='项目创建者（冗余）'),
        sa.Column('view_count',      sa.Integer(), nullable=False, server_default='1', comment='累计浏览次数'),
        sa.Column('last_viewed_at',  sa.DateTime(), nullable=True,  comment='最近一次浏览时间（排序）'),
        sa.Column('created_at',      sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_project_view_history')),
        sa.UniqueConstraint('user_id', 'project_id', name='uq_user_project_view'),
        sa.ForeignKeyConstraint(['user_id'],    ['users.id'],    name=op.f('fk_project_view_history_user_id_users')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_project_view_history_project_id_projects')),
        sa.ForeignKeyConstraint(['author_id'],  ['users.id'],    name=op.f('fk_project_view_history_author_id_users')),
    )
    with op.batch_alter_table('project_view_history', schema=None) as batch_op:
        batch_op.create_index('ix_user_last_view_project',   ['user_id',   'last_viewed_at'], unique=False)
        batch_op.create_index('ix_author_last_view_project', ['author_id', 'last_viewed_at'], unique=False)

    # 3. users 表加 4 个冗余计数字段（先用 nullable=True + server_default 兼容存量）
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('following_count', sa.Integer(), nullable=False, server_default='0',
                                      comment='我关注的人数'))
        batch_op.add_column(sa.Column('follower_count',  sa.Integer(), nullable=False, server_default='0',
                                      comment='粉丝数'))
        batch_op.add_column(sa.Column('work_count',      sa.Integer(), nullable=False, server_default='0',
                                      comment='作品数（软删除排除）'))
        batch_op.add_column(sa.Column('project_count',   sa.Integer(), nullable=False, server_default='0',
                                      comment='项目数'))

    # 4. 回填 4 个计数（纯 SQL，与后续业务代码保持一致）
    conn = op.get_bind()
    conn.execute(text("""
        UPDATE users u
        SET following_count = COALESCE((SELECT COUNT(*) FROM follows f WHERE f.follower_id = u.id), 0)
    """))
    conn.execute(text("""
        UPDATE users u
        SET follower_count = COALESCE((SELECT COUNT(*) FROM follows f WHERE f.followed_id = u.id), 0)
    """))
    conn.execute(text("""
        UPDATE users u
        SET work_count = COALESCE((SELECT COUNT(*) FROM works w
                                    WHERE w.user_id = u.id AND w.status <> 'deleted'), 0)
    """))
    conn.execute(text("""
        UPDATE users u
        SET project_count = COALESCE((SELECT COUNT(*) FROM projects p WHERE p.user_id = u.id), 0)
    """))


def downgrade():
    # 1. 删 users 新列
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('project_count')
        batch_op.drop_column('work_count')
        batch_op.drop_column('follower_count')
        batch_op.drop_column('following_count')

    # 2. 删浏览表
    op.drop_table('project_view_history')
    op.drop_table('work_view_history')
