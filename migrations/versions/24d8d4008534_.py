"""empty message

Revision ID: 24d8d4008534
Revises: 1057f3f25ff9
Create Date: 2016-04-12 12:11:40.313652

"""

# revision identifiers, used by Alembic.
revision = '24d8d4008534'
down_revision = '1057f3f25ff9'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('addresses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('a_use', postgresql.ENUM('home', 'work', 'temp', 'old', name='address_use'), nullable=True),
    sa.Column('a_type', postgresql.ENUM('postal', 'physical', 'both', name='address_type'), nullable=True),
    sa.Column('line1', sa.Text(), nullable=True),
    sa.Column('line2', sa.Text(), nullable=True),
    sa.Column('line3', sa.Text(), nullable=True),
    sa.Column('city', sa.Text(), nullable=True),
    sa.Column('district', sa.Text(), nullable=True),
    sa.Column('state', sa.Text(), nullable=True),
    sa.Column('postalCode', sa.Text(), nullable=True),
    sa.Column('country', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('organizations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('phone', sa.String(length=40), nullable=True),
    sa.Column('type_id', sa.Integer(), nullable=True),
    sa.Column('partOf_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['partOf_id'], ['organizations.id'], ),
    sa.ForeignKeyConstraint(['type_id'], ['codeable_concepts.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('organization_addresses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('address_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['address_id'], ['addresses.id'], ondelete='cascade'),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('organization_id', 'address_id', name='_observation_address')
    )
    op.create_table('user_organizations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='cascade'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'organization_id', name='_user_organization')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_organizations')
    op.drop_table('organization_addresses')
    op.drop_table('organizations')
    op.drop_table('addresses')
    ### end Alembic commands ###
