"""user authentication and authorization support tables

Revision ID: 53709fe8e8e
Revises: 4d84e50d8b4
Create Date: 2015-04-14 21:40:32.101540

"""

# revision identifiers, used by Alembic.
revision = '53709fe8e8e'
down_revision = '4d84e50d8b4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('auth_roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('default', sa.Boolean(), nullable=True),
    sa.Column('permissions', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_auth_roles_default'), 'auth_roles', ['default'], unique=False)
    op.create_table('auth_users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=64), nullable=True),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('confirmed', sa.Boolean(), nullable=True),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('preferred_lang', sa.String(length=3), nullable=True),
    sa.Column('member_since', sa.DateTime(), nullable=True),
    sa.Column('last_seen', sa.DateTime(), nullable=True),
    sa.Column('avatar_hash', sa.String(length=32), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['auth_roles.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_auth_users_email'), 'auth_users', ['email'], unique=True)
    op.create_index(op.f('ix_auth_users_username'), 'auth_users', ['username'], unique=True)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_auth_users_username'), table_name='auth_users')
    op.drop_index(op.f('ix_auth_users_email'), table_name='auth_users')
    op.drop_table('auth_users')
    op.drop_index(op.f('ix_auth_roles_default'), table_name='auth_roles')
    op.drop_table('auth_roles')
    ### end Alembic commands ###
