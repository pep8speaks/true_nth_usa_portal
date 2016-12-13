"""Clinical API view functions"""
from flask import abort, Blueprint, jsonify
from flask import request

from ..audit import auditable_event
from ..models.audit import Audit
from ..models.fhir import CC, ValueQuantity
from ..models.user import current_user, get_user
from ..extensions import oauth
from ..extensions import db

clinical_api = Blueprint('clinical_api', __name__, url_prefix='/api')


@clinical_api.route('/patient/<int:patient_id>/clinical/biopsy')
@oauth.require_oauth()
def biopsy(patient_id):
    """Simplified API for getting clinical biopsy data w/o FHIR

    Returns 'true', 'false' or 'unknown' for the patient's clinical biopsy
    value in JSON, i.e. '{"value": true}'
    ---
    tags:
      - Clinical
    operationId: getBiopsy
    produces:
      - application/json
    parameters:
      - name: patient_id
        in: path
        description: TrueNTH patient ID
        required: true
        type: integer
        format: int64
    responses:
      200:
        description:
          Returns clinical biopsy information for requested portal user id
      401:
        description:
          if missing valid OAuth token or logged-in user lacks permission
          to view requested patient

    """
    return clinical_api_shortcut_get(patient_id=patient_id,
                                     codeable_concept=CC.BIOPSY)


@clinical_api.route('/patient/<int:patient_id>/clinical/pca_diag')
@oauth.require_oauth()
def pca_diag(patient_id):
    """Simplified API for getting clinical PCa diagnosis status w/o FHIR

    Returns 'true', 'false' or 'unknown' for the patient's clinical PCa
    diagnosis value in JSON, i.e. '{"value": true}'
    ---
    tags:
      - Clinical
    operationId: getPCaDiagnosis
    produces:
      - application/json
    parameters:
      - name: patient_id
        in: path
        description: TrueNTH patient ID
        required: true
        type: integer
        format: int64
    responses:
      200:
        description:
          Returns 'true', 'false' or 'unknown' for the patient's clinical PCa
          diagnosis value in JSON
      401:
        description:
          if missing valid OAuth token or logged-in user lacks permission
          to view requested patient

    """
    return clinical_api_shortcut_get(patient_id=patient_id,
                                     codeable_concept=CC.PCaDIAG)


@clinical_api.route('/patient/<int:patient_id>/clinical/pca_localized')
@oauth.require_oauth()
def pca_localized(patient_id):
    """Simplified API for getting clinical PCaLocalized status w/o FHIR

    Returns 'true', 'false' or 'unknown' for the patient's clinical
    PCaLocalized diagnosis value in JSON, i.e. '{"value": true}'
    ---
    tags:
      - Clinical
    operationId: getPCaLocalized
    produces:
      - application/json
    parameters:
      - name: patient_id
        in: path
        description: TrueNTH patient ID
        required: true
        type: integer
        format: int64
    responses:
      200:
        description:
          Returns 'true', 'false' or 'unknown' for the patient's clinical
          PCaLocalized diagnosis value in JSON
      401:
        description:
          if missing valid OAuth token or logged-in user lacks permission
          to view requested patient

    """
    return clinical_api_shortcut_get(patient_id=patient_id,
                                     codeable_concept=CC.PCaLocalized)


@clinical_api.route('/patient/<int:patient_id>/clinical/tx')
@oauth.require_oauth()
def treatment(patient_id):
    """Simplified API for getting clinical treatment begun status w/o FHIR

    Returns 'true', 'false' or 'unknown' for the patient's clinical treatment
    begun value in JSON, i.e. '{"value": true}'
    ---
    tags:
      - Clinical
    operationId: getTx
    produces:
      - application/json
    parameters:
      - name: patient_id
        in: path
        description: TrueNTH patient ID
        required: true
        type: integer
        format: int64
    responses:
      200:
        description:
          Returns 'true', 'false' or 'unknown' for the patient's clinical
          treatment begun status in JSON
      401:
        description:
          if missing valid OAuth token or logged-in user lacks permission
          to view requested patient

    """
    return clinical_api_shortcut_get(patient_id=patient_id,
                                     codeable_concept=CC.TX)


@clinical_api.route('/patient/<int:patient_id>/clinical/biopsy',
                    methods=('POST', 'PUT'))
@oauth.require_oauth()
def biopsy_set(patient_id):
    """Simplified API for setting clinical biopsy data w/o FHIR

    Requires a simple JSON doc to set value for biopsy: '{"value": true}'

    Returns a json friendly message, i.e. '{"message": "ok"}'

    Raises 401 if logged-in user lacks permission to edit requested
    patient.

    ---
    operationId: setBiopsy
    tags:
      - Clinical
    produces:
      - application/json
    parameters:
      - name: patient_id
        in: path
        description: TrueNTH patient ID
        required: true
        type: integer
        format: int64
      - in: body
        name: body
        schema:
          id: Biopsy
          required:
            - value
          properties:
            value:
              type: boolean
              description: has the patient undergone a biopsy
    responses:
      200:
        description: successful operation
        schema:
          id: response
          required:
            - message
          properties:
            message:
              type: string
              description: Result, typically "ok"
      401:
        description:
          if missing valid OAuth token or logged-in user lacks permission
          to view requested patient

    """
    return clinical_api_shortcut_set(patient_id=patient_id,
                                     codeable_concept=CC.BIOPSY)


@clinical_api.route('/patient/<int:patient_id>/clinical/pca_diag',
                    methods=('POST', 'PUT'))
@oauth.require_oauth()
def pca_diag_set(patient_id):
    """Simplified API for setting clinical PCa diagnosis status w/o FHIR

    Requires a simple JSON doc to set PCa diagnosis: '{"value": true}'

    Raises 401 if logged-in user lacks permission to edit requested
    patient.

    ---
    operationId: setPCaDiagnosis
    tags:
      - Clinical
    produces:
      - application/json
    parameters:
      - name: patient_id
        in: path
        description: TrueNTH patient ID
        required: true
        type: integer
        format: int64
      - in: body
        name: body
        schema:
          id: PCaDiagnosis
          required:
            - value
          properties:
            value:
              type: boolean
              description: the patient's PCa diagnosis
    responses:
      200:
        description: successful operation
        schema:
          id: response
          required:
            - message
          properties:
            message:
              type: string
              description: Result, typically "ok"
      401:
        description:
          if missing valid OAuth token or logged-in user lacks permission
          to view requested patient

    """
    return clinical_api_shortcut_set(patient_id=patient_id,
                                     codeable_concept=CC.PCaDIAG)


@clinical_api.route('/patient/<int:patient_id>/clinical/pca_localized',
                    methods=('POST', 'PUT'))
@oauth.require_oauth()
def pca_localized_set(patient_id):
    """Simplified API for setting clinical PCa localizedstatus w/o FHIR

    Requires simple JSON doc to set PCaLocalized diagnosis: '{"value": true}'

    Raises 401 if logged-in user lacks permission to edit requested
    patient.

    ---
    operationId: setPCaLocalized
    tags:
      - Clinical
    produces:
      - application/json
    parameters:
      - name: patient_id
        in: path
        description: TrueNTH patient ID
        required: true
        type: integer
        format: int64
      - in: body
        name: body
        schema:
          id: PCaLocalized
          required:
            - value
          properties:
            value:
              type: boolean
              description: the patient's PCaLocalized diagnosis
    responses:
      200:
        description: successful operation
        schema:
          id: response
          required:
            - message
          properties:
            message:
              type: string
              description: Result, typically "ok"
      401:
        description:
          if missing valid OAuth token or logged-in user lacks permission
          to view requested patient

    """
    return clinical_api_shortcut_set(patient_id=patient_id,
                                     codeable_concept=CC.PCaLocalized)


@clinical_api.route('/patient/<int:patient_id>/clinical/tx',
                    methods=('POST', 'PUT'))
@oauth.require_oauth()
def tx_set(patient_id):
    """Simplified API for setting clinical treatment status w/o FHIR

    Requires a simple JSON doc to set treatment status: '{"value": true}'

    Raises 401 if logged-in user lacks permission to edit requested
    patient.

    ---
    operationId: setTx
    tags:
      - Clinical
    produces:
      - application/json
    parameters:
      - name: patient_id
        in: path
        description: TrueNTH patient ID
        required: true
        type: integer
        format: int64
      - in: body
        name: body
        schema:
          id: Tx
          required:
            - value
          properties:
            value:
              type: boolean
              description: the patient's treatment status
    responses:
      200:
        description: successful operation
        schema:
          id: response
          required:
            - message
          properties:
            message:
              type: string
              description: Result, typically "ok"
      401:
        description:
          if missing valid OAuth token or logged-in user lacks permission
          to view requested patient

    """
    return clinical_api_shortcut_set(patient_id=patient_id,
                                     codeable_concept=CC.TX)


@clinical_api.route('/patient/<int:patient_id>/clinical')
@oauth.require_oauth()
def clinical(patient_id):
    """Access clinical data as a FHIR bundle of observations (in JSON)

    Returns a patient's clinical data (eg TNM, Gleason score) as a FHIR
    bundle of observations (http://www.hl7.org/fhir/observation.html)
    in JSON.
    ---
    tags:
      - Clinical
    operationId: getPatientObservations
    produces:
      - application/json
    parameters:
      - name: patient_id
        in: path
        description: TrueNTH patient ID
        required: true
        type: integer
        format: int64
    responses:
      200:
        description:
          Returns clinical information for requested portal user id as a
          FHIR bundle of observations
          (http://www.hl7.org/fhir/observation.html) in JSON.
      401:
        description:
          if missing valid OAuth token or logged-in user lacks permission
          to view requested patient

    """
    current_user().check_role(permission='view', other_id=patient_id)
    patient = get_user(patient_id)
    if patient.deleted:
        abort(400, "deleted user - operation not permitted")
    return jsonify(patient.clinical_history(requestURL=request.url))


@clinical_api.route('/patient/<int:patient_id>/clinical',
                    methods=('POST', 'PUT'))
@oauth.require_oauth()
def clinical_set(patient_id):
    """Add clinical entry via FHIR Resource Observation

    Submit a minimal FHIR doc in JSON format including the 'Observation'
    resource type, and any fields to retain.  NB, only a subset
    are persisted in the portal including {"name"(CodeableConcept),
    "valueQuantity", "status", "issued", "performer"} - others will be ignored.

    Returns details of the change in the json 'message' field.

    If *performer* isn't defined, the current user is assumed.

    Raises 401 if logged-in user lacks permission to edit requested
    patient.

    ---
    operationId: setPatientObservation
    tags:
      - Clinical
    produces:
      - application/json
    parameters:
      - name: patient_id
        in: path
        description: TrueNTH patient ID
        required: true
        type: integer
        format: int64
      - in: body
        name: body
        schema:
          id: FHIRObservation
          required:
            - resourceType
          properties:
            resourceType:
              type: string
              description:
                defines FHIR resource type, must be Observation
                http://www.hl7.org/fhir/observation.html
    responses:
      200:
        description: successful operation
        schema:
          id: response
          required:
            - message
          properties:
            message:
              type: string
              description: details of the change
      401:
        description:
          if missing valid OAuth token or logged-in user lacks permission
          to view requested patient

    """
    current_user().check_role(permission='edit', other_id=patient_id)
    patient = get_user(patient_id)
    if patient.deleted:
        abort(400, "deleted user - operation not permitted")
    if not request.json or 'resourceType' not in request.json or\
            request.json['resourceType'] != 'Observation':
        abort(400, "Requires FHIR resourceType of 'Observation'")
    audit = Audit(user_id=current_user().id)
    code, result = patient.add_observation(request.json, audit)
    if code != 200:
        abort(code, result)
    db.session.commit()
    auditable_event(result, user_id=current_user().id)
    return jsonify(message=result)


def clinical_api_shortcut_set(patient_id, codeable_concept):
    """Helper for common code used in clincal api shortcuts"""
    current_user().check_role(permission='edit', other_id=patient_id)
    patient = get_user(patient_id)
    if patient.deleted:
        abort(400, "deleted user - operation not permitted")

    if not request.json or 'value' not in request.json:
        abort(400, "Expects 'value' in JSON")
    value = str(request.json['value']).lower()
    if value not in ('true', 'false'):
        abort(400, "Expecting boolean for 'value'")

    truthiness = ValueQuantity(value=value, units='boolean')
    patient.save_constrained_observation(codeable_concept=codeable_concept,
                                         value_quantity=truthiness,
                                         audit=Audit(user_id=current_user().id))
    db.session.commit()
    auditable_event("set {0} {1} on user {2}".format(
        codeable_concept, truthiness, patient_id), user_id=current_user().id)
    return jsonify(message='ok')


def clinical_api_shortcut_get(patient_id, codeable_concept):
    """Helper for common code used in clincal api shortcuts"""
    current_user().check_role(permission='view', other_id=patient_id)
    patient = get_user(patient_id)
    if patient.deleted:
        abort(400, "deleted user - operation not permitted")
    value_quantities = patient.fetch_values_for_concept(codeable_concept)
    if value_quantities:
        assert len(value_quantities) == 1
        return jsonify(value=value_quantities[0].value)

    return jsonify(value='unknown')