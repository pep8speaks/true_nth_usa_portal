"""Module for intervention access strategy functions

Determining whether or not to provide access to a given intervention
for a user is occasionally tricky business.  By way of the access_strategies
property on all interventions, one can add additional criteria by defining a
function here (or elsewhere) and adding it to the desired intervention.

function signature: takes named parameters (intervention, user) and returns
a boolean - True grants access (and short circuits further access tests),
False does not.

NB - several functions are closures returning access_strategy functions with
the parameters given to the closures.

"""
from datetime import datetime
from flask import current_app, url_for
from flask_babel import gettext as _
import json
from sqlalchemy import and_, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import sys

from ..database import db
from ..date_tools import localize_datetime
from .fhir import CC, Coding, CodeableConcept
from .identifier import Identifier
from .intervention import Intervention, INTERVENTION, UserIntervention
from .organization import Organization, OrgTree, OrganizationIdentifier
from .procedure_codes import known_treatment_started
from .role import Role
from ..system_uri import DECISION_SUPPORT_GROUP, TRUENTH_CLINICAL_CODE_SYSTEM


# ##
# # functions implementing the 'access_strategy' API
# ##

__log_strats = None


def _log(**kwargs):
    """Wrapper to log all the access lookup results within"""
    # get config value if haven't yet
    global __log_strats
    if __log_strats is None:
        __log_strats = current_app.config.get("LOG_DEBUG_STRATS", False)
    if __log_strats:
        msg = kwargs.get('message', '')  # optional
        current_app.logger.debug(
            "{func_name} returning {result} for {user} on intervention "
            "{intervention}".format(**kwargs) + msg)


def limit_by_clinic_w_id(
        identifier_value, identifier_system=DECISION_SUPPORT_GROUP,
        combinator='any', include_children=True):
    """Requires user is associated with {any,all} clinics with identifier

    :param identifier_value: value string for identifer associated with org(s)
    :param identifier_system: system string for identifier, defaults to
        DECISION_SUPPORT_GROUP
    :param combinator: determines if the user must be in 'any' (default) or
       'all' of the clinics in the given list.  NB combining 'all' with
       include_children=True would mean all orgs in the list AND all chidren of
       all orgs in list must be associated with the user for a true result.
    :param include_children: include children in the organization tree if
        set (default), otherwise, only include the organizations in the list

    """
    try:
        identifier = Identifier.query.filter_by(
            _value=identifier_value, system=identifier_system).one()
    except NoResultFound:
        raise ValueError(
            "strategy names non-existing Identifier({}, {})".format(
                identifier_value, identifier_system))

    orgs = Organization.query.join(OrganizationIdentifier).filter(and_(
        Organization.id == OrganizationIdentifier.organization_id,
        OrganizationIdentifier.identifier_id == identifier.id)).all()

    if include_children:
        ot = OrgTree()
        required = set([o for og in orgs for o in ot.here_and_below_id(og.id)])
    else:
        required = set((o.id for o in orgs))
    if combinator not in ('any', 'all'):
        raise ValueError("unknown value {} for combinator, must be any or all")

    def user_registered_with_all_clinics(intervention, user):
        has = set((o.id for o in user.organizations))
        if required.intersection(has) == required:
            _log(result=True, func_name='limit_by_clinic_list', user=user,
                 intervention=intervention.name)
            return True

    def user_registered_with_any_clinics(intervention, user):
        has = set((o.id for o in user.organizations))
        if not required.isdisjoint(has):
            _log(result=True, func_name='limit_by_clinic_list', user=user,
                 intervention=intervention.name)
            return True

    return user_registered_with_all_clinics if combinator == 'all' else\
        user_registered_with_any_clinics


def not_in_clinic_w_id(
        identifier_value, identifier_system=DECISION_SUPPORT_GROUP,
        include_children=True):
    """Requires user isn't associated with any clinic in the list

    :param identifier_value: value string for identifer associated with org(s)
    :param identifier_system: system string for identifier, defaults to
        DECISION_SUPPORT_GROUP
    :param include_children: include children in the organization tree if
        set (default), otherwise, only include the organizations directly
        associated with the identifier

    """
    try:
        identifier = Identifier.query.filter_by(
            _value=identifier_value, system=identifier_system).one()
    except NoResultFound:
        raise ValueError(
            "strategy names non-existing Identifier({}, {})".format(
                identifier_value, identifier_system))

    orgs = Organization.query.join(OrganizationIdentifier).filter(and_(
        Organization.id == OrganizationIdentifier.organization_id,
        OrganizationIdentifier.identifier_id == identifier.id)).all()

    if include_children:
        ot = OrgTree()
        dont_want = set(
            [o for og in orgs for o in ot.here_and_below_id(og.id)])
    else:
        dont_want = set((o.id for o in orgs))

    def user_not_registered_with_clinics(intervention, user):
        has = set((o.id for o in user.organizations))
        if has.isdisjoint(dont_want):
            _log(result=True, func_name='not_in_clinic_list', user=user,
                 intervention=intervention.name)
            return True

    return user_not_registered_with_clinics


def in_role_list(role_list):
    """Requires user is associated with any role in the list"""
    roles = []
    for role in role_list:
        try:
            role = Role.query.filter_by(
                name=role).one()
            roles.append(role)
        except NoResultFound:
            raise ValueError("role '{}' not found".format(role))
        except MultipleResultsFound:
            raise ValueError("more than one role named '{}'"
                             "found".format(role))
    required = set(roles)

    def user_has_given_role(intervention, user):
        has = set(user.roles)
        if has.intersection(required):
            _log(result=True, func_name='in_role_list', user=user,
                 intervention=intervention.name)
            return True

    return user_has_given_role


def not_in_role_list(role_list):
    """Requires user isn't associated with any role in the list"""
    roles = []
    for role in role_list:
        try:
            role = Role.query.filter_by(
                name=role).one()
            roles.append(role)
        except NoResultFound:
            raise ValueError("role '{}' not found".format(role))
        except MultipleResultsFound:
            raise ValueError("more than one role named '{}'"
                             "found".format(role))
    dont_want = set(roles)

    def user_not_given_role(intervention, user):
        has = set(user.roles)
        if has.isdisjoint(dont_want):
            _log(result=True, func_name='not_in_role_list', user=user,
                 intervention=intervention.name)
            return True

    return user_not_given_role


def allow_if_not_in_intervention(intervention_name):
    """Strategy API checks user does not belong to named intervention"""

    exclusive_intervention = getattr(INTERVENTION, intervention_name)

    def user_not_in_intervention(intervention, user):
        if not exclusive_intervention.quick_access_check(user):
            _log(result=True, func_name='user_not_in_intervention', user=user,
                 intervention=intervention.name)
            return True

    return user_not_in_intervention


def update_card_html_on_completion():
    """Update description and card_html depending on state"""
    from .assessment_status import AssessmentStatus  # avoid cycle

    def update_user_card_html(intervention, user):
        # NB - this is by design, a method with side effects
        # namely, alters card_html and links depending on survey state
        now = datetime.utcnow()
        assessment_status = AssessmentStatus(user=user, as_of_date=now)
        current_app.logger.debug("{}".format(assessment_status))
        indefinite_questionnaires = (
            assessment_status.instruments_needing_full_assessment(
                classification='indefinite'),
            assessment_status.instruments_in_progress(
                classification='indefinite'))

        def thank_you_block(name, registry):
            greeting = _(u"Thank you, {}.").format(name)
            confirm = _(
                u"You've completed the {} questionnaire"
                ".").format(registry)
            reminder = _(
                u"You will be notified when the next "
                "questionnaire is ready to complete.")
            logout = _(u"Log out")
            return u"""
                <div class="portal-header-container">
                  <h2 class="portal-header">{greeting}</h2>
                  <p>{confirm}</p>
                  <p>{reminder}</p>
                  <div class="button-callout">
                    <figure id="portalScrollArrow"></figure>
                  </div>
                  <br/><br/>
                  <div class="button-container portal-header-logout-container">
                    <a class="btn-lg btn-tnth-primary" href="/logout">
                      {logout}
                    </a>
                  </div>
                </div>""".format(
                    greeting=greeting, confirm=confirm, reminder=reminder,
                    logout=logout)

        def intro_html(assessment_status):
            """Generates appropriate HTML for the intro paragraph"""

            indefinite_questionnaires = (
                assessment_status.instruments_needing_full_assessment(
                    classification='indefinite'),
                assessment_status.instruments_in_progress(
                    classification='indefinite'))

            if assessment_status.overall_status in (
                    'Due', 'Overdue', 'In Progress'):
                qb = assessment_status.qb_data.qb
                trigger_date = qb.trigger_date(user)
                utc_due = qb.calculated_start(
                    trigger_date, as_of_date=now).relative_start
                utc_due = qb.calculated_due(
                    trigger_date, as_of_date=now) or utc_due
                due_date = localize_datetime(utc_due, user)
                assert due_date
                greeting = _(u"Hi {}").format(user.display_name)
                reminder = _(
                    u"Please complete your {} "
                    "questionnaire by {}.").format(
                        assessment_status.top_organization.name,
                        due_date.strftime('%-d %b %Y'))
                return u"""
                    <div class="portal-header-container">
                      <h2 class="portal-header">{greeting},</h2>
                      <h4 class="portal-intro-text">
                        {reminder}
                      </h4>
                      <div class="button-callout">
                        <figure id="portalScrollArrow"></figure>
                      </div>
                    </div>""".format(greeting=greeting, reminder=reminder)

            if any(indefinite_questionnaires):
                greeting = _(u"Hi {}").format(user.display_name)
                reminder = _(
                    u"Please complete your {} "
                    "questionnaire at your convenience.").format(
                        assessment_status.top_organization.name)
                return u"""
                    <div class="portal-header-container">
                      <h2 class="portal-header">{greeting},</h2>
                      <h4 class="portal-intro-text">
                        {reminder}
                      </h4>
                      <div class="button-callout">
                        <figure id="portalScrollArrow"></figure>
                      </div>
                    </div>""".format(greeting=greeting, reminder=reminder)

            if assessment_status.overall_status == "Completed":
                return thank_you_block(
                    name=user.display_name,
                    registry=assessment_status.top_organization.name)
            raise ValueError("Unexpected state generating intro_heml")

        def completed_card_html(assessment_status):
            """Generates the appropriate HTML for the 'completed card'"""
            header = _(u"Completed Questionnaires")
            message = _(
                u"When you are done, completed questionnaires will be "
                "shown here.")
            completed_placeholder = u"""
                <div class="portal-description disabled">
                  <h4 class="portal-description-title">
                    {header}
                  </h4>
                  <div class="portal-description-body">
                    <p>{message}</p>
                  </div>
                </div>""".format(header=header, message=message)

            completed_html = u"""
                <div class="portal-description">
                  <h4 class="portal-description-title">
                    {header}
                  </h4>
                  <div class="portal-description-body">
                    <p>
                      <a href="{recent_survey_link}">
                        {message}
                      </a>
                    </p>
                  </div>
                 </div>"""

            if assessment_status.overall_status == "Completed":
                header = _(u"Completed Questionnaires")
                utc_comp_date = assessment_status.completed_date
                comp_date = localize_datetime(utc_comp_date, user)
                message = _(
                    u"View questionnaire completed on {}").format(
                        comp_date.strftime('%-d %b %Y'))
                return completed_html.format(
                    header=header, message=message,
                    recent_survey_link=url_for(
                        "portal.profile", _anchor="proAssessmentsLoc"))
            else:
                return completed_placeholder

        ###
        #  Generate link_url, link_label and card_html to
        #  match state of users questionnaires (aka assessments)
        ####
        if assessment_status.overall_status in (
                'Due', 'Overdue', 'In Progress'):
            # User has unfinished baseline assessment work
            link_label = 'Continue questionnaire' if (
                assessment_status.overall_status == 'In Progress') else (
                    'Go to questionnaire')
            link_url = url_for('assessment_engine_api.present_needed')
            header = _(u"Open Questionnaire")
            card_html = u"""
            {intro}
            <div class="portal-main portal-flex-container">
              <div class="portal-description portal-description-incomplete">
                <h4 class="portal-description-title">{header}</h4>
                <div class="button-container">
                  <a class="btn-lg btn-tnth-primary" href="{link_url}">
                     {link_label}
                  </a>
                </div>
              </div>
              {completed_card}
            </div>""".format(
                intro=intro_html(assessment_status), header=header,
                link_url=link_url, link_label=link_label,
                completed_card=completed_card_html(assessment_status))

        elif any(indefinite_questionnaires):
            # User completed baseline, but has outstanding indefinite work
            link_label = _(u'Continue questionnaire') if (
                indefinite_questionnaires[1]) else (
                    _(u'Go to questionnaire'))
            link_url = url_for('assessment_engine_api.present_needed')
            header = _(u"Open Questionnaire")
            card_html = u"""
            {intro}
            <div class="portal-main portal-flex-container">
              <div class="portal-description portal-description-incomplete">
                <h4 class="portal-description-title">{header}</h4>
                <div class="button-container">
                  <a class="btn-lg btn-tnth-primary" href="{link_url}">
                     {link_label}
                  </a>
                </div>
              </div>
              {completed_card}
            </div>
            """.format(
                intro=intro_html(assessment_status), header=header,
                link_url=link_url, link_label=link_label,
                completed_card=completed_card_html(assessment_status))

        elif assessment_status.overall_status == "Completed":
            # User completed both baseline and indefinite
            link_label = _(u'View previous questionnaire')
            link_url = url_for("portal.profile", _anchor="proAssessmentsLoc")
            header = _(u"Open Questionnaire")
            message = _(u"No questionnaire is due.")
            card_html = u"""
            <div class="container">
              {intro}
              <div class=
              "portal-main portal-flex-container portal-completed-container">
                <div class="portal-description">
                  <h4 class="portal-description-title">{header}</h4>
                  <div class="portal-description-body">
                      <p>{message}</p>
                  </div>
                </div>
                {completed_card}
              </div>
            </div>
            """.format(
                intro=intro_html(assessment_status),
                header=header, message=message,
                completed_card=completed_card_html(assessment_status))
        else:
            # User has completed indefinite work, and the baseline
            # is either Expired or Partially Completed
            if assessment_status.overall_status not in (
                    "Expired", "Partially Completed"):
                raise ValueError(
                    "Unexpected state {} for {}".format(
                        assessment_status.overall_status, user))

            link_label = u"N/A"
            link_url = None

            # If the user was enrolled in indefinite work and lands
            # here, they should see the thank you text.
            if assessment_status.enrolled_in_classification('indefinite'):
                card_html = thank_you_block(
                    name=user.display_name,
                    registry=assessment_status.top_organization.name)
            else:
                message = _(
                    u"The assessment is no longer available.\n"
                    "A research staff member will contact you for assistance.")
                card_html = u"""
                    <div class='portal-description
                        portal-no-description-container'>
                      {message}
                    </div>""".format(message=message)

        ui = UserIntervention.query.filter(and_(
            UserIntervention.user_id == user.id,
            UserIntervention.intervention_id == intervention.id)).first()
        if not ui:
            db.session.add(
                UserIntervention(
                    user_id=user.id,
                    intervention_id=intervention.id,
                    card_html=card_html,
                    link_label=link_label,
                    link_url=link_url
                ))
            db.session.commit()
        else:
            if ui.card_html != card_html or ui.link_label != link_label or\
               ui.link_url != link_url:
                ui.card_html = card_html
                ui.link_label = link_label,
                ui.link_url = link_url
                db.session.commit()

        # Really this function just exists for the side effects, don't
        # prevent access
        return True

    return update_user_card_html


def tx_begun(boolean_value):
    """Returns strategy function testing if user is known to have started Tx

    :param boolean_value: true for known treatment started (i.e. procedure
        indicating tx has begun), false to confirm a user doesn't have
        a procedure indicating tx has begun

    """
    if boolean_value == 'true':
        check_func = known_treatment_started
    elif boolean_value == 'false':
        def check_func(u): return not known_treatment_started(u)
    else:
        raise ValueError("expected 'true' or 'false' for boolean_value")

    def user_has_desired_tx(intervention, user):
        return check_func(user)
    return user_has_desired_tx


def observation_check(display, boolean_value):
    """Returns strategy function for a particular observation and logic value

    :param display: observation coding.display from
      TRUENTH_CLINICAL_CODE_SYSTEM
    :param boolean_value: ValueQuantity boolean true or false expected

    """
    try:
        coding = Coding.query.filter_by(
            system=TRUENTH_CLINICAL_CODE_SYSTEM, display=display).one()
    except NoResultFound:
        raise ValueError("coding.display '{}' not found".format(display))
    try:
        cc_id = CodeableConcept.query.filter(
            CodeableConcept.codings.contains(coding)).one().id
    except NoResultFound:
        raise ValueError("codeable_concept'{}' not found".format(coding))

    if boolean_value == 'true':
        vq = CC.TRUE_VALUE
    elif boolean_value == 'false':
        vq = CC.FALSE_VALUE
    else:
        raise ValueError("boolean_value must be 'true' or 'false'")

    def user_has_matching_observation(intervention, user):
        obs = [o for o in user.observations if o.codeable_concept_id == cc_id]
        if obs and obs[0].value_quantity == vq:
            _log(result=True, func_name='observation_check', user=user,
                 intervention=intervention.name,
                 message='{}:{}'.format(coding.display, vq.value))
            return True

    return user_has_matching_observation


def combine_strategies(**kwargs):
    """Make multiple strategies into a single statement

    The nature of the access lookup returns True for the first
    success in the list of strategies for an intervention.  Use
    this method to chain multiple strategies together into a logical **and**
    fashion rather than the built in locical **or**.

    NB - kwargs must have keys such as 'strategy_n', 'strategy_n_kwargs'
    for every 'n' strategies being combined, starting at 1.  Set arbitrary
    limit of 6 strategies for time being.

    Nested strategies may actually want a logical 'OR'.  Optional kwarg
    `combinator` takes values {'any', 'all'} - default 'all' means all
    strategies must evaluate true.  'any' means just one must eval true for a
    positive result.

    """
    strats = []
    arbitrary_limit = 7
    if 'strategy_{}'.format(arbitrary_limit) in kwargs:
        raise ValueError("only supporting %d combined strategies",
                         arbitrary_limit-1)
    for i in range(1, arbitrary_limit):
        if 'strategy_{}'.format(i) not in kwargs:
            break

        func_name = kwargs['strategy_{}'.format(i)]

        func_kwargs = {}
        for argset in kwargs['strategy_{}_kwargs'.format(i)]:
            func_kwargs[argset['name']] = argset['value']

        func = getattr(sys.modules[__name__], func_name)
        strats.append(func(**func_kwargs))

    def call_all_combined(intervention, user):
        "Returns True if ALL of the combined strategies return True"
        for strategy in strats:
            if not strategy(intervention, user):
                _log(
                    result=False, func_name='combine_strategies', user=user,
                    intervention=intervention.name)
                return
        # still here?  effective AND passed as all returned true
        _log(
            result=True, func_name='combine_strategies', user=user,
            intervention=intervention.name)
        return True

    def call_any_combined(intervention, user):
        "Returns True if ANY of the combined strategies return True"
        for strategy in strats:
            if strategy(intervention, user):
                _log(
                    result=True, func_name='combine_strategies', user=user,
                    intervention=intervention.name)
                return True
        # still here?  effective ANY failed as none returned true
        _log(
            result=False, func_name='combine_strategies', user=user,
            intervention=intervention.name)
        return

    combinator = kwargs.get('combinator', 'all')
    if combinator == 'any':
        return call_any_combined
    elif combinator == 'all':
        return call_all_combined
    else:
        raise ValueError("unrecognized value {} for `combinator`, "
                         "limited to {'any', 'all'}").format(combinator)


class AccessStrategy(db.Model):
    """ORM to persist access strategies on an intervention

    The function_details field contains JSON defining which strategy to
    use and how it should be instantiated by one of the closures implementing
    the access_strategy interface.  Said closures must be defined in this
    module (a security measure to keep unsanitized code out).

    """
    __tablename__ = 'access_strategies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    intervention_id = db.Column(
        db.ForeignKey('interventions.id'), nullable=False)
    rank = db.Column(db.Integer)
    function_details = db.Column(JSONB, nullable=False)

    __table_args__ = (UniqueConstraint('intervention_id', 'rank',
                                       name='rank_per_intervention'),)

    def __str__(self):
        """Log friendly string format"""
        return "AccessStrategy: {0.name} {0.description} {0.rank}"\
            "{0.function_details}".format(self)

    @classmethod
    def from_json(cls, data):
        obj = cls()
        try:
            obj.name = data['name']
            if 'id' in data:
                obj.id = data['id']
            if 'intervention_name' in data:
                intervention = Intervention.query.filter_by(
                    name=data['intervention_name']).first()
                if not intervention:
                    raise ValueError(
                        'Intervention not found {}.  (NB: new interventions '
                        'require `seed -i` to import)'.format(
                            data['intervention_name']))
                obj.intervention_id = intervention.id
            if 'description' in data:
                obj.description = data['description']
            if 'rank' in data:
                obj.rank = data['rank']
            obj.function_details = json.dumps(data['function_details'])

            # validate the given details by attempting to instantiate
            obj.instantiate()
        except Exception, e:
            raise ValueError("AccessStrategy instantiation error: {}".format(
                e))
        return obj

    def as_json(self):
        """Return self in JSON friendly dictionary"""
        d = {
            "name": self.name,
            "function_details": json.loads(self.function_details),
            "resourceType": 'AccessStrategy'
        }
        d['intervention_name'] = Intervention.query.get(
            self.intervention_id).name
        if self.id:
            d['id'] = self.id
        if self.rank:
            d['rank'] = self.rank
        if self.description:
            d['description'] = self.description
        return d

    def instantiate(self):
        """Bring the serialized access strategy function to life

        Using the JSON in self.function_details, instantiate the
        function and return it ready to use.

        """
        details = json.loads(self.function_details)
        if 'function' not in details:
            raise ValueError("'function' not found in function_details")
        if 'kwargs' not in details:
            raise ValueError("'kwargs' not found in function_details")
        func_name = details['function']
        # limit to this module
        func = getattr(sys.modules[__name__], func_name)
        kwargs = {}
        for argset in details['kwargs']:
            kwargs[argset['name']] = argset['value']
        return func(**kwargs)
