from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

from typing import Type

from trench.backends.provider import get_mfa_handler
from trench.command.remove_backup_code import remove_backup_code_command
from trench.command.validate_backup_code import validate_backup_code_command
from trench.exceptions import InvalidCodeError, InvalidTokenError
from trench.models import MFAMethod
from trench.utils import get_mfa_model, user_token_generator, get_mfa_backup_code_model


User: AbstractUser = get_user_model()


class AuthenticateSecondFactorCommand:
    def __init__(self, mfa_model: Type[MFAMethod]) -> None:
        self._mfa_model = mfa_model

    def execute(self, code: str, ephemeral_token: str) -> User:
        user = user_token_generator.check_token(user=None, token=ephemeral_token)
        if user is None:
            raise InvalidTokenError()
        self.is_authenticated(user_id=user.id, code=code)
        return user

    def is_authenticated(self, user_id: int, code: str) -> None:
        for auth_method in self._mfa_model.objects.list_active(user_id=user_id):
            if get_mfa_handler(mfa_method=auth_method).validate_code(code=code):
                return

        mfa_backup_code = get_mfa_backup_code_model().objects.filter(user_id=user_id).first()
        if not mfa_backup_code:
            raise InvalidCodeError()

        validated_backup_code = validate_backup_code_command(
            value=code, backup_codes=mfa_backup_code.values
        )

        if validated_backup_code:
            remove_backup_code_command(
                user_id=user_id, code=code
            )
            return

        raise InvalidCodeError()


authenticate_second_step_command = AuthenticateSecondFactorCommand(
    mfa_model=get_mfa_model()
).execute
