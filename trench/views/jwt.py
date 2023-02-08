from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings

from trench.views import MFAFirstStepMixin, MFASecondStepMixin, MFAStepMixin, User


class MFAJWTView(MFAStepMixin):
    def _successful_authentication_response(self, user: User) -> Response:
        token = self.create_token(user)
        return Response(data={"access": str(token)})

    def create_token(self, user):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        return token


class MFAFirstStepJWTView(MFAJWTView, MFAFirstStepMixin):
    pass


class MFASecondStepJWTView(MFAJWTView, MFASecondStepMixin):
    pass
