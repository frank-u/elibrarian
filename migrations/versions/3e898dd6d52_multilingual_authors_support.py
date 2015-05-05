"""multilingual_authors_support

Revision ID: 3e898dd6d52
Revises: 27c24cd72c1
Create Date: 2015-05-04 23:11:31.083296

"""

# revision identifiers, used by Alembic.
revision = '3e898dd6d52'
down_revision = '27c24cd72c1'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('authors_details_pkey', 'authors_details',
                       type_='primary')
    op.create_primary_key('author_id-lang_pkey', 'authors_details',
                          ['id', 'lang'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('author_id-lang_pkey', 'authors_details',
                       type_='primary')
    op.create_primary_key('authors_details_pkey', 'authors_details', ['id'])
    ### end Alembic commands ###