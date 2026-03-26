from enum import StrEnum


class UserRole(StrEnum):
    client = "client"
    operator = "operator"
    admin = "admin"


class OrderStatus(StrEnum):
    draft = "draft"
    pending_payment = "pending_payment"
    payment_submitted = "payment_submitted"
    payment_review = "payment_review"
    processing = "processing"
    completed = "completed"
    cancelled = "cancelled"
    expired = "expired"
    rejected = "rejected"


class OrderEventType(StrEnum):
    created = "created"
    status_changed = "status_changed"
    attachment_added = "attachment_added"
    payment_marked = "payment_marked"
    quote_updated = "quote_updated"
    note = "note"
