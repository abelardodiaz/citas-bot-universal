"""Outbound messaging: sender stub for Meta Send API.

In M05 the sender only logs; the live HTTP call to Meta's Cloud API is
implemented in M07.
"""

from citas_bot.messaging.meta_sender import MetaSender
from citas_bot.messaging.sender import LogOnlySender, MessageSender

__all__ = ["LogOnlySender", "MessageSender", "MetaSender"]
