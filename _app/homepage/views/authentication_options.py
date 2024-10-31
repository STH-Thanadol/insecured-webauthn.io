import json

from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from webauthn import options_to_json

from homepage.services import AuthenticationService, CredentialService, SessionService
from homepage.forms import AuthenticationOptionsRequestForm
from homepage.response import JsonResponseBadRequest


@csrf_exempt
def authentication_options(request: HttpRequest) -> JsonResponse:
    body_json: dict = json.loads(request.body)

    options_form = AuthenticationOptionsRequestForm(body_json)

    if not options_form.is_valid():
        return JsonResponseBadRequest(dict(options_form.errors.items()))

    form_data = options_form.cleaned_data
    options_username: str | None = form_data["username"]
    options_user_verification = form_data["user_verification"]
    options_challenge_generation = form_data["challenge_generation"]

    authentication_service = AuthenticationService()
    session_service = SessionService()

    existing_credentials = []
    if options_username:
        credential_service = CredentialService()
        existing_credentials = credential_service.retrieve_credentials_by_username(
            username=options_username
        )

        if len(existing_credentials) == 0:
            return JsonResponseBadRequest({"error": "That username has no registered credentials"})

    authentication_options = authentication_service.generate_authentication_options(
        cache_key=session_service.get_session_key(request=request),
        user_verification=options_user_verification,
        challenge_generation=options_challenge_generation,
        existing_credentials=existing_credentials,
    )

    return JsonResponse(json.loads(options_to_json(authentication_options)))
