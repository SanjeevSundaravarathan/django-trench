from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import AbstractUser

from rest_framework.request import Request

from trench.exceptions import UnauthenticatedError


User: AbstractUser = get_user_model()


class AuthenticateUserCommand:
    @staticmethod
    def execute(request: Request, username: str, password: str) -> User:
        try:
            user_with_matching_email = User.objects.get(email__iexact=username)
            username = user_with_matching_email.email
        except User.DoesNotExist:
            raise UnauthenticatedError()

        user = authenticate(
            request=request,
            username=username,
            password=password,
        )
        if user is None:
            raise UnauthenticatedError()
        return user


authenticate_user_command = AuthenticateUserCommand.execute
