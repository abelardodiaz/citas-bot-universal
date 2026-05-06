"""User-facing strings, isolated for future i18n migration."""

# Book intent
BOOK_ASK_DATE = (
    "Para que dia te gustaria agendar tu cita? "
    'Puedes decirme algo como "manana", "lunes", o "12 de mayo".'
)
BOOK_ASK_TIME = "Perfecto. A que hora? Por ejemplo: \"10:00\" o \"3 de la tarde\"."
BOOK_ASK_NAME = "Y a nombre de quien queda la cita?"
BOOK_CONFIRM_TPL = (
    "Para confirmar: cita el {when} a nombre de {name}. "
    "?Es correcto? Responde si o no."
)
BOOK_DONE_TPL = (
    "Listo, te confirmo tu cita el {when} a nombre de {name}. "
    "Recibiras un recordatorio."
)
BOOK_CANCEL = "Cita cancelada. Puedes empezar de nuevo cuando quieras."
BOOK_INVALID_DATE = (
    "No entendi la fecha. Intenta con un formato como \"manana\" o "
    '"lunes 12 de mayo".'
)
BOOK_INVALID_TIME = (
    "No entendi la hora. Indicame algo como \"10:00\" o "
    '"3 de la tarde".'
)
BOOK_PAST_DATE = "Esa fecha ya paso. Por favor elige una fecha futura."
BOOK_OUT_OF_HOURS_TPL = "El horario es {hours}. Por favor elige una hora dentro de ese rango."
BOOK_DUPLICATE = "Ya tienes una cita en esa fecha y hora. Elige otro horario."
BOOK_RETRY_EXHAUSTED = (
    "Disculpa, no logre entenderte. Intenta empezar de nuevo escribiendo \"agendar\"."
)
BOOK_INVALID_NAME = "Por favor dime tu nombre (1 a 3 palabras)."

# Universal
KEYWORD_CANCEL = ("cancelar", "cancelo", "olvidalo", "olvídalo")
KEYWORD_NO = ("no",)
KEYWORD_YES = ("si", "sí", "claro", "confirmo")
KEYWORD_BOOK = ("agendar", "cita", "reservar", "agenda")
