"""Assessment Engine API view functions"""
from flask import abort, Blueprint, current_app, jsonify, request, redirect
from flask import session
from flask_swagger import swagger
import jsonschema

from ..audit import auditable_event
from ..models.auth import validate_client_origin
from ..models.fhir import FHIR_datetime, QuestionnaireResponse
from ..models.intervention import INTERVENTION
from ..models.user import current_user, get_user
from ..extensions import oauth
from ..extensions import db

assessment_engine_api = Blueprint('assessment_engine_api', __name__,
                                  url_prefix='/api')


@assessment_engine_api.route(
    '/patient/<int:patient_id>/assessment',
    defaults={'instrument_id': None},
)
@assessment_engine_api.route(
    '/patient/<int:patient_id>/assessment/<string:instrument_id>'
)
@oauth.require_oauth()
def assessment(patient_id, instrument_id):
    """Return a patient's responses to a questionnaire

    Retrieve a minimal FHIR doc in JSON format including the
    'QuestionnaireResponse' resource type.
    ---
    operationId: getQuestionnaireResponse
    tags:
      - Assessment Engine
    produces:
      - application/json
    parameters:
      - name: patient_id
        in: path
        description: TrueNTH patient ID
        required: true
        type: integer
        format: int64
      - name: instrument_id
        in: path
        description:
          ID of the instrument, eg "epic26", "eq5d"
        required: true
        type: string
        enum:
          - epic26
          - eq5d

    responses:
      200:
        description: successful operation
        schema:
          id: assessment_bundle
          required:
            - type
          properties:
            type:
                description:
                  Indicates the purpose of this bundle- how it was
                  intended to be used.
                type: string
                enum:
                  - document
                  - message
                  - transaction
                  - transaction-response
                  - batch
                  - batch-response
                  - history
                  - searchset
                  - collection
            link:
              description:
                A series of links that provide context to this bundle.
              items:
                properties:
                  relation:
                    description:
                      A name which details the functional use for
                      this link - see [[http://www.iana.org/assignments/link-relations/link-relations.xhtml]].
                  url:
                    description: The reference details for the link.
            total:
                description:
                  If a set of search matches, this is the total number of
                  matches for the search (as opposed to the number of
                  results in this bundle).
                type: integer
            entry:
              type: array
              items:
                $ref: "#/definitions/QuestionnaireResponse"
          example:
            entry:
            - resourceType: QuestionnaireResponse
              authored: '2016-01-22T20:32:17Z'
              status: completed
              identifier:
                value: '101.0'
                use: official
                label: cPRO survey session ID
              subject:
                display: patient demographics
                reference: https://stg.us.truenth.org/api/demographics/10015
              author:
                display: patient demographics
                reference: https://stg.us.truenth.org/api/demographics/10015
              source:
                display: patient demographics
                reference: https://stg.us.truenth.org/api/demographics/10015
              group:
                question:
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.1.5
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 5
                  linkId: epic26.1
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.2.4
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 4
                  linkId: epic26.2
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.3.2
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 1
                  linkId: epic26.3
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.4.3
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 2
                  linkId: epic26.4
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.5.1
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 0
                  linkId: epic26.5
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.6.2
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 1
                  linkId: epic26.6
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.7.3
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 2
                  linkId: epic26.7
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.8.4
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 3
                  linkId: epic26.8
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.9.2
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 2
                  linkId: epic26.9
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.10.1
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 0
                  linkId: epic26.10
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.11.2
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 1
                  linkId: epic26.11
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.12.3
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 2
                  linkId: epic26.12
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.13.4
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 3
                  linkId: epic26.13
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.14.5
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 4
                  linkId: epic26.14
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.15.4
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 4
                  linkId: epic26.15
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.16.2
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 2
                  linkId: epic26.16
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.17.1
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 1
                  linkId: epic26.17
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.18.1
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 1
                  linkId: epic26.18
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.19.3
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 3
                  linkId: epic26.19
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.20.2
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 2
                  linkId: epic26.20
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.21.4
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 4
                  linkId: epic26.21
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.22.1
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 0
                  linkId: epic26.22
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.23.2
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 1
                  linkId: epic26.23
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.24.3
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 2
                  linkId: epic26.24
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.25.3
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 2
                  linkId: epic26.25
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.26.3
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 2
                  linkId: epic26.26
              questionnaire:
                display: EPIC 26 Short Form
                reference: https://stg.us.truenth.org/api/questionnaires/epic26
            - resourceType: QuestionnaireResponse
              authored: '2016-03-11T23:47:28Z'
              status: completed
              identifier:
                value: '119.0'
                use: official
                label: cPRO survey session ID
              subject:
                display: patient demographics
                reference: https://stg.us.truenth.org/api/demographics/10015
              author:
                display: patient demographics
                reference: https://stg.us.truenth.org/api/demographics/10015
              source:
                display: patient demographics
                reference: https://stg.us.truenth.org/api/demographics/10015
              group:
                question:
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.1.1
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 1
                  linkId: epic26.1
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.2.1
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 1
                  linkId: epic26.2
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.3.3
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 2
                  linkId: epic26.3
                - answer: []
                  linkId: epic26.4
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.5.4
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 3
                  linkId: epic26.5
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.6.3
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 2
                  linkId: epic26.6
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.7.2
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 1
                  linkId: epic26.7
                - answer: []
                  linkId: epic26.8
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.9.3
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 3
                  linkId: epic26.9
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.10.5
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 4
                  linkId: epic26.10
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.11.2
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 1
                  linkId: epic26.11
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.12.2
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 1
                  linkId: epic26.12
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.13.4
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 3
                  linkId: epic26.13
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.14.1
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 0
                  linkId: epic26.14
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.15.5
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 5
                  linkId: epic26.15
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.16.2
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 2
                  linkId: epic26.16
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.17.1
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 1
                  linkId: epic26.17
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.18.4
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 4
                  linkId: epic26.18
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.19.4
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 4
                  linkId: epic26.19
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.20.2
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 2
                  linkId: epic26.20
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.21.5
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 5
                  linkId: epic26.21
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.22.1
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 0
                  linkId: epic26.22
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.23.2
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 1
                  linkId: epic26.23
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.24.3
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 2
                  linkId: epic26.24
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.25.4
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 3
                  linkId: epic26.25
                - answer:
                  - valueCoding:
                      system: https://stg.us.truenth.org/api/codings/assessment
                      code: epic26.26.5
                      extension:
                        url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                        valueDecimal: 4
                  linkId: epic26.26
              questionnaire:
                display: EPIC 26 Short Form
                reference: https://stg.us.truenth.org/api/questionnaires/epic26
            link:
              href: https://stg.us.truenth.org/api/patient/10015/assessment/epic26
              rel: self
            resourceType: Bundle
            total: 2
            type: searchset
            updated: '2016-03-14T20:47:26.282263Z'
      401:
        description:
          if missing valid OAuth token or logged-in user lacks permission
          to view requested patient

    """

    current_user().check_role(permission='view', other_id=patient_id)
    patient = get_user(patient_id)
    if patient.deleted:
        abort(400, "deleted user - operation not permitted")
    questionnaire_responses = QuestionnaireResponse.query.filter_by(user_id=patient_id).order_by(QuestionnaireResponse.authored.desc())

    if instrument_id is not None:
        questionnaire_responses = questionnaire_responses.filter(
            QuestionnaireResponse.document[
                ("questionnaire", "reference")
            ].astext.endswith(instrument_id)
        )

    documents = [qnr.document for qnr in questionnaire_responses]

    bundle = {
        'resourceType':'Bundle',
        'updated':FHIR_datetime.now(),
        'total':len(documents),
        'type': 'searchset',
        'link': {
            'rel':'self',
            'href':request.url,
        },
        'entry':documents,
    }

    return jsonify(bundle)


@assessment_engine_api.route('/patient/<int:patient_id>/assessment',
                             methods=('POST', 'PUT'))
@oauth.require_oauth()
def assessment_set(patient_id):
    """Add a questionnaire response to a patient's record

    Submit a minimal FHIR doc in JSON format including the 'QuestionnaireResponse'
    resource type.
    ---
    operationId: addQuestionnaireResponse
    tags:
      - Assessment Engine
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
          id: QuestionnaireResponse
          description:
            A patient's responses to a questionnaire (a set of instruments,
            some standardized, some not), and metadata about the presentation
            and context of the assessment session (date, etc).
          required:
            - status
          properties:
            status:
              externalDocs:
                url: http://hl7.org/implement/standards/fhir/DSTU2/questionnaireresponse-definitions.html#QuestionnaireResponse.status
              description:
                  The lifecycle status of the questionnaire response as a whole
              type: string
              enum:
                - in-progress
                - completed
            subject:
              schema:
                id: Reference
                type: object
                description: A reference from one resource to another
                properties:
                  reference:
                    type: string
                    externalDocs:
                      url: http://hl7.org/implement/standards/fhir/DSTU2/references-definitions.html#Reference.reference
                  display:
                    type: string
                    externalDocs:
                      url: http://hl7.org/implement/standards/fhir/DSTU2/references-definitions.html#Reference.display
            author:
              $ref: "#/definitions/Reference"
            authored:
              externalDocs:
                url: http://hl7.org/implement/standards/fhir/DSTU2/questionnaireresponse-definitions.html#QuestionnaireResponse.authored
              description: The datetime this resource was last updated
              type: string
              format: date-time
            source:
              $ref: "#/definitions/Reference"
            group:
              schema:
                id: group
                description:
                  A group of related questions or sub-groups. May only
                  contain either questions or groups
                properties:
                  group:
                    $ref: "#/definitions/group"
                  title:
                    type: string
                    description: Group name
                    externalDocs:
                      url: http://hl7.org/implement/standards/fhir/DSTU2/questionnaireresponse-definitions.html#QuestionnaireResponse.group.title
                  text:
                    type: string
                    description: Additional text for this group
                    externalDocs:
                      url: http://hl7.org/implement/standards/fhir/DSTU2/questionnaireresponse-definitions.html#QuestionnaireResponse.group.text
                  question:
                    description:
                      Set of questions within this group. The order of
                      questions within the group is relevant.
                    type: array
                    externalDocs:
                      url: http://hl7.org/implement/standards/fhir/DSTU2/questionnaireresponse-definitions.html#QuestionnaireResponse.group.question
                    items:
                      description: An individual question and related attributes
                      type: object
                      properties:
                        text:
                          type: string
                          description: Question text
                        answer:
                          type: array
                          description:
                            The respondent's answer(s) to the question
                          externalDocs:
                            url: http://hl7.org/implement/standards/fhir/DSTU2/questionnaireresponse-definitions.html#QuestionnaireResponse.group.question.answer
                          items:
                            description:
                              An individual answer to a question and related
                              attributes. May only contain a single `value[x]`
                              attribute
                            type: object
                            externalDocs:
                              url: http://hl7.org/implement/standards/fhir/DSTU2/questionnaireresponse-definitions.html#QuestionnaireResponse.group.question.answer.value_x_
                            properties:
                              valueBoolean:
                                type: boolean
                                description: Boolean value answer to a question
                              valueDecimal:
                                type: number
                                description: Decimal value answer to a question
                              valueInteger:
                                type: integer
                                description: Integer value answer to a question
                              valueDate:
                                type: string
                                format: date
                                description: Date value answer to a question
                              valueDateTime:
                                type: string
                                format: date-time
                                description: Datetime value answer to a question
                              valueInstant:
                                type: string
                                format: date-time
                                description: Instant value answer to a question
                              valueTime:
                                type: string
                                description: Time value answer to a question
                              valueString:
                                type: string
                                description: String value answer to a question
                              valueUri:
                                type: string
                                description: URI value answer to a question
                              valueAttachment:
                                type: object
                                description:
                                  Attachment value answer to a question
                              valueCoding:
                                type: object
                                description:
                                  Coding value answer to a question, may
                                  include score as FHIR extension
                                properties:
                                  system:
                                    description:
                                      Identity of the terminology system
                                    type: string
                                    format: uri
                                  version:
                                    description:
                                      Version of the system - if relevant
                                    type: string
                                  code:
                                    description:
                                      Symbol in syntax defined by the system
                                    type: string
                                  display:
                                    description:
                                      Representation defined by the system
                                    type: string
                                  userSelected:
                                    description:
                                      If this coding was chosen directly by
                                      the user
                                    type: boolean
                                  extension:
                                    description:
                                      Extension - Numerical value associated
                                      with the code
                                    type: object
                                    properties:
                                      url:
                                        description:
                                          Hardcoded reference to extension
                                        type: string
                                        format: uri
                                      valueDecimal:
                                        description: Numeric score value
                                        type: number
                              valueQuantity:
                                type: object
                                description:
                                  Quantity value answer to a question
                              valueReference:
                                type: object
                                description:
                                  Reference value answer to a question
                              group:
                                $ref: "#/definitions/group"
          example:
            resourceType: QuestionnaireResponse
            authored: '2016-03-11T23:47:28Z'
            status: completed
            identifier:
              value: '119.0'
              use: official
              label: cPRO survey session ID
            subject:
              display: patient demographics
              reference: https://stg.us.truenth.org/api/demographics/10015
            author:
              display: patient demographics
              reference: https://stg.us.truenth.org/api/demographics/10015
            source:
              display: patient demographics
              reference: https://stg.us.truenth.org/api/demographics/10015
            group:
              question:
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.1.1
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 1
                linkId: epic26.1
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.2.1
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 1
                linkId: epic26.2
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.3.3
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 2
                linkId: epic26.3
              - answer: []
                linkId: epic26.4
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.5.4
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 3
                linkId: epic26.5
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.6.3
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 2
                linkId: epic26.6
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.7.2
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 1
                linkId: epic26.7
              - answer: []
                linkId: epic26.8
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.9.3
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 3
                linkId: epic26.9
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.10.5
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 4
                linkId: epic26.10
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.11.2
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 1
                linkId: epic26.11
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.12.2
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 1
                linkId: epic26.12
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.13.4
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 3
                linkId: epic26.13
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.14.1
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 0
                linkId: epic26.14
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.15.5
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 5
                linkId: epic26.15
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.16.2
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 2
                linkId: epic26.16
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.17.1
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 1
                linkId: epic26.17
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.18.4
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 4
                linkId: epic26.18
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.19.4
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 4
                linkId: epic26.19
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.20.2
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 2
                linkId: epic26.20
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.21.5
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 5
                linkId: epic26.21
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.22.1
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 0
                linkId: epic26.22
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.23.2
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 1
                linkId: epic26.23
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.24.3
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 2
                linkId: epic26.24
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.25.4
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 3
                linkId: epic26.25
              - answer:
                - valueCoding:
                    system: https://stg.us.truenth.org/api/codings/assessment
                    code: epic26.26.5
                    extension:
                      url: https://hl7.org/fhir/StructureDefinition/iso21090-CO-value
                      valueDecimal: 4
                linkId: epic26.26
            questionnaire:
              display: EPIC 26 Short Form
              reference: https://stg.us.truenth.org/api/questionnaires/epic26
    responses:
      401:
        description:
          if missing valid OAuth token or logged-in user lacks permission
          to view requested patient
    """

    if not hasattr(request, 'json') or not request.json:
        return abort(400, 'Invalid request')

    # Verify the current user has permission to edit given patient
    current_user().check_role(permission='edit', other_id=patient_id)
    patient = get_user(patient_id)
    if patient.deleted:
        abort(400, "deleted user - operation not permitted")

    swag = swagger(current_app)

    draft4_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'type': 'object',
        'definitions': swag['definitions'],
    }

    validation_schema = 'QuestionnaireResponse'
    # Copy desired schema (to validate against) to outermost dict
    draft4_schema.update(swag['definitions'][validation_schema])

    response = {
        'ok': False,
        'message': 'error saving questionnaire reponse',
        'valid': False,
    }

    try:
        jsonschema.validate(request.json, draft4_schema)

    except jsonschema.ValidationError as e:
        response = {
            'ok': False,
            'message': e.message,
            'reference': e.schema,
        }
        return jsonify(response)

    response.update({
        'ok': True,
        'message': 'questionnaire response valid',
        'valid': True,
    })

    questionnaire_response = QuestionnaireResponse(
        user_id=patient_id,
        document=request.json,
    )

    db.session.add(questionnaire_response)
    db.session.commit()
    auditable_event("added {}".format(questionnaire_response),
                    user_id=current_user().id)
    response.update({'message': 'questionnaire response saved successfully'})
    return jsonify(response)


@assessment_engine_api.route('/present-assessment')
@oauth.require_oauth()
def present_assessment(instruments=None):
    """Request that TrueNTH present an assessment via the assessment engine

    Redirects to the first assessment engine instance that is capable of
    administering the requested assessment
    ---
    operationId: present_assessment
    tags:
      - Assessment Engine
    produces:
      - text/html
    parameters:
      - name: instrument_id
        in: query
        description:
          ID of the instrument, eg "epic26", "eq5d"
        required: true
        type: array
        items:
          type: string
          enum:
            - epic26
            - eq5d
        collectionFormat: multi
      - name: next
        in: query
        description: Intervention URL to return to after assessment completion
        required: true
        type: string
        format: url
    responses:
      303:
        description: successful operation
        headers:
          Location:
            description:
              URL registered with assessment engine used to provide given
              assessment
            type: string
            format: url
      401:
        description: if missing valid OAuth token or bad `next` parameter

    """
    # Todo: replace with proper models
    configured_instruments = current_app.config['INSTRUMENTS']

    queued_instruments = request.args.getlist('instrument_id')

    # Hack to allow deprecated API to piggyback
    # Remove when deprecated_present_assessment() is fully removed
    if instruments is not None:
        queued_instruments = instruments


    if set(queued_instruments) - set(configured_instruments):
        abort(
            404,
            "No matching assessment found: %s" % (
                ", ".join(set(queued_instruments) - set(configured_instruments))
            )
        )

    assessment_url = "%s/surveys/new_session?project=%s" % (
        INTERVENTION.ASSESSMENT_ENGINE.link_url,
        ",".join(queued_instruments),
    )

    if 'next' in request.args:
        next_url = request.args.get('next')

        # Validate next URL the same way CORS requests are
        validate_client_origin(next_url)

        current_app.logger.debug('storing session[assessment_return]: %s',
                                 next_url)
        session['assessment_return'] = next_url

    return redirect(assessment_url, code=303)

@assessment_engine_api.route('/present-assessment/<instrument_id>')
@oauth.require_oauth()
def deprecated_present_assessment(instrument_id):
    current_app.logger.warning(
        "use of depricated API %s from referer %s",
        request.url,
        request.headers.get('Referer'),
    )

    return present_assessment(instruments=[instrument_id,])

@assessment_engine_api.route('/complete-assessment')
@oauth.require_oauth()
def complete_assessment():
    """Return to the last intervention that requested an assessment be presented

    Redirects to the URL passed to TrueNTH when present-assessment was last
    called (if valid) or TrueNTH home
    ---
    operationId: complete_assessment
    tags:
      - Internal
    produces:
      - text/html
    responses:
      303:
        description: successful operation
        headers:
          Location:
            description:
              URL passed to TrueNTH when present-assessment was last
              called (if valid) or TrueNTH home
            type: string
            format: url
      401:
        description: if missing valid OAuth token

    """

    next_url = session.pop("assessment_return", "home")

    current_app.logger.debug("assessment complete, redirect to: %s", next_url)
    return redirect(next_url, code=303)