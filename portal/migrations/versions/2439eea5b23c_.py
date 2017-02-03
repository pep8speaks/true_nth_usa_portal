"""empty message

Revision ID: 2439eea5b23c
Revises: 577ad345788e
Create Date: 2015-11-23 14:04:45.572638

"""

# revision identifiers, used by Alembic.
revision = '2439eea5b23c'
down_revision = '577ad345788e'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('questionnaire_responses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('document', postgresql.JSONB(), nullable=True),
    sa.Column('status', postgresql.ENUM('in-progress', 'completed', name='questionnaire_response_statuses'), nullable=True),
    sa.Column('authored', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('questionnaire_responses')
    ### end Alembic commands ###