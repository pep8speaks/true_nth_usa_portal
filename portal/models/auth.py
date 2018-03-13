"""Auth related model classes """
from flask import current_app, url_for
from datetime import datetime, timedelta
from smtplib import SMTPRecipientsRefused
from sqlalchemy.dialects.postgresql import ENUM

from ..database import db
from ..extensions import oauth
from .message import EmailMessage
from .role import Role, ROLE
from .relationship import Relationship, RELATIONSHIP
from .user import User, UserRoles, UserRelationship
from ..system_uri import SUPPORTED_OAUTH_PROVIDERS, TRUENTH_IDENTITY_SYSTEM
from .user import current_user

providers_list = ENUM(
    *SUPPORTED_OAUTH_PROVIDERS, name='providers', create_type=False)


class AuthProvider(db.Model):
    __tablename__ = 'auth_providers'
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column('provider', providers_list)
    provider_id = db.Column(db.String(40))
    user_id = db.Column(db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False)
    user = db.relationship('User')

    def as_fhir(self):
        # produce a FHIR identifier entry for the provider
        # helps interventions with support, i.e. user authentication used
        return {
            'use': 'secondary',
            'system': '{system}/{provider}'.format(
                system=TRUENTH_IDENTITY_SYSTEM, provider=self.provider),
            'value': self.provider_id}


class Grant(db.Model):
    __tablename__ = 'grants'  # Override default 'grant'
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )
    user = db.relationship('User')

    client_id = db.Column(
        db.String(40), db.ForeignKey('clients.client_id'),
        nullable=False,
    )
    client = db.relationship('Client')

    code = db.Column(db.String(255), index=True, nullable=False)

    redirect_uri = db.Column(db.Text)
    expires = db.Column(db.DateTime)

    _scopes = db.Column(db.Text)

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []

    def validate_redirect_uri(self, redirect_uri):
        """Validate the redirect_uri from the OAuth Grant request

        The RFC requires exact match on the redirect_uri.  In practice
        this is too great of a burden for the interventions.  Make
        sure it's from the same scheme:://host:port the client
        registered with

        http://tools.ietf.org/html/rfc6749#section-4.1.3

        """
        # Use same implementation found in client
        return self.client.validate_redirect_uri(redirect_uri)


class Token(db.Model):
    __tablename__ = 'tokens'  # Override default 'token'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(
        db.String(40), db.ForeignKey('clients.client_id', ondelete='CASCADE'),
        nullable=False,
    )
    client = db.relationship('Client', backref='tokens')

    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )
    user = db.relationship('User')

    # currently only bearer is supported
    token_type = db.Column(db.String(40))

    access_token = db.Column(db.String(255), unique=True)
    refresh_token = db.Column(db.String(255), unique=True)
    expires = db.Column(db.DateTime)
    _scopes = db.Column(db.Text)

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


@oauth.grantgetter
def load_grant(client_id, code):
    return Grant.query.filter_by(client_id=client_id, code=code).first()


@oauth.grantsetter
def save_grant(client_id, code, request, *args, **kwargs):
    # decide the expires time yourself
    expires = datetime.utcnow() + timedelta(seconds=100)
    grant = Grant(
        client_id=client_id,
        code=code['code'],
        redirect_uri=request.redirect_uri,
        _scopes=' '.join(request.scopes),
        user=current_user(),
        expires=expires
    )
    db.session.add(grant)
    db.session.commit()
    return grant


@oauth.tokengetter
def load_token(access_token=None, refresh_token=None):
    if access_token:
        return Token.query.filter_by(access_token=access_token).first()
    elif refresh_token:
        return Token.query.filter_by(refresh_token=refresh_token).first()


@oauth.tokensetter
def save_token(token, request, *args, **kwargs):
    toks = Token.query.filter_by(
        client_id=request.client.client_id,
        user_id=request.user.id
    )
    # delete any existing; allow one token per client:user
    for t in toks:
        db.session.delete(t)

    expires_in = token.get('expires_in')
    expires = datetime.utcnow() + timedelta(seconds=expires_in)

    tok = Token(
        access_token=token['access_token'],
        refresh_token=(
            token['refresh_token'] if 'refresh_token' in token else None),
        token_type=token['token_type'],
        _scopes=token['scope'],
        expires=expires,
        client_id=request.client.client_id,
        user_id=request.user.id,
    )
    db.session.add(tok)
    db.session.commit()
    return tok


class Mock(object):
    pass


def create_service_token(client, user):
    """Generate and return a bearer token for service calls

    Partners need a mechanism for automated, authorized API access.  This
    function returns a bearer token for subsequent authorized calls.

    NB - as this opens a back door, it's only offered to users with the single
    role 'service'.

    """
    if not current_app.config.get('TESTING') and (
            len(user.roles) > 1 or user.roles[0].name != ROLE.SERVICE):
        raise ValueError("only service users can create service tokens")

    # Hacking a backdoor into the OAuth protocol to generate a valid token
    # Mock the request and validation needed to pass
    from oauthlib.oauth2.rfc6749.tokens import BearerToken

    fake_request = Mock()
    fake_request.state, fake_request.extra_credentials = None, None
    fake_request.client = client
    fake_request.user = user
    fake_request.scopes = ['email']

    request_validator = Mock()
    request_validator.save_bearer_token = save_token

    bt = BearerToken(request_validator=request_validator)
    bt.expires_in = int(timedelta(days=365).total_seconds())  # one year
    bt.create_token(fake_request)

    # Token should now exist as only token for said user - return it
    return Token.query.filter_by(user_id=user.id).first()


def token_janitor():
    """Called by scheduled job to clean up and send alerts

    No value in keeping around stale tokens, so we delete any that have expired.

    For service tokens, trigger an email alert if they will be expiring soon.

    :returns: list of unreachable email addresses

    """
    # Delete expired tokens
    Token.query.filter(Token.expires < datetime.utcnow()).delete()
    db.session.commit()

    # Look up all service tokens and warn any sponsors via email if about
    # to expire
    error_emails = set()
    threshold = datetime.utcnow() + timedelta(weeks=6)
    results = Token.query.join(
        UserRoles, Token.user_id == UserRoles.user_id).join(
        Role, UserRoles.role_id == Role.id).filter(
        Role.name == ROLE.SERVICE).filter(
        Token.expires < threshold).with_entities(
        UserRoles.user_id, Token.client_id, Token.expires).order_by(
        Token.expires).all()
    for user_id, client_id, expires in results:
        # Lookup the sponsor of the service account, and send em an email
        sponsor = UserRelationship.query.join(
            Relationship,
            Relationship.id == UserRelationship.relationship_id).filter(
            Relationship.name == RELATIONSHIP.SPONSOR).filter(
            UserRelationship.other_user_id == user_id).with_entities(
            UserRelationship.user_id)
        if sponsor.count() != 1:
            raise ValueError(
                'expiring service token, cannot locate sponsor for {}'.format(
                    user_id))
        sponsor_email = User.query.filter(
            User.id == sponsor).with_entities(User.email).one()[0]
        subject = 'WARNING: Service Token Expiration'
        body = (
            "The service token in use at {app} expires {expires}.  "
            "Please renew at {client_url}".format(
                app=current_app.config.get('USER_APP_NAME'),
                expires=expires,
                client_url=url_for(
                    'client.client_edit', client_id=client_id, _external=True)))
        current_app.logger.warn(body)
        em = EmailMessage(
            recipients=sponsor_email,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            subject=subject,
            body=body)
        try:
            # Copy error account in case owner isn't paying attention
            em.send_message(
                cc_address=current_app.config.get('ERROR_SENDTO_EMAIL'))
        except SMTPRecipientsRefused as exc:
            msg = ("Error sending site summary email to {}: "
                   "{}".format(sponsor_email, exc))
            current_app.logger.error(msg)
            for email in exc[0]:
                error_emails.add(email)

    return list(error_emails)
