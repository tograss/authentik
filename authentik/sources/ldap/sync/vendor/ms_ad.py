"""Active Directory specific"""

from collections.abc import Generator
from enum import IntFlag
from typing import Any

from authentik.core.models import User
from authentik.sources.ldap.sync.base import BaseLDAPSynchronizer


class UserAccountControl(IntFlag):
    """UserAccountControl attribute for Active directory users"""

    # https://docs.microsoft.com/en-us/troubleshoot/windows-server/identity
    #   /useraccountcontrol-manipulate-account-properties

    SCRIPT = 1
    ACCOUNTDISABLE = 2
    HOMEDIR_REQUIRED = 8
    LOCKOUT = 16
    PASSWD_NOTREQD = 32
    PASSWD_CANT_CHANGE = 64
    ENCRYPTED_TEXT_PWD_ALLOWED = 128
    TEMP_DUPLICATE_ACCOUNT = 256
    NORMAL_ACCOUNT = 512
    INTERDOMAIN_TRUST_ACCOUNT = 2048
    WORKSTATION_TRUST_ACCOUNT = 4096
    SERVER_TRUST_ACCOUNT = 8192
    DONT_EXPIRE_PASSWORD = 65536
    MNS_LOGON_ACCOUNT = 131072
    SMARTCARD_REQUIRED = 262144
    TRUSTED_FOR_DELEGATION = 524288
    NOT_DELEGATED = 1048576
    USE_DES_KEY_ONLY = 2097152
    DONT_REQ_PREAUTH = 4194304
    PASSWORD_EXPIRED = 8388608
    TRUSTED_TO_AUTH_FOR_DELEGATION = 16777216
    PARTIAL_SECRETS_ACCOUNT = 67108864


class MicrosoftActiveDirectory(BaseLDAPSynchronizer):
    """Microsoft-specific LDAP"""

    @staticmethod
    def name() -> str:
        return "microsoft_ad"

    def get_objects(self, **kwargs) -> Generator:
        yield None

    def sync(self, attributes: dict[str, Any], user: User, created: bool):
        self.check_pwd_last_set("pwdLastSet", attributes, user, created)
        self.ms_check_uac(attributes, user)

    def ms_check_uac(self, attributes: dict[str, Any], user: User):
        """Check userAccountControl"""
        if "userAccountControl" not in attributes:
            return
        # Default from https://docs.microsoft.com/en-us/troubleshoot/windows-server/identity
        #   /useraccountcontrol-manipulate-account-properties
        uac_bit = attributes.get("userAccountControl", 512)
        uac = UserAccountControl(uac_bit)
        is_active = (
            UserAccountControl.ACCOUNTDISABLE not in uac and UserAccountControl.LOCKOUT not in uac
        )
        if is_active != user.is_active:
            user.is_active = is_active
            user.save()
