"""Unit test module for terms of use logic"""
import json
from flask_webtest import SessionScope

from tests import TestCase, TEST_USER_ID
from portal.extensions import db
from portal.models.audit import Audit
from portal.models.tou import ToU


tou_url = 'http://fake-tou.org'


class TestTou(TestCase):
    """Terms Of Use tests"""

    def test_tou_str(self):
        audit = Audit(user_id=TEST_USER_ID, subject_id=TEST_USER_ID,
                    comment="Agreed to ToU", context='other')
        tou = ToU(audit=audit, agreement_url=tou_url)
        results = "{}".format(tou)
        self.assertTrue(tou_url in results)

    def test_get_tou(self):
        rv = self.client.get('/api/tou')
        self.assert200(rv)
        self.assertTrue('url' in rv.json)

    def test_accept(self):
        self.login()
        data = {'agreement_url': tou_url}
        rv = self.client.post('/api/tou/accepted',
                           content_type='application/json',
                           data=json.dumps(data))
        self.assert200(rv)
        tou = ToU.query.one()
        self.assertEquals(tou.agreement_url, tou_url)
        self.assertEquals(tou.audit.user_id, TEST_USER_ID)

    def test_service_accept(self):
        service_user = self.add_service_user()
        self.login(user_id=service_user.id)
        data = {'agreement_url': tou_url}
        rv = self.client.post('/api/user/{}/tou/accepted'.format(TEST_USER_ID),
                           content_type='application/json',
                           data=json.dumps(data))
        self.assert200(rv)
        tou = ToU.query.one()
        self.assertEquals(tou.agreement_url, tou_url)
        self.assertEquals(tou.audit.user_id, TEST_USER_ID)

    def test_get(self):
        audit = Audit(user_id=TEST_USER_ID, subject_id=TEST_USER_ID)
        tou = ToU(audit=audit, agreement_url=tou_url)
        with SessionScope(db):
            db.session.add(tou)
            db.session.commit()

        self.login()
        rv = self.client.get('/api/user/{}/tou'.format(TEST_USER_ID))
        self.assert200(rv)
        self.assertEquals(rv.json['accepted'], True)
