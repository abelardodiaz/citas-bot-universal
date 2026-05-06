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
KEYWORD_CANCEL_INTENT = ("cancelar cita", "cancela mi", "cancelar mi")
KEYWORD_RESCHEDULE = ("cambiar", "reagendar", "reprogramar", "mover")
KEYWORD_LIST = ("mis citas", "que citas", "cuales citas", "ver citas", "tengo cita")
KEYWORD_HANDOFF = ("humano", "persona", "asesor", "doctor", "encargado")

# Cancel
CANCEL_NO_APPOINTMENTS = "No tienes citas activas para cancelar."
CANCEL_PICK_TPL = "Cuales citas tienes activas:\n{listing}\nResponde con el numero a cancelar."
CANCEL_INVALID_PICK = "No entendi. Responde con el numero (ejemplo: 1)."
CANCEL_CONFIRM_TPL = "?Confirmas cancelar la cita del {when}? Responde si o no."
CANCEL_DONE_TPL = "Listo, cancele tu cita del {when}."

# Reschedule
RESCHEDULE_NO_APPOINTMENTS = "No tienes citas activas para reprogramar."
RESCHEDULE_PICK_TPL = (
    "Cuales citas tienes activas:\n{listing}\n"
    "Responde con el numero a reprogramar."
)
RESCHEDULE_ASK_DATE = "Para que dia la quieres mover?"
RESCHEDULE_DONE_TPL = "Listo, tu cita ahora es el {when}."

# list_mine
LIST_NONE = "No tienes citas activas."
LIST_HEADER = "Tus citas:\n{listing}"

# handoff
HANDOFF_DONE = (
    "Aviso al equipo. En unos momentos alguien te respondera. "
    "Mientras tanto puedes seguir escribiendo aqui."
)
