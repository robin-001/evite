import csv
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Canonical titles mapped from the messy prefixes found in the source list.
# Patterns allow optional dots and glued names (e.g. "Mr.Adrian", "Ms..Amanda",
# "Mr & Mrs.Michael"). Compound titles must be tried before bare ones.
TITLE_PATTERNS = [
    (r'^Mr\.?\s*&\s*Mrs\.?\s*', 'Mr & Mrs'),
    (r'^Mr\s+Mrs\.?\s*', 'Mr & Mrs'),
    (r'^Mrs\.{0,2}\s*', 'Mrs'),
    (r'^Mr\.{0,2}\s*', 'Mr'),
    (r'^Ms\.{0,2}\s*', 'Ms'),
    (r'^Hon\.?\s+', 'Hon'),
    (r'^Gen\.?\s+', 'Gen'),
]


def extract_title_and_name(full_name):
    """Extract a leading title from a name. Returns (cleaned_name, title)."""
    full_name = re.sub(r'\s+', ' ', full_name.strip())
    for pattern, title in TITLE_PATTERNS:
        if re.match(pattern, full_name):
            cleaned = re.sub(pattern, '', full_name).strip()
            return cleaned, title
    return full_name, ''


def normalise_phone(token):
    """Normalise one phone token to E.164. Local Ugandan numbers get +256.
    Returns the normalised string, or '' for blanks/placeholders."""
    digits = re.sub(r'[\s\-]+', '', token.strip())
    if not digits or digits in ('-', '0'):
        return ''
    if digits.startswith('+'):
        body = re.sub(r'\D', '', digits[1:])
        return '+' + body if body else ''
    digits = re.sub(r'\D', '', digits)
    if not digits:
        return ''
    if len(digits) == 10 and digits.startswith('0'):
        return '+256' + digits[1:]
    if len(digits) == 9:
        return '+256' + digits
    if len(digits) > 10:
        # International number typed without the '+'
        return '+' + digits
    logger.warning(f"Unrecognised phone format, keeping raw: {token!r}")
    return token.strip()


def merge_phones(mr_cell, mrs_cell):
    """Merge the two phone columns into one '/'-separated value, deduped."""
    numbers = []
    for cell in (mr_cell, mrs_cell):
        for token in (cell or '').split('/'):
            normalised = normalise_phone(token)
            if normalised and normalised not in numbers:
                numbers.append(normalised)
    return '/'.join(numbers)


def process_csv(input_file, output_file):
    """Sanitise the Herbert 60th guest list into Name,Phone,Title,Admits."""
    rows = []
    empty_phone = 0

    with open(input_file, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_name = (row.get('NAME') or '').strip()
            if not raw_name or 'TOTAL' in raw_name.upper():
                continue

            name, title = extract_title_and_name(raw_name)
            phone = merge_phones(row.get('PHONE NO (Mr)'), row.get('PHONE NO. (Mrs)'))
            admits = (row.get('Qty') or '').strip()
            if not phone:
                empty_phone += 1

            rows.append({'Name': name, 'Phone': phone, 'Title': title, 'Admits': admits})

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Name', 'Phone', 'Title', 'Admits'])
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Wrote {len(rows)} guests to {output_file} ({empty_phone} with no phone)")


if __name__ == "__main__":
    process_csv('Herbert 60th Birthday Guest List.csv', 'guests.csv')
