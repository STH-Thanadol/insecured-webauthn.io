from django import forms


class RegistrationOptionsRequestForm(forms.Form):
    username = forms.CharField(required=True, max_length=64)
    user_verification = forms.ChoiceField(
        required=True,
        choices=[
            ("discouraged", "Discouraged"),
            ("preferred", "Preferred"),
            ("required", "Required"),
        ],
    )
    attestation = forms.ChoiceField(
        required=True,
        choices=[
            ("none", "None"),
            ("direct", "Direct"),
        ],
    )
    attachment = forms.ChoiceField(
        required=True,
        choices=[
            ("all", "All Supported"),
            ("cross_platform", "Cross-Platform"),
            ("platform", "Platform"),
        ],
    )
    algorithms = forms.MultipleChoiceField(
        required=False, choices=[("es256", "ES256"), ("eddsa", "EDDSA"), ("es512", "ES512"), ("pss256", "PSS256"), ("pss384", "PSS384"), ("pss512", "PSS512"), ("rs256", "RS256"), ("rs384", "RS384"), ("rs512", "RS512"), ("rs1", "RS1")]
    )
    discoverable_credential = forms.ChoiceField(
        required=True,
        choices=[
            ("discouraged", "Discouraged"),
            ("preferred", "Preferred"),
            ("required", "Required"),
        ],
    )
    hints = forms.MultipleChoiceField(
        required=False,
        choices=[
            ("security-key", "Security Key"),
            ("client-device", "Client Device"),
            ("hybrid", "Hybrid"),
        ],
    )


class RegistrationResponseForm(forms.Form):
    username = forms.CharField(required=True, max_length=64)
    response = forms.JSONField(required=True)


class AuthenticationOptionsRequestForm(forms.Form):
    username = forms.CharField(required=False, max_length=64)
    user_verification = forms.ChoiceField(
        required=True,
        choices=[
            ("discouraged", "Discouraged"),
            ("preferred", "Preferred"),
            ("required", "Required"),
        ],
    )


class AuthenticationResponseForm(forms.Form):
    username = forms.CharField(required=False, max_length=64)
    response = forms.JSONField(required=True)
