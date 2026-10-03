"""Specific refusal reasons of the send-service. Each carries a stable ``code`` for audit/UX."""

from __future__ import annotations


class SendError(Exception):
    """Base class for everything the send-service can raise."""

    code = "error"


class SendRefused(SendError):
    """The message was NOT handed to the transport."""

    code = "refused"


class KillSwitchEngaged(SendRefused):
    code = "kill_switch"


class HashMismatch(SendRefused):
    """Approval does not cover these exact bytes, or the prepared message was altered."""

    code = "hash_mismatch"


class UnknownApproval(SendRefused):
    """No such approval, or it differs from the record the approval service issued."""

    code = "unknown_approval"


class WrongApprovalKind(SendRefused):
    code = "wrong_approval_kind"


class ApprovalExpired(SendRefused):
    code = "approval_expired"


class NonceReplayed(SendRefused):
    code = "nonce_replayed"


class TenantMismatch(SendRefused):
    code = "tenant_mismatch"


class RecipientNotVendor(SendRefused):
    code = "recipient_not_vendor"


class VendorOptedOut(SendRefused):
    code = "vendor_opted_out"


class DomainMismatch(SendRefused):
    """Recipient domain differs from the vendor's registered domain (R12)."""

    code = "domain_mismatch"


class FooterMissing(SendRefused):
    """The mandatory AI-disclosure footer (R8) is absent or does not name the sender."""

    code = "footer_missing"


class IdentityMissing(SendRefused):
    """A business-identity line the deployment requires (company particulars) is absent or empty.

    The text names the missing labels only; it never echoes a value."""

    code = "identity_missing"


class MalformedMessage(SendRefused):
    code = "malformed_message"


class UnsafeText(MalformedMessage):
    """The bytes hold a control, line-break or hidden character where the sanitiser keeps it out (a
    one-line header text, or the body). ``prepare`` never builds such bytes; this is the send-time
    re-check for bytes that did not come from it. The text names the kinds of field, never their
    text."""

    code = "unsafe_text"


class StandingRuleViolation(SendRefused):
    code = "standing_rule_violation"


class CapRefused(SendRefused):
    """Per-order or daily aggregate cap (R9)."""

    code = "cap_exceeded"


class DuplicateSend(SendRefused):
    code = "duplicate_send"


class RecipientLimitExceeded(SendRefused):
    code = "recipient_limit"


class VendorMissing(SendRefused):
    """The vendor a follow-up plan was made for no longer exists for its tenant. Audit only: the
    plan is cancelled for good, nothing is sent."""

    code = "vendor_missing"


class FollowUpCancelled(SendRefused):
    """A pending follow-up plan was stopped on request (for example because the vendor replied).
    Audit only: it records that the next follow-up will not be sent."""

    code = "follow_up_cancelled"


class TransportFailure(SendError):
    """The transport was called and failed. Delivery is unknown, so the approval stays used."""

    code = "transport_failure"
