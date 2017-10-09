"""Correct rank of CRV baseline

Revision ID: 9ebdfeb28bef
Revises: a679f493bcdd
Create Date: 2017-10-09 10:16:40.584279

"""
from alembic import op
from sqlalchemy.orm import sessionmaker

from portal.models.questionnaire_bank import QuestionnaireBank

# revision identifiers, used by Alembic.
revision = '9ebdfeb28bef'
down_revision = 'a679f493bcdd'


def upgrade():
    # site_persistence isn't handling small changes - wants to destroy and
    # recreate, which breaks foreign key constraints to existing results, etc.

    # https://github.com/uwcirg/ePROMs-site-config/pull/71 shows the desired
    # rank corrections.

    # On CRV_baseline:
    #    rank questionnaire
    #    0: epic26
    #    1: eproms_add
    #    2: comorb

    desired_order = ['epic26', 'eproms_add', 'comorb']
    Session = sessionmaker()
    bind = op.get_bind()
    session = Session(bind=bind)

    qb = session.query(QuestionnaireBank).filter(
        QuestionnaireBank.name == 'CRV_baseline').one()

    found_order = []
    for q in qb.questionnaires:
        found_order.append(q.name)

    if found_order == desired_order:
        # in correct order, done
        return

    # correct rank collides with existing - move out of way (+100)
    for rank, name in enumerate(desired_order):
        match = [q for q in qb.questionnaires if q.name == name]
        assert len(match) == 1
        match[0].rank = rank + 100

    session.commit()

    # now restore to desired rank
    for rank, name in enumerate(desired_order):
        match = [q for q in qb.questionnaires if q.name == name]
        assert len(match) == 1
        match[0].rank = rank

    session.commit()


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
