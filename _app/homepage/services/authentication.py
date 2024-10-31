from typing import List, Union
from dataclasses import dataclass

from django.conf import settings
from webauthn import (
    generate_authentication_options,
    options_to_json,
    verify_authentication_response,
)
from webauthn.helpers import (
    base64url_to_bytes,
    parse_authentication_credential_json,
    parse_authentication_options_json,
)
from webauthn.helpers.structs import (
    PublicKeyCredentialRequestOptions,
    UserVerificationRequirement,
    PublicKeyCredentialDescriptor,
)

from homepage.services import RedisService
from homepage.models import WebAuthnCredential
from homepage.exceptions import InvalidAuthenticationResponse


@dataclass
class VerifiedAuthentication:
    """
    A custom version of py_webauthn's VerifiedAuthentication since it doesn't output username from
    the response
    """

    credential_id: bytes
    new_sign_count: int
    username: str


class AuthenticationService:
    redis: RedisService

    def __init__(self):
        self.redis = RedisService(db=3)

    def generate_authentication_options(
        self,
        *,
        cache_key: str,
        user_verification: str,
        challenge_generation: str = "",
        existing_credentials: List[WebAuthnCredential],
    ) -> PublicKeyCredentialRequestOptions:
        """
        Generate and store authentication options
        """

        if user_verification == "discouraged":
            _user_verification = UserVerificationRequirement.DISCOURAGED
        elif user_verification == "preferred":
            _user_verification = UserVerificationRequirement.PREFERRED
        elif user_verification == "required":
            _user_verification = UserVerificationRequirement.REQUIRED

        if challenge_generation == "random":
            _challenge = b""
        elif challenge_generation == "fixed":
            _challenge = b"1234567890"

        authentication_options = generate_authentication_options(
            rp_id=settings.RP_ID,
            user_verification=_user_verification,
            challenge=_challenge,
            allow_credentials=[
                PublicKeyCredentialDescriptor(
                    id=base64url_to_bytes(cred.id), transports=cred.transports
                )
                for cred in existing_credentials[-64:]
            ],
        )

        self._save_options(cache_key=cache_key, options=authentication_options)

        return authentication_options

    def verify_authentication_response(
        self,
        *,
        cache_key: str,
        existing_credential: WebAuthnCredential,
        response: dict,
    ) -> VerifiedAuthentication:
        credential = parse_authentication_credential_json(response)
        options = self._get_options(cache_key=cache_key)

        if not options:
            raise InvalidAuthenticationResponse(f"no options for user {cache_key}")

        require_user_verification = False
        if options.user_verification:
            require_user_verification = (
                options.user_verification == UserVerificationRequirement.REQUIRED
            )

        self._delete_options(cache_key=cache_key)

        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=options.challenge,
            expected_rp_id=settings.RP_ID,
            expected_origin=settings.RP_EXPECTED_ORIGIN,
            require_user_verification=require_user_verification,
            credential_public_key=base64url_to_bytes(existing_credential.public_key),
            credential_current_sign_count=existing_credential.sign_count,
        )

        confirmed_username = existing_credential.username

        return VerifiedAuthentication(
            credential_id=verification.credential_id,
            new_sign_count=verification.new_sign_count,
            username=confirmed_username,
        )

    def _save_options(self, *, cache_key: str, options: PublicKeyCredentialRequestOptions):
        """
        Store authentication options for the user so we can reference them later
        """
        expiration = options.timeout
        if type(expiration) is int:
            # Store them temporarily, for twice as long as we're telling WebAuthn how long it
            # should give the user to complete the WebAuthn ceremony
            expiration = int(expiration / 1000 * 2)
        else:
            # Default to two minutes since we default timeout to 60 seconds
            expiration = 120

        return self.redis.store(
            key=cache_key, value=options_to_json(options), expiration_seconds=expiration
        )

    def _get_options(self, *, cache_key: str) -> Union[PublicKeyCredentialRequestOptions, None]:
        """
        Attempt to retrieve saved authentication options for the user
        """
        options: str | None = self.redis.retrieve(key=cache_key)
        if options is None:
            return options

        return parse_authentication_options_json(options)

    def _delete_options(self, *, cache_key: str) -> int:
        return self.redis.delete(key=cache_key)
