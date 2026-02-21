TOOLS_CALENDAR = [
  {
    "name": "noop",
    "description": "Use when no action is needed (greeting/thanks).",
    "parameters": {"type": "object", "properties": {}, "required": []},
  },
  {
    "name": "ask_clarifying_question",
    "description": (
      "Ask ONE clarifying question when the user request is ambiguous or missing required details. "
      "Use instead of guessing."
    ),
    "parameters": {
      "type": "object",
      "properties": {
        "question": {"type": "string", "description": "One short question to ask the user."},
        "choices": {"type": "array", "items": {"type": "string"}, "description": "Optional choices."},
      },
      "required": ["question"],
    },
  },
  {
    "name": "create_event",
    "description": "Create/schedule/book/add a calendar event.",
    "parameters": {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "when_text": {"type": "string", "description": "Natural language time like 'tomorrow 7pm'"},
        "duration_minutes": {"type": "integer", "description": "Default 60"},
        "location": {"type": "string"},
      },
      "required": ["title", "when_text"],
    },
  },
  {
    "name": "find_event",
    "description": "Find events by keyword in a time range. Use before move/cancel if event_id is unknown.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {"type": "string"},
        "start_when_text": {"type": "string", "description": "e.g. 'today'"},
        "end_when_text": {"type": "string", "description": "e.g. 'in 14 days'"},
      },
      "required": ["query", "start_when_text", "end_when_text"],
    },
  },
  {
    "name": "move_event",
    "description": "Reschedule an event to a new time. Requires event_id (use find_event first).",
    "parameters": {
      "type": "object",
      "properties": {
        "event_id": {"type": "string"},
        "new_when_text": {"type": "string"},
      },
      "required": ["event_id", "new_when_text"],
    },
  },
  {
    "name": "cancel_event",
    "description": "Cancel/delete an event. Requires event_id (use find_event first).",
    "parameters": {
      "type": "object",
      "properties": {"event_id": {"type": "string"}},
      "required": ["event_id"],
    },
  },
]
