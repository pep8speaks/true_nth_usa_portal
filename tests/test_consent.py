"""Unit test module for user consent"""
from dateutil import parser
from flask_webtest import SessionScope
import json

from portal.extensions import db
from portal.models.audit import Audit
from portal.models.organization import Organization
from portal.models.user_consent import UserConsent
from tests import TestCase, TEST_USER_ID


class TestUserConsent(TestCase):
    url = 'http://fake.com?arg=critical'

    def test_user_consent(self):
        org1, org2 = [org for org in Organization.query.filter(
            Organization.id > 0).limit(2)]

        audit = Audit(user_id=TEST_USER_ID)
        uc1 = UserConsent(organization=org1, agreement_url=self.url,
                          audit=audit)
        uc2 = UserConsent(organization=org2, agreement_url=self.url,
                          audit=audit)
        self.test_user._consents.append(uc1)
        self.test_user._consents.append(uc2)
        with SessionScope(db):
            db.session.commit()
        self.test_user = db.session.merge(self.test_user)
        self.login()
        rv = self.client.get('/api/user/{}/consent'.format(TEST_USER_ID))
        self.assert200(rv)
        self.assertEquals(len(rv.json['consent_agreements']), 2)

    def test_post_user_consent(self):
        org1 = Organization.query.filter(Organization.id > 0).first()
        data = {'organization_id': org1.id, 'agreement_url': self.url}

        self.login()
        rv = self.client.post('/api/user/{}/consent'.format(TEST_USER_ID),
                          content_type='application/json',
                          data=json.dumps(data))
        self.assert200(rv)
        self.assertEqual(self.test_user.valid_consents.count(), 1)
        self.assertEqual(self.test_user.valid_consents[0].organization_id,
                         org1.id)

    def test_post_user_consent_dates(self):
        org1 = Organization.query.filter(Organization.id > 0).first()
        acceptance_date = "2007-10-30"
        data = {'organization_id': org1.id,
                'agreement_url': self.url,
                'acceptance_date': acceptance_date}

        self.login()
        rv = self.client.post('/api/user/{}/consent'.format(TEST_USER_ID),
                          content_type='application/json',
                          data=json.dumps(data))
        self.assert200(rv)
        self.assertEqual(self.test_user.valid_consents.count(), 1)
        self.assertEqual(self.test_user.valid_consents[0].organization_id,
                         org1.id)
        self.assertEqual(self.test_user.valid_consents[0].audit.timestamp,
                         parser.parse(acceptance_date))

    def test_delete_user_consent(self):
        org1, org2 = [org for org in Organization.query.filter(
            Organization.id > 0).limit(2)]
        org1_id, org2_id = org1.id, org2.id
        data = {'organization_id': org1_id}

        audit = Audit(user_id=TEST_USER_ID)
        uc1 = UserConsent(organization=org1, agreement_url=self.url,
                          audit=audit)
        uc2 = UserConsent(organization=org2, agreement_url=self.url,
                          audit=audit)
        self.test_user._consents.append(uc1)
        self.test_user._consents.append(uc2)
        with SessionScope(db):
            db.session.commit()
        self.test_user = db.session.merge(self.test_user)
        self.assertEqual(self.test_user.valid_consents.count(), 2)
        self.login()

        rv = self.client.delete('/api/user/{}/consent'.format(TEST_USER_ID),
                             content_type='application/json',
                             data=json.dumps(data))
        self.assert200(rv)
        self.assertEqual(self.test_user.valid_consents.count(), 1)
        self.assertEqual(self.test_user.valid_consents[0].organization_id,
                         org2_id)

        # We no longer omit deleted consent rows, but rather, include
        # their audit data.
        rv = self.client.get('/api/user/{}/consent'.format(TEST_USER_ID))
        self.assertTrue('deleted' in json.dumps(rv.json))
