from flask import (
    abort,
    current_app,
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from flask_user import roles_required

from ..database import db
from ..extensions import oauth, recaptcha
from ..models.app_text import (
    app_text,
    get_terms,
    AboutATMA,
    PrivacyATMA,
    Terms_ATMA,
    VersionedResource,
    WebsiteDeclarationForm_ATMA
)
from ..models.auth import validate_origin
from ..models.coredata import Coredata
from ..models.intervention import Intervention
from ..models.message import EmailMessage
from ..models.organization import Organization
from ..models.role import ROLE
from ..models.user import current_user, get_user
from ..views.auth import next_after_login


eproms = Blueprint(
    'eproms', __name__, template_folder='templates', static_folder='static',
    static_url_path='/eproms/static')


@eproms.errorhandler(404)
def page_not_found(e):
    return render_template('eproms/404.html', no_nav="true", user=current_user()), 404


@eproms.errorhandler(500)
def server_error(e):  # pragma: no cover
    # NB - this is only hit if app.debug == False
    # exception is automatically sent to log by framework
    return render_template('eproms/500.html', no_nav="true", user=current_user()), 500


@eproms.route('/')
def landing():
    """landing page view function - present register / login options"""
    if current_user():
        current_app.logger.debug("landing (found user) -> next_after_login")
        return next_after_login()

    timed_out = request.args.get('timed_out', False)
    init_login_modal = False
    if 'pending_authorize_args' in session:
        init_login_modal = True
    return render_template('eproms/landing.html', user=None, no_nav="true", timed_out=timed_out, init_login_modal=init_login_modal)


@eproms.route('/home')
def home():
    """home page view function

    Present user with appropriate view dependent on roles.

    The inital flow through authentication and data collection is
    controlled by next_after_login().  Only expecting requests
    here after login and intermediate steps have been handled, and then
    only if the login didn't include a 'next' target.

    Raising server error (500) if unexpected state is found to assist in
    finding problems.

    """
    user = current_user()

    # Enforce flow - expect authorized user for this view
    if not user:
        return redirect(url_for('eproms.landing'))

    # Enforce flow - don't expect 'next' params here
    if 'next' in session and session['next']:
        abort(500, "session['next'] found in /home for user {}".\
              format(user))

    # Enforce flow - confirm we have acquired initial data
    if not Coredata().initial_obtained(user):
        still_needed = Coredata().still_needed(user)
        abort(500, 'Missing initial data still needed: {}'.\
              format(still_needed))

    # All checks passed - present appropriate view for user role
    if user.has_role(ROLE.STAFF) or user.has_role(ROLE.INTERVENTION_STAFF):
        return redirect(url_for('patients.patients_root'))
    if user.has_role(ROLE.RESEARCHER):
        return redirect(url_for('.research_dashboard'))

    interventions = Intervention.query.order_by(
        Intervention.display_rank).all()

    consent_agreements = {}
    return render_template(
        'eproms/portal.html', user=user,
        interventions=interventions, consent_agreements=consent_agreements)


@eproms.route('/privacy')
def privacy():
    """ privacy use page"""
    user = current_user()
    if user:
        organization = user.first_top_organization()
        role = None
        for r in (ROLE.STAFF, ROLE.PATIENT):
            if user.has_role(r):
                role = r
        # only include role and organization if both are defined
        if not all((role, organization)):
            role, organization = None, None

        privacy_resource = VersionedResource(app_text(
            PrivacyATMA.name_key(role=role, organization=organization)))
    else:
        abort(400, "No publicly viewable privacy policy page available")

    return render_template(
        'eproms/privacy.html',
        content=privacy_resource.asset, user=user,
        editorUrl=privacy_resource.editor_url)


@eproms.route('/terms')
def terms_and_conditions():
    """ terms-and-conditions of use page"""
    user = current_user()
    terms = VersionedResource(app_text(Terms_ATMA.name_key()))
    return render_template(
        'eproms/terms.html', content=terms.asset, editorUrl=terms.editor_url, user=user)


@eproms.route('/about')
def about():
    """main TrueNTH about page"""
    about_tnth = VersionedResource(
        app_text(AboutATMA.name_key(subject='TrueNTH')))
    return render_template(
        'eproms/about.html',
        about_tnth=about_tnth.asset,
        about_tnth_editorUrl=about_tnth.editor_url,
        user=current_user())


@eproms.route('/contact', methods=('GET', 'POST'))
def contact():
    """main TrueNTH contact page"""
    user = current_user()
    if request.method == 'GET':
        sendername = user.display_name if user else ''
        email = user.email if user else ''
        recipient_types = []
        for org in Organization.query.filter(Organization.email.isnot(None)):
            if u'@' in org.email:
                recipient_types.append((org.name, org.email))
        return render_template(
            'eproms/contact.html', sendername=sendername, email=email, user=user,
            types=recipient_types)

    if (not user and
            current_app.config.get('RECAPTCHA_SITE_KEY', None) and
            current_app.config.get('RECAPTCHA_SECRET_KEY', None) and
            not recaptcha.verify()):
        abort(400, "Recaptcha verification failed")
    sender = request.form.get('email')
    if not sender or ('@' not in sender):
        abort(400, "No valid sender email address provided")
    sendername = request.form.get('sendername')
    subject = u"{server} contact request: {subject}".format(
        server=current_app.config['SERVER_NAME'],
        subject=request.form.get('subject'))
    if len(sendername) > 255:
        abort(400, "Sender name max character length exceeded")
    if len(subject) > 255:
        abort(400, "Subject max character length exceeded")
    formbody = request.form.get('body')
    if not formbody:
        abort(400, "No contact request body provided")
    body = u"From: {sendername}<br />Email: {sender}<br /><br />{body}".format(
        sendername=sendername, sender=sender, body=formbody)
    recipient = request.form.get('type')
    recipient = recipient or current_app.config['CONTACT_SENDTO_EMAIL']
    if not recipient:
        abort(400, "No recipient found")

    user_id = user.id if user else None
    email = EmailMessage(subject=subject, body=body, recipients=recipient,
                         sender=sender, user_id=user_id)
    email.send_message()
    db.session.add(email)
    db.session.commit()
    return jsonify(msgid=email.id)


@eproms.route('/website-consent-script/<int:patient_id>', methods=['GET'])
@roles_required(ROLE.STAFF)
@oauth.require_oauth()
def website_consent_script(patient_id):
    entry_method = request.args.get('entry_method', None)
    redirect_url = request.args.get('redirect_url', None)
    if redirect_url:
        """
        redirect url here is the patient's assessment link
        /api/present-assessment, so validate against local origin
        """
        validate_origin(redirect_url)
    user = current_user()
    patient = get_user(patient_id)
    org = patient.first_top_organization()
    """
    NOTE, we are getting PATIENT's website consent terms here
    as STAFF member needs to read the terms to the patient
    """
    terms = get_terms(org, ROLE.PATIENT)
    top_org = patient.first_top_organization()
    declaration_form = VersionedResource(app_text(WebsiteDeclarationForm_ATMA.
                                                  name_key(organization=top_org)))
    return render_template(
        'eproms/website_consent_script.html', user=user,
        terms=terms, top_organization=top_org,
        entry_method=entry_method, redirect_url=redirect_url,
        declaration_form=declaration_form, patient_id=patient_id)