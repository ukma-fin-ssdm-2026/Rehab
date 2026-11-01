"""Register all shared ORM models without opening database connections."""

from backend.app.db.models.avatar import UserAvatar
from backend.app.db.models.complaint import Complaint
from backend.app.db.models.email_delivery import EmailReminderDelivery
from backend.app.db.models.entry import DayRecord
from backend.app.db.models.goal import Goal
from backend.app.db.models.mentorship import Mentorship
from backend.app.db.models.notification import Notification
from backend.app.db.models.support_comment import SupportComment
from backend.app.db.models.user import User

__all__ = [
    "User",
    "DayRecord",
    "Goal",
    "UserAvatar",
    "Mentorship",
    "Notification",
    "SupportComment",
    "Complaint",
    "EmailReminderDelivery",
]
