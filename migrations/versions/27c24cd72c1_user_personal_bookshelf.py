"""user personal bookshelf

Revision ID: 27c24cd72c1
Revises: 4a8674c1b8a
Create Date: 2015-04-20 20:46:20.702185

"""

# revision identifiers, used by Alembic.
revision = '27c24cd72c1'
down_revision = '4a8674c1b8a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users_personal_library',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('literary_work_id', sa.Integer(), nullable=False),
    sa.Column('plan_to_read', sa.Boolean(), nullable=False),
    sa.Column('read_flag', sa.Boolean(), nullable=False),
    sa.Column('read_progress', sa.Integer(), nullable=True),
    sa.Column('read_date', sa.Date(), nullable=True),
    sa.Column('rating', sa.Integer(), nullable=True),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['literary_work_id'], ['literary_works.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['auth_users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'literary_work_id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users_personal_library')
    ### end Alembic commands ###
