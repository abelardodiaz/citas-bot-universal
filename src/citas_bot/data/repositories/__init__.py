"""Repository layer: query encapsulation per aggregate."""

from citas_bot.data.repositories.appointment import AppointmentRepository
from citas_bot.data.repositories.conversation import ConversationRepository
from citas_bot.data.repositories.customer import CustomerRepository

__all__ = [
    "AppointmentRepository",
    "ConversationRepository",
    "CustomerRepository",
]
