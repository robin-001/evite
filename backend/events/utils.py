import csv
import io
import re

PHONE_SPLIT_RE = re.compile(r'[/;]|,\s*(?=\+?[\d\s])')


def normalize_phone(raw):
    """Normalise a phone number to international format.

    Ugandan local numbers (07XXXXXXXX or bare 7XXXXXXXX) become +256...
    Numbers already in +international form are preserved.
    Returns '' for unusable values.
    """
    if not raw:
        return ''
    value = re.sub(r'[\s\-().]', '', raw.strip())
    if value in ('', '-', '0'):
        return ''
    if value.startswith('00'):
        value = '+' + value[2:]
    if value.startswith('+'):
        return value if re.fullmatch(r'\+\d{7,15}', value) else ''
    digits = re.sub(r'\D', '', value)
    if not digits:
        return ''
    # Ugandan local formats
    if re.fullmatch(r'0?7\d{8}', digits):
        return '+256' + digits[-9:]
    # Bare 20XXXXXXXXXX (Egyptian-style, no +)
    if re.fullmatch(r'20\d{10}', digits):
        return '+' + digits
    if len(digits) > 9:
        return '+' + digits
    return ''


def parse_phones(raw):
    """Split a merged phone field ('/'-separated) into normalised numbers."""
    seen = []
    for part in re.split(r'/', raw or ''):
        num = normalize_phone(part)
        if num and num not in seen:
            seen.append(num)
    return seen


def import_guests_csv(event, file_obj):
    """Import guests from an uploaded CSV.

    Expected columns (case-insensitive): Title, Name, Phone, Admits
    (a Phone column with '/'-separated values splits into multiple numbers).
    Returns (created_count, skipped_rows).
    """
    from .models import Guest

    text = file_obj.read().decode('utf-8-sig', errors='replace')
    reader = csv.DictReader(io.StringIO(text))
    headers = {h.strip().lower(): h for h in (reader.fieldnames or [])}

    def col(row, *names):
        for n in names:
            if n in headers:
                return (row.get(headers[n]) or '').strip()
        return ''

    created, skipped = 0, []
    for row in reader:
        name = col(row, 'name')
        title = col(row, 'title')
        phone_raw = col(row, 'phone', 'phones')
        admits_raw = col(row, 'admits', 'qty', 'guests')
        if not name:
            skipped.append(row)
            continue
        phones = parse_phones(phone_raw)
        try:
            admits = int(admits_raw) if admits_raw else 1
        except ValueError:
            admits = 1
        Guest.objects.create(
            event=event, name=name, title=title,
            phone=phones[0] if phones else '',
            phones=phones, admits=max(admits, 1),
        )
        created += 1
    return created, skipped
