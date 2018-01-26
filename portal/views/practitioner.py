"""Practitioner API view functions"""
from flask import abort, jsonify, Blueprint, request
from flask import render_template, current_app, url_for
from flask_user import roles_required

from ..audit import auditable_event
from ..database import db
from ..date_tools import FHIR_datetime
from ..extensions import oauth
from ..models.role import ROLE
from ..models.practitioner import Practitioner
from ..models.user import current_user
from .portal import check_int


practitioner_api = Blueprint('practitioner_api', __name__, url_prefix='/api')


@practitioner_api.route('/practitioner')
@oauth.require_oauth()
def practitioner_search():
    """Obtain a bundle (list) of all matching practitioners

    Filter search on key=value pairs.

    Example search:
        /api/practitioner?first_name=Indiana&last_name=Jones

    Returns a JSON FHIR bundle of practitioners as per given search terms.
    Without any search terms, returns all practitioners known to the system.
    If search terms are provided but no matching practitioners are found,
    a 404 is returned.

    ---
    operationId: practitioner_search
    tags:
      - Practitioner
    parameters:
      - name: search_parameters
        in: query
        description:
            Search parameters (`first_name`, `last_name`)
        required: false
        type: string
    produces:
      - application/json
    responses:
      200:
        description:
          Returns a FHIR bundle of [practitioner
          resources](http://www.hl7.org/fhir/practitioner.html) in JSON.
      400:
        description:
          if invalid search param keys are used
      401:
        description:
          if missing valid OAuth token or logged-in user lacks permission
          to view requested patient
      404:
        description:
          if no practitioners found for given search parameters

    """
    query = Practitioner.query
    for k, v in request.args.items():
        if k not in ('first_name', 'last_name'):
            abort(400, "only `first_name`, `last_name` search filters "
                  "are available at this time")
        if v:
            d = {k: v}
            query = query.filter_by(**d)

    practs = [p.as_fhir() for p in query]

    bundle = {
        'resourceType': 'Bundle',
        'updated': FHIR_datetime.now(),
        'total': len(practs),
        'type': 'searchset',
        'link': {
            'rel': 'self',
            'href': url_for(
                'practitioner_api.practitioner_search', _external=True),
        },
        'entry': practs
    }

    return jsonify(bundle)


@practitioner_api.route('/practitioner/<int:practitioner_id>')
@oauth.require_oauth()
def practitioner_get(practitioner_id):
    """Access to the requested practitioner as a FHIR resource

    ---
    operationId: practitioner_get
    tags:
      - Practitioner
    produces:
      - application/json
    parameters:
      - name: practitioner_id
        in: path
        description: TrueNTH practitioner ID
        required: true
        type: integer
        format: int64
    responses:
      200:
        description:
          Returns the requested practitioner as a FHIR [practitioner
          resource](http://www.hl7.org/fhir/practitioner.html) in JSON.
      401:
        description:
          if missing valid OAuth token or logged-in user lacks permission
          to view requested patient

    """
    check_int(practitioner_id)
    practitioner = Practitioner.query.get_or_404(practitioner_id)
    return jsonify(practitioner.as_fhir())


@practitioner_api.route('/practitioner', methods=('POST',))
@oauth.require_oauth()
@roles_required([ROLE.ADMIN, ROLE.SERVICE])
def practitioner_post():
    """Add a new practitioner.  Updates should use PUT

    Returns the JSON FHIR practitioner as known to the system after adding.

    Submit JSON format [Practitioner
    Resource](https://www.hl7.org/fhir/practitioner.html) to add an
    practitioner.

    ---
    operationId: practitioner_post
    tags:
      - Practitioner
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          id: FHIRPractitioner
          required:
            - resourceType
          properties:
            resourceType:
              type: string
              description: defines FHIR resource type, must be Practitioner
    responses:
      200:
        description:
          Returns created [FHIR practitioner
          resource](http://www.hl7.org/fhir/practitioner.html) in JSON.
      400:
        description:
          if practitioner FHIR JSON is not valid
      401:
        description:
          if missing valid OAuth token or logged-in user lacks permission
          to view requested patient

    """
    if (not request.json or 'resourceType' not in request.json or
            request.json['resourceType'] != 'Practitioner'):
        abort(400, "Requires FHIR resourceType of 'Practitioner'")
    try:
        practitioner = Practitioner.from_fhir(request.json)
    except MissingReference, e:
        abort(400, str(e))
    db.session.add(practitioner)
    db.session.commit()
    auditable_event("created new practitioner {}".format(practitioner),
                    user_id=current_user().id, subject_id=current_user().id,
                    context='user')
    return jsonify(practitioner.as_fhir())


# @org_api.route('/organization/<int:organization_id>', methods=('PUT',))
# @oauth.require_oauth()  # for service token access, oauth must come first
# @roles_required([ROLE.ADMIN, ROLE.SERVICE])
# def organization_put(organization_id):
#     """Update organization via FHIR Resource Organization. New should POST

#     Submit JSON format [Organization
#     Resource](https://www.hl7.org/fhir/organization.html) to update an
#     existing organization.

#     Include an **identifier** with system of
#     http://us.truenth.org/identity-codes/shortcut-alias to name a shortcut
#     alias for the organization, useful at `/go/<alias>`.  NB, including a
#     partial list of identifiers will result in the non mentioned identifiers
#     being deleted.  Consider calling GET first.

#     A resource mentioned as partOf the given organization must exist as a
#     prerequisit or a 400 will result.

#     ---
#     operationId: organization_put
#     tags:
#       - Organization
#     produces:
#       - application/json
#     parameters:
#       - name: organization_id
#         in: path
#         description: TrueNTH organization ID
#         required: true
#         type: integer
#         format: int64
#       - in: body
#         name: body
#         schema:
#           id: FHIROrganization
#           required:
#             - resourceType
#           properties:
#             resourceType:
#               type: string
#               description: defines FHIR resource type, must be Organization
#     responses:
#       200:
#         description:
#           Returns updated [FHIR organization
#           resource](http://www.hl7.org/fhir/patient.html) in JSON.
#       400:
#         description:
#           if partOf resource does not exist
#       401:
#         description:
#           if missing valid OAuth token or logged-in user lacks permission
#           to view requested patient

#     """
#     if not request.json or 'resourceType' not in request.json or\
#             request.json['resourceType'] != 'Organization':
#         abort(400, "Requires FHIR resourceType of 'Organization'")
#     org = Organization.query.get_or_404(organization_id)
#     try:
#         # As we allow partial updates, first obtain a full representation
#         # of this org, and update with any provided elements
#         complete = org.as_fhir(include_empties=True)
#         complete.update(request.json)
#         org.update_from_fhir(complete)
#     except MissingReference, e:
#         abort(400, str(e))
#     db.session.commit()
#     auditable_event("updated organization from input {}".format(
#         json.dumps(request.json)), user_id=current_user().id,
#         subject_id=current_user().id, context='organization')
#     OrgTree.invalidate_cache()
#     return jsonify(org.as_fhir(include_empties=False))
