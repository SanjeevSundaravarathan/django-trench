from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db.models import Model

from abc import abstractmethod
from rest_framework.authtoken.models import Token
from rest_framework.fields import CharField, ChoiceField
from rest_framework.serializers import ModelSerializer, Serializer
from typing import Any, OrderedDict

from trench.backends.provider import get_mfa_handler
from trench.command.remove_backup_code import remove_backup_code_command
from trench.command.validate_backup_code import validate_backup_code_command
from trench.exceptions import (
    CodeInvalidOrExpiredError,
    MFAMethodAlreadyActiveError,
    MFAMethodDoesNotExistError,
    MFANotEnabledError,
    OTPCodeMissingError,
)
from trench.models import MFAMethod
from trench.settings import trench_settings
from trench.utils import available_method_choices, get_mfa_model, get_mfa_backup_code_model


User: AbstractUser = get_user_model()


class RequestBodyValidator(Serializer):
    def update(self, instance: Model, validated_data: OrderedDict[str, Any]):
        raise NotImplementedError

    def create(self, validated_data: OrderedDict[str, Any]):
        raise NotImplementedError


class MFAMethodBackupCodesGenerationValidator(RequestBodyValidator):
    code = CharField(
        required=trench_settings.CONFIRM_BACKUP_CODES_REGENERATION_WITH_CODE
    )

    @staticmethod
    def _get_validation_method_name() -> str:
        return "validate_code"

    def __init__(self, user: User, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._user = user

    def validate_code(self, value: str) -> str:
        if not value:
            raise OTPCodeMissingError()

        mfa_backup_code_model = get_mfa_backup_code_model()

        mfa_backup_code = mfa_backup_code_model.objects.filter(user_id=self._user.id).first()

        validated_backup_code = False
        if mfa_backup_code:
            validated_backup_code = validate_backup_code_command(
                value=value, backup_codes=mfa_backup_code.values
            )

        if mfa_backup_code and validated_backup_code:
            remove_backup_code_command(
                user_id=self._user.id, code=value
            )
            return value

        for auth_method in get_mfa_model().objects.list_active(user_id=self._user.id):
            if get_mfa_handler(mfa_method=auth_method).validate_code(code=value):
                return value

        raise CodeInvalidOrExpiredError()


class ProtectedActionValidator(RequestBodyValidator):
    code = CharField()

    @staticmethod
    def _get_validation_method_name() -> str:
        return "validate_code"

    @staticmethod
    @abstractmethod
    def _validate_mfa_method(mfa: MFAMethod) -> None:
        raise NotImplementedError

    def __init__(self, mfa_method_name: str, user: User, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._user = user
        self._mfa_method_name = mfa_method_name

    def validate_code(self, value: str) -> str:
        if not value:
            raise OTPCodeMissingError()
        mfa_model = get_mfa_model()
        mfa_backup_code_model = get_mfa_backup_code_model()
        mfa = mfa_model.objects.get_by_name(
            user_id=self._user.id, name=self._mfa_method_name
        )
        mfa_backup_code = mfa_backup_code_model.objects.filter(user_id=self._user.id).first()
        self._validate_mfa_method(mfa)

        validated_backup_code = False
        if mfa_backup_code:
            validated_backup_code = validate_backup_code_command(
                value=value, backup_codes=mfa_backup_code.values
            )

        handler = get_mfa_handler(mfa)
        validation_method = getattr(handler, self._get_validation_method_name())
        if validation_method(value):
            return value

        if mfa_backup_code and validated_backup_code:
            remove_backup_code_command(
                user_id=mfa.user_id, code=value
            )
            return value

        raise CodeInvalidOrExpiredError()


class MFAMethodDeactivationValidator(ProtectedActionValidator):
    code = CharField(required=trench_settings.CONFIRM_DISABLE_WITH_CODE)

    @staticmethod
    def _validate_mfa_method(mfa: MFAMethod) -> None:
        if not mfa.is_active:
            raise MFANotEnabledError()


class MFAMethodActivationConfirmationValidator(ProtectedActionValidator):
    @staticmethod
    def _get_validation_method_name() -> str:
        return "validate_confirmation_code"

    @staticmethod
    def _validate_mfa_method(mfa: MFAMethod) -> None:
        if mfa.is_active:
            raise MFAMethodAlreadyActiveError()


class MFAMethodCodeSerializer(RequestBodyValidator):
    method = CharField(max_length=255, required=False)

    @staticmethod
    def validate_method(value: str) -> str:
        if value and value not in trench_settings.MFA_METHODS:
            raise MFAMethodDoesNotExistError()
        return value


class MFAMethodResendCodeSerializer(MFAMethodCodeSerializer):
    email = CharField(max_length=255, required=True)
    ephemeral_token = CharField(max_length=255, required=True)


class LoginSerializer(RequestBodyValidator):
    password = CharField(write_only=True)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields[User.USERNAME_FIELD] = CharField()


class CodeLoginSerializer(RequestBodyValidator):
    ephemeral_token = CharField()
    code = CharField()


class UserMFAMethodSerializer(ModelSerializer):
    class Meta:
        model = get_mfa_model()
        fields = ("name", "is_primary")


class ChangePrimaryMethodCodeValidator(ProtectedActionValidator):
    @staticmethod
    def _validate_mfa_method(mfa: MFAMethod) -> None:
        pass


class ChangePrimaryMethodValidator(RequestBodyValidator):
    method = ChoiceField(choices=available_method_choices())


class TokenSerializer(ModelSerializer):
    auth_token = CharField(source="key")

    class Meta:
        model = Token
        fields = ("auth_token",)
