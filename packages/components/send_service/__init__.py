"""Send-service: the only module that may hold or call the mail transport (R1, ADR-003)."""

from .errors import IdentityMissing, SendError, SendRefused
from .service import (
    DEFAULT_IDENTITY_LABELS,
    FOOTER_TEMPLATE,
    NO_FOLLOW_UPS,
    FollowUpSchedule,
    KillSwitch,
    MessagePurpose,
    PreparedMessage,
    SendService,
)

__all__ = [
    "DEFAULT_IDENTITY_LABELS",
    "FOOTER_TEMPLATE",
    "NO_FOLLOW_UPS",
    "FollowUpSchedule",
    "IdentityMissing",
    "KillSwitch",
    "MessagePurpose",
    "PreparedMessage",
    "SendError",
    "SendRefused",
    "SendService",
]
