"""Send-service: the only module that may hold or call the mail transport (R1, ADR-003)."""

from .errors import SendError, SendRefused
from .service import (
    FOOTER_TEMPLATE,
    NO_FOLLOW_UPS,
    FollowUpSchedule,
    KillSwitch,
    MessagePurpose,
    PreparedMessage,
    SendService,
)

__all__ = [
    "FOOTER_TEMPLATE",
    "NO_FOLLOW_UPS",
    "FollowUpSchedule",
    "KillSwitch",
    "MessagePurpose",
    "PreparedMessage",
    "SendError",
    "SendRefused",
    "SendService",
]
