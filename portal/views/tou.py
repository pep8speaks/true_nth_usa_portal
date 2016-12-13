"""Views for Terms of Use"""
from flask import abort, jsonify, Blueprint, request

from ..extensions import db, oauth
from ..models.audit import Audit
from ..models.user import current_user, get_user
from ..models.tou import ToU


tou_api = Blueprint('tou_api', __name__, url_prefix='/api')

@tou_api.route('/user/<int:user_id>/tou')
@oauth.require_oauth()
def get_tou(user_id):
    """Access Terms of Use info for given user

    Returns ToU{'accepted': true|false} for requested user.
    ---
    tags:
      - Terms Of Use
    operationId: getToU
    produces:
      - application/json
    parameters:
      - name: user_id
        in: path
        description: TrueNTH user ID
        required: true
        type: integer
        format: int64
    responses:
      200:
        description:
          Returns 'accepted' True or False for requested user.
      401:
        description:
          if missing valid OAuth token or logged-in user lacks permission
          to view requested patient

    """
    user = get_user(user_id)
    if not user:
        abort(404)
    current_user().check_role(permission='view', other_id=user_id)
    tous = ToU.query.join(Audit).filter(Audit.user_id==user_id).first()
    if tous:
        return jsonify(accepted=True)
    return jsonify(accepted=False)


@tou_api.route('/tou/accepted', methods=('POST',))
@oauth.require_oauth()
def accept_tou():
    """Accept Terms of Use info for authenticated user

    POST simple JSON describing ToU the user accepted for persistence.

    ---
    tags:
      - Terms Of Use
    operationId: acceptToU
    produces:
      - application/json
    parameters:
      - name: body
        in: body
        schema:
          id: acceptedToU
          description: Details of accepted ToU
          required:
            - text
          properties:
            text:
              description: Full text agreed to
              type: string
    responses:
      200:
        description: message detailing success
      400:
        description: if the required JSON is ill formed
      401:
        description:
          if missing valid OAuth token or logged-in user lacks permission
          to view requested patient

    """
    user = current_user()
    if not request.json or 'text' not in request.json:
        abort(400, "Requires JSON with the ToU 'text'")
    audit = Audit(user_id = user.id, comment = "ToU accepted")
    tou = ToU(audit=audit, text=request.json['text'])
    db.session.add(tou)
    db.session.commit()
    # Note: skipping auditable_event, as there's a audit row created above
    return jsonify(message="accepted")