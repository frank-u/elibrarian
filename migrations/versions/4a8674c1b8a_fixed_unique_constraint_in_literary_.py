"""fixed unique constraint in literary_works_details

Revision ID: 4a8674c1b8a
Revises: 531bf3c3a95
Create Date: 2015-04-16 21:39:51.153494

"""

# revision identifiers, used by Alembic.
revision = '4a8674c1b8a'
down_revision = '531bf3c3a95'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('lw_lang_unique', 'literary_works_details', ['literary_work_id', 'lang'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('lw_lang_unique', 'literary_works_details', type_='unique')
    ### end Alembic commands ###
