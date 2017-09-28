from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from portal.models.user import User


"""empty message

Revision ID: 68c153cf6a02
Revises: d0b40bc8d7e6
Create Date: 2017-09-22 13:51:06.797595

"""

# revision identifiers, used by Alembic.
revision = '68c153cf6a02'
down_revision = 'd0b40bc8d7e6'

Session = sessionmaker()


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    bind = op.get_bind()
    session = Session(bind=bind)

    sysname = '__system__'

    sysuser = session.query(User).filter_by(username=sysname).first()
    if not sysuser:
    	sysuser = User(username=sysname, first_name='System',
                	   last_name='Admin')
        session.add(sysuser)
        session.commit()
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###