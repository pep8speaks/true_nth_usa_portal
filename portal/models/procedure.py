"""Procedure Model"""

from ..extensions import db
from .fhir import as_fhir, CodeableConcept, FHIR_datetime
from .reference import Reference


class Procedure(db.Model):
    """ORM class for procedures

    Similar to the profiles published by
    `SMART <http://docs.smarthealthit.org/profiles/>`_

    :Each *Procedure* must have:
        :1 patient: in Procedure.subject (aka Procedure.user)
        :1 code: in Procedure.code (pointing to a CodeableConcept) with
            *system* of http://snomed.info/sct
        :1 performed datetime: in Procedure.performedDateTime

    """
    __tablename__ = 'procedures'
    id = db.Column(db.Integer, primary_key=True)

    start_time = db.Column(db.DateTime, nullable=False)
    """required whereas end_time is optional
    """

    end_time = db.Column(db.DateTime, nullable=True)
    """when defined, produces a performedPeriod, otherwise
    *start_time* is used alone as performedDateTime
    """

    code_id = db.Column(db.ForeignKey('codeable_concepts.id'), nullable=False)
    user_id = db.Column(db.ForeignKey('users.id'), nullable=False)
    audit_id = db.Column(db.ForeignKey('audit.id'), nullable=False)

    audit = db.relationship('Audit', cascade="save-update", lazy='joined')
    """tracks when and by whom the `procedure` was retained, included
    as *meta* data in the FHIR output
    """

    code = db.relationship('CodeableConcept', lazy='joined')
    """procedure.code (a `CodeableConcept`) defines the procedure.
    coding.system is required to be `http://snomed.info/sct`
    """

    def as_fhir(self):
        """produces FHIR representation of procedure in JSON format"""
        d = {}
        d['resourceType'] = 'Procedure'
        d['id'] = self.id
        d['meta'] = self.audit.as_fhir()
        d['subject'] = Reference.patient(self.user_id).as_fhir()
        d['code'] = self.code.as_fhir()
        if self.end_time:
            d['performedPeriod'] = {
                'start': as_fhir(self.start_time),
                'end': as_fhir(self.end_time)}
        else:
            d['performedDateTime'] = as_fhir(self.start_time)
        return d

    @classmethod
    def from_fhir(cls, data, audit):
        """Parses FHIR data to produce a new procedure instance"""
        p = cls(audit=audit)
        p.user_id = Reference.parse(data['subject']).id
        if 'performedDateTime' in data:
            p.start_time = FHIR_datetime.parse(data['performedDateTime'])
        else:
            period = data['performedPeriod']
            p.start_time = FHIR_datetime.parse(period['start'])
            p.end_time = FHIR_datetime.parse(period['end'])
        p.code = CodeableConcept.from_fhir(data['code'])
        return p

    def __str__(self):
        """Log friendly string format"""
        def performed():
            if self.end_time:
                return "{} to {}".format(
                    FHIR_datetime.as_fhir(self.start_time),
                    FHIR_datetime.as_fhir(self.end_time))
            return FHIR_datetime.as_fhir(self.start_time)

        return "Procedure {} on {} performed {}".format(
            self.code, self.user_id, performed())