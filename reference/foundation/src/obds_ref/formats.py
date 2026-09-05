"""Format checks used by production boundaries, without optional dependencies."""
from datetime import datetime
import re
import jsonschema


def valid_datetime(value):
    if not isinstance(value, str):
        return True  # The schema's type constraint owns non-strings.
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:[0-5]\d(?:\.\d+)?(?:[Zz]|[+-](?:[01]\d|2[0-3]):[0-5]\d)', value):
        return False
    try:
        return datetime.fromisoformat(value.upper().replace('Z', '+00:00')).tzinfo is not None
    except ValueError:
        return False


def format_checker():
    checker = jsonschema.FormatChecker()
    checker.checks('date-time')(valid_datetime)
    return checker
