"""Module for additional datetime tools/utilities"""
from datetime import date, datetime
from dateutil import parser
from flask import abort, current_app
import pytz


def as_fhir(obj):
    """For builtin types needing FHIR formatting help

    Returns obj as JSON FHIR formatted string

    """
    if hasattr(obj, 'as_fhir'):
        return obj.as_fhir()
    if isinstance(obj, datetime):
        # Make SURE we only communicate unaware or UTC timezones
        tz = getattr(obj, 'tzinfo', None)
        if tz and tz != pytz.utc:
            current_app.logger.error("Datetime export of NON-UTC timezone")
        return obj.strftime("%Y-%m-%dT%H:%M:%S%z")
    if isinstance(obj, date):
        return obj.strftime('%Y-%m-%d')


class FHIR_datetime(object):
    """Utility class/namespace for working with FHIR datetimes"""

    @staticmethod
    def as_fhir(obj):
        return as_fhir(obj)

    @staticmethod
    def parse(data, error_subject=None):
        """Parse input string to generate a UTC datetime instance

        NB - date must be more recent than year 1900 or a ValueError
        will be raised.

        :param data: the datetime string to parse
        :param error_subject: Subject string to use in error message

        :return: UTC datetime instance from given data

        """
        # As we use datetime.strftime for display, and it can't handle dates
        # older than 1900, treat all such dates as an error
        epoch = datetime.strptime('1900-01-01', '%Y-%m-%d')
        try:
            dt = parser.parse(data)
        except ValueError:
            msg = "Unable to parse {}: {}".format(error_subject, data)
            current_app.logger.warn(msg)
            abort(400, msg)
        if dt.tzinfo:
            epoch = pytz.utc.localize(epoch)
            # Convert to UTC if necessary
            if dt.tzinfo != pytz.utc:
                dt = dt.astimezone(pytz.utc)
        # As we use datetime.strftime for display, and it can't handle dates
        # older than 1900, treat all such dates as an error
        if dt < epoch:
            raise ValueError("Dates prior to year 1900 not supported")
        return dt

    @staticmethod
    def now():
        """Generates a FHIR compliant datetime string for current moment"""
        return datetime.utcnow().isoformat()+'Z'