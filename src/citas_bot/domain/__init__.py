"""Domain entities (SQLAlchemy 2.0 declarative models)."""

from citas_bot.domain.appointment import Appointment, AppointmentStatus
from citas_bot.domain.base import Base
from citas_bot.domain.conversation import Conversation
from citas_bot.domain.customer import Customer

__all__ = [
    "Appointment",
    "AppointmentStatus",
    "Base",
    "Conversation",
    "Customer",
]
