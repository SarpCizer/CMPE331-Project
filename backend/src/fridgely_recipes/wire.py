"""Lossless Cloudflare wire adaptation. No invented recipe fields or quantities."""
import json
import math
import re


MAX_RESPONSE_CHARS = 262144
UNIT_NAMES = {
    'g': 'g', 'gram': 'g', 'grams': 'g', 'kg': 'kg', 'kilogram': 'kg', 'kilograms': 'kg',
    'ml': 'ml', 'milliliter': 'ml', 'milliliters': 'ml',
    'l': 'L', 'liter': 'L', 'liters': 'L', 'pcs': 'pcs', 'piece': 'pcs', 'pieces': 'pcs',
    'pack': 'pack', 'bunch': 'bunch',
}


class WireError(ValueError):
    """The message is a fixed diagnostic code, never provider/user content."""


def token_limit_reached(usage, limit):
    if not isinstance(usage, dict):
        return False
    count = usage.get('completion_tokens')
    return type(count) in (int, float) and math.isfinite(count) and count >= limit


def json_text(value):
    if len(value) > MAX_RESPONSE_CHARS:
        raise WireError('response_too_large')
    text = value.strip()
    if text.startswith('```json') and text.endswith('```'):
        return text[7:-3].strip()
    if text.startswith('```') and text.endswith('```'):
        return text[3:-3].strip()
    return text


def complete_prefix(text):
    """Only called after a confirmed output-token limit, never after a timeout.

    Decode whole objects before an unfinished final object. Do not manufacture
    JSON delimiters or values, or skip any complete object that fails validation.
    """
    match = re.match(r'\s*(?:\{\s*"recipes"\s*:\s*)?\[', text)
    if not match:
        raise WireError('truncated_root')
    decoder, rows, offset = json.JSONDecoder(), [], match.end()
    while True:
        tail = text[offset:].lstrip()
        if not tail.startswith('{'):
            raise WireError('truncated_delimiter')
        try:
            row, end = decoder.raw_decode(tail)
        except json.JSONDecodeError:
            if not rows:
                raise WireError('no_complete_recipe') from None
            return {'recipes': rows}
        rows.append(row)
        remaining = tail[end:].lstrip()
        if not remaining or remaining == ',':
            return {'recipes': rows}
        if not remaining.startswith(','):
            raise WireError('truncated_delimiter')
        offset = len(text) - len(remaining) + 1


def decode_response(value, allow_prefix=False):
    recovered = False
    if isinstance(value, str):
        text = json_text(value)
        try:
            value = json.loads(text)
        except (ValueError, RecursionError):
            if not allow_prefix:
                raise WireError('invalid_json') from None
            value = complete_prefix(text)
            recovered = True
    if isinstance(value, list):
        value = {'recipes': value}
    elif isinstance(value, dict) and ('t' in value or 'title' in value) and 'recipes' not in value:
        value = {'recipes': [value]}
    if not isinstance(value, dict) or not isinstance(value.get('recipes'), list):
        raise WireError('invalid_root')
    return value, recovered


def canonical_fields(row, names):
    if not isinstance(row, dict):
        raise WireError('invalid_record')
    result = {}
    for short, long in names.items():
        if short in row and long in row and row[short] != row[long]:
            raise WireError('conflicting_aliases')
        if short not in row and long not in row:
            raise WireError('missing_field')
        result[long] = row[short] if short in row else row[long]
    return result


def explicit_amount(value):
    """Normalize explicit unit spellings only; the strict dose parser follows."""
    if isinstance(value, dict) and set(value) == {'quantity', 'unit'}:
        unit = value['unit']
        if isinstance(unit, str):
            return {**value, 'unit': UNIT_NAMES.get(unit.casefold(), unit)}
        return value
    if not isinstance(value, str) or len(value) > 64:
        return value
    match = re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*([a-zA-Z]+)\s*', value)
    if match and match[2].casefold() in UNIT_NAMES:
        return match[1] + ' ' + UNIT_NAMES[match[2].casefold()]
    return value
