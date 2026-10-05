import csv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
import qrcode
from PIL import Image
import os
import io
import logging
from dotenv import load_dotenv
import requests
import json
import uuid
import base64
import urllib.parse
import re
import sqlite3
import shutil
from reportlab.pdfbase.pdfmetrics import stringWidth

# Load environment variables
load_dotenv()

# Infobip API settings
INFOBIP_API_KEY = os.getenv('INFOBIP_API_KEY')
# Use hardcoded sender number in E.164 format
INFOBIP_WHATSAPP_SENDER = "447860088970"

# Kenkom SMS API settings
KENKOM_BASE_URL = os.getenv('KENKOM_BASE_URL', 'https://pay.kenkom.ug').rstrip('/')
KENKOM_API_KEY = os.getenv('KENKOM_API_KEY')
KENKOM_SENDER = os.getenv('KENKOM_SENDER', 'ANGSTROM')
# Live sends only happen when SEND_SMS is set; otherwise payloads are logged
SEND_SMS = os.getenv('SEND_SMS', 'false').strip().lower() in ('1', 'true', 'yes')

DB_PATH = "evites.db"
EVITE_BASE_URL = "https://events.angstrom-technologies.ug/evite"

# Format title and name for the message
def format_greeting(title, name):
    # If title contains 'Mr & Mrs', format it as a single unit
    if "&" in title:
        return f"{title} {name.split()[0]}"
    # For single titles, format as "Dear Mr. Edmund"
    if title:
        return f"{title}. {name.split()[0]}"
    return f"{name.split()[0]}"

# Create message template with formatted greeting
MESSAGE_TEMPLATE = "{greeting},\n\nHere is your birthday invitation e-vite. Please save it and present it at the event.\n\nBest regards,\nBirthday Organizers"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Send WhatsApp document message using Infobip API
def send_whatsapp_document(phone, name, title, pdf_path):
    """Send WhatsApp document message using Infobip API."""
    try:
        # Format message
        greeting = format_greeting(title, name)
        # Format message as a single line without newlines
        message = MESSAGE_TEMPLATE.format(greeting=greeting).replace('\n', ' ').strip()
        
        # Prepare the API request
        headers = {
            'Authorization': f'App {INFOBIP_API_KEY}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # Use sender number from environment variable and ensure proper formatting
        sender_number = INFOBIP_WHATSAPP_SENDER
        logger.info(f"Using sender number: {sender_number}")
        import uuid
        message_id = str(uuid.uuid4())
        
        # Create the message payload
        payload = {
            "messages": [
                {
                    "from": sender_number,
                    "to": phone,
                    "messageId": message_id,
                    "content": {
                        "filename": "evite.pdf",
                        "caption": message,
                        "mediaUrl": f"https://events.angstrom-technologies.ug/{name.replace(' ', '_')}_evite.pdf"
                    }
                }
            ]
        }
        logger.info(payload)
        
        # Send the message
        response = requests.post(
            "https://yp936p.api.infobip.com/whatsapp/1/message/document",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            logger.info(f"Successfully sent document to {phone}")
            logger.info(response.json())
        else:
            logger.error(f"Failed to send document to {phone}: {response.text}")
            
    except Exception as e:
        logger.error(f"Error sending WhatsApp document to {phone}: {str(e)}")
        raise

# Send SMS message using Infobip API
def send_sms(phone, name, title, download_url):
    """Send SMS message using Infobip API."""
    try:
        # Format message with download URL
        greeting = format_greeting(title, name)
        url = download_url
        message = f"{greeting},\n\nHere is your birthday invitation e-vite. Please save it and present it at the event.\n\nE-vite URL: {url}\n\nBest regards,\nBirthday Organizers".replace('\n', ' ').strip()
        
        # Prepare the API request
        headers = {
            'Authorization': f'App {INFOBIP_API_KEY}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # Create the message payload
        payload = {
            "messages": [
                {
                    "destinations": [{"to": phone}],
                    "from": "12036358403",
                    "text": message
                }
            ]
        }
        logger.info(f"Sending SMS to {phone}")
        logger.info(f"SMS payload: {payload}")
        
        # Send the message
        response = requests.post(
            "https://yp936p.api.infobip.com/sms/2/text/advanced",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            logger.info(f"Successfully sent SMS to {phone}")
            logger.info(response.json())
        else:
            logger.error(f"Failed to send SMS to {phone}: {response.text}")
            logger.error(f"Response status code: {response.status_code}")
            logger.error(f"Response content: {response.content}")
            
    except Exception as e:
        logger.error(f"Error sending SMS to {phone}: {str(e)}")
        raise

# Send WhatsApp text message using Infobip API
def send_whatsapp_text(phone, name, title):
    """Send WhatsApp text message using Infobip API."""
    try:
        # Prepare the API request
        headers = {
            'Authorization': f'App {INFOBIP_API_KEY}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # Use sender number from environment variable and ensure proper formatting
        sender_number = INFOBIP_WHATSAPP_SENDER
        if not sender_number.startswith('+'):
            sender_number = '+' + sender_number
        logger.info(f"Using sender number: {sender_number}")
        import uuid
        message_id = str(uuid.uuid4())
        
        # Create the message payload
        payload = {
            "messages": [
                {
                    "from": sender_number,
                    "to": phone,
                    "messageId": message_id,
                    "content": {
                        "text": f"Hello, Please RSVP for {name}_Birthday to receive your invite"
                    }
                }
            ]
        }
        logger.info(payload)
        
        # Send the message
        response = requests.post(
            "https://yp936p.api.infobip.com/whatsapp/1/message/text",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            logger.info(f"Successfully sent text message to {phone}")
            logger.info(response.json())
        else:
            logger.error(f"Failed to send text message to {phone}: {response.text}")
            logger.error(f"Response status code: {response.status_code}")
            logger.error(f"Response content: {response.content}")
            
    except Exception as e:
        logger.error(f"Error sending WhatsApp text to {phone}: {str(e)}")
        raise

        import uuid
        message_id = str(uuid.uuid4())
        
        # Create the message payload
        payload = {
            "from": INFOBIP_WHATSAPP_SENDER,
            "to": phone,
            "messageId": message_id,
            "entityId":"evenzon3",
            "applicationId": "evenzon3",
            "content": {
                "text": f"Hello, Please RSVP for {name}_Birthday to receive your invite"
            },
            "callbackData": "Callback data",
            "notifyUrl": "https://events.angstrom-technologies.ug/infobip_webhook.php",
            "urlOptions": {
                "shortenUrl": True,
                "trackClicks": True,
                "trackingUrl": "https://events.angstrom-technologies.ug/infobip_webhook.php",
                "removeProtocol": True
            }
        }
        logger.info(payload)
        
        # Send the message
        response = requests.post(
            "https://yp936p.api.infobip.com/whatsapp/1/message/text",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            logger.info(f"Successfully sent text message to {phone}")
            logger.info(response.json())
        else:
            logger.error(f"Failed to send text message to {phone}: {response.text}")
            
    except Exception as e:
        logger.error(f"Error sending WhatsApp text to {phone}: {str(e)}")
        raise



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Birthday event details
EVENT_TITLE = "HERBERT TINDYEBWA MURANGIRA'S 60th Birthday"
EVENT_DATE = "Friday 30th October 2026"
EVENT_LOCATION = "Speke Resort Munyonyo, Victoria Hall"
DRESS_CODE = "Smart Casual"
RSVP_LINES = ["Lillian: +256 741 404 822", "Edmund: +256 787 467 287"]
INVITE_IMAGE = "Herbert Evite.jpeg"

# PDF dimensions
PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = inch * 0.5

# Card color settings — gold on black, per card design.drawio
GOLD = colors.Color(0.890, 0.765, 0.533)        # #e3c388
GREETING_GOLD = colors.Color(0.906, 0.780, 0.545)  # #E7C78B
PHONE_GOLD = colors.Color(0.55, 0.46, 0.31)     # muted gold for the phone line
FOOTER_BLUE = colors.Color(0.600, 0.800, 1.000)  # #99CCFF
FOOTER_LINES = ["Powered by Angstrom Technologies Limited.", "https://angstrom-technologies.ug", "events@angstrom-technologies.ug"]

# Banner: top crop of the artwork, bottom fraction faded to black
BANNER_ASPECT = 1.56       # width/height of the cropped banner region
BANNER_HEIGHT_FRAC = 0.495 # banner height as a fraction of page height
BANNER_FADE_FRAC = 0.28    # bottom fraction of the banner that fades to black
BANNER_FILE = "invite_banner.jpg"

_banner_path = None

def get_invite_banner():
    """Crop the top '60 balloons' region of the artwork and fade its bottom
    into black. Cached: the JPEG is built once per run and reused."""
    global _banner_path
    if _banner_path is not None:
        return _banner_path

    img = Image.open(INVITE_IMAGE).convert('RGB')
    crop_h = int(img.width / BANNER_ASPECT)
    banner = img.crop((0, 0, img.width, crop_h))

    # Blend the bottom fade zone toward pure black so it merges with the card
    fade_h = int(crop_h * BANNER_FADE_FRAC)
    mask = Image.new('L', banner.size, 255)
    ramp = Image.new('L', (1, fade_h))
    ramp.putdata([round(255 * (1 - i / (fade_h - 1))) for i in range(fade_h)])
    mask.paste(ramp.resize((banner.width, fade_h)), (0, crop_h - fade_h))
    banner = Image.composite(banner, Image.new('RGB', banner.size, (0, 0, 0)), mask)

    banner.save(BANNER_FILE, format='JPEG', quality=88)
    _banner_path = BANNER_FILE
    return _banner_path

# -------------------- SQLite e-vite registry --------------------

def init_db(path=DB_PATH):
    """Create the evites and sms_log tables if needed and return a connection."""
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS evites (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT NOT NULL UNIQUE,
            title        TEXT,
            phones       TEXT,
            admits       INTEGER,
            uuid         TEXT NOT NULL,
            verify_data  TEXT NOT NULL,
            download_url TEXT NOT NULL,
            filename     TEXT,
            created_at   TEXT DEFAULT (datetime('now')),
            updated_at   TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sms_log (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            evite_id     INTEGER REFERENCES evites(id),
            phone        TEXT NOT NULL,
            status       TEXT NOT NULL,
            api_response TEXT,
            sent_at      TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


def get_or_create_evite(conn, name, title, phones, admits, filename):
    """Return the guest's stored evite (stable UUID/URL across runs) or create it."""
    row = conn.execute(
        "SELECT id, uuid, verify_data, download_url FROM evites WHERE name = ?",
        (name,)
    ).fetchone()
    if row:
        evite_id, evite_uuid, verify_data, _ = row
        # Short filename keeps SMS under 160 chars; derived from the stable UUID
        download_url = f"{EVITE_BASE_URL}/download/{evite_uuid.split('-')[0]}.pdf"
        conn.execute(
            "UPDATE evites SET title=?, phones=?, admits=?, filename=?, "
            "download_url=?, updated_at=datetime('now') WHERE id=?",
            (title, phones, admits, filename, download_url, evite_id)
        )
        conn.commit()
        return {"id": evite_id, "uuid": evite_uuid,
                "verify_data": verify_data, "download_url": download_url}

    evite_uuid = str(uuid.uuid4())
    verify_data = f"{title}:{name}:{phones}:{evite_uuid}"
    download_url = f"{EVITE_BASE_URL}/download/{evite_uuid.split('-')[0]}.pdf"
    cur = conn.execute(
        "INSERT INTO evites (name, title, phones, admits, uuid, verify_data, "
        "download_url, filename) VALUES (?,?,?,?,?,?,?,?)",
        (name, title, phones, admits, evite_uuid, verify_data, download_url, filename)
    )
    conn.commit()
    return {"id": cur.lastrowid, "uuid": evite_uuid,
            "verify_data": verify_data, "download_url": download_url}


def log_sms(conn, evite_id, phone, status, api_response):
    conn.execute(
        "INSERT INTO sms_log (evite_id, phone, status, api_response) "
        "VALUES (?,?,?,?)",
        (evite_id, phone, status, api_response)
    )
    conn.commit()


# -------------------- Kenkom SMS --------------------

def send_sms_kenkom(phone, message):
    """Send an SMS via the Kenkom gateway. Returns (ok, response_text)."""
    try:
        response = requests.post(
            f"{KENKOM_BASE_URL}/api/v1/sms/send/",
            headers={
                'x-api-key': KENKOM_API_KEY,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            json={"phone": phone, "message": message, "sender": KENKOM_SENDER},
            timeout=30,
        )
        return response.status_code == 200, response.text
    except Exception as e:
        return False, str(e)


def generate_pdf(name, title, phone, admits, output_path, verify_data):
    """Generate a PDF e-vite."""
    try:

        # Create canvas
        c = canvas.Canvas(output_path, pagesize=letter)

        # Black card background
        c.setFillColor(colors.black)
        c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)

        # Positions are fractions of the card (mirroring card design.drawio):
        # xr = fraction of page width from the left, yr = fraction from the top
        def xr(frac):
            return frac * PAGE_WIDTH

        def yr(frac):
            return PAGE_HEIGHT - frac * PAGE_HEIGHT

        def draw_fitted(text, x, y_pos, font, size, max_width, color=GOLD):
            """Draw left-aligned text, shrinking the font until it fits."""
            while size > 7 and stringWidth(text, font, size) > max_width:
                size -= 0.5
            c.setFillColor(color)
            c.setFont(font, size)
            c.drawString(x, y_pos, text)

        def draw_centered_fitted(text, y_pos, font, size, color=GOLD):
            """Draw centered text, shrinking the font until it fits.
            Returns the effective font size used."""
            while size > 7 and stringWidth(text, font, size) > PAGE_WIDTH - 2 * MARGIN:
                size -= 0.5
            c.setFillColor(color)
            c.setFont(font, size)
            c.drawCentredString(PAGE_WIDTH / 2, y_pos, text)
            return size

        # Banner: artwork top crop, faded to black, flush across the page top
        banner_h = PAGE_HEIGHT * BANNER_HEIGHT_FRAC
        c.drawImage(get_invite_banner(), 0, PAGE_HEIGHT - banner_h,
                    width=PAGE_WIDTH, height=banner_h)

        # Greeting inside the fade zone, then a subtle phone line
        greeting = f"{title} {name}".strip() if title else f"{name}"
        draw_centered_fitted(greeting.upper(), yr(0.525), "Helvetica-Bold", 15, GREETING_GOLD)
        #draw_centered_fitted(f"Phone: {phone}", yr(0.548), "Helvetica", 8, PHONE_GOLD)

        # Celebrate block — flanking rules on the first line, as in the artwork.
        # Baselines are spaced for the 18/24/18pt sizes so caps don't collide.
        join_y = yr(0.575)
        join_size = draw_centered_fitted("PLEASE JOIN US TO CELEBRATE", join_y, "Helvetica", 18)
        draw_centered_fitted("HERBERT TINDYEBWA MURANGIRA'S", yr(0.612), "Helvetica-Bold", 24)

        # "60TH BIRTHDAY" with TH as a raised superscript
        runs = [("60", "Helvetica", 18, 0), ("TH", "Helvetica", 11, 8), (" BIRTHDAY", "Helvetica", 18, 0)]
        widths = [stringWidth(t, f, s) for t, f, s, _ in runs]
        x = (PAGE_WIDTH - sum(widths)) / 2
        c.setFillColor(GOLD)
        for (t, f, s, rise), w in zip(runs, widths):
            c.setFont(f, s)
            c.drawString(x, yr(0.642) + rise, t)
            x += w

        c.setStrokeColor(GOLD)
        c.setLineWidth(0.8)
        half = stringWidth("PLEASE JOIN US TO CELEBRATE", "Helvetica", join_size) / 2
        rule_y = join_y + join_size * 0.33
        c.line(xr(0.10), rule_y, PAGE_WIDTH / 2 - half - 12, rule_y)
        c.line(PAGE_WIDTH / 2 + half + 12, rule_y, xr(0.90), rule_y)

        # Rules above and below the date & venue block (80% width, centered)
        c.line(xr(0.10), yr(0.662), xr(0.90), yr(0.662))
        c.line(xr(0.10), yr(0.732), xr(0.90), yr(0.732))

        # Two-column info block with a gold divider, as in the artwork
        col_left_x = xr(0.13)
        col_right_x = xr(0.40)
        col_size = 10.5
        col_gap = 15
        col_top = yr(0.680)

        c.line(xr(0.36), col_top + 4, xr(0.36), col_top - 2 * col_gap - 4)

        for i, line in enumerate(["FRIDAY", "30TH OCTOBER 2026", "AT 6:00PM"]):
            draw_fitted(line, col_left_x, col_top - i * col_gap, "Helvetica", col_size, xr(0.36) - col_left_x - 8)
        for i, line in enumerate(["COCKTAIL & DINNER",
                                  "VENUE: SPEKE RESORT MUNYONYO, VICTORIA HALL",
                                  "DRESS CODE: SMART CASUAL"]):
            draw_fitted(line, col_right_x, col_top - i * col_gap, "Helvetica", col_size, xr(0.90) - col_right_x)

        # RSVP — all italic
        draw_centered_fitted("RSVP", yr(0.752), "Helvetica-Oblique", 12)
        draw_fitted(RSVP_LINES[0], col_left_x, yr(0.790), "Helvetica-Oblique", col_size, 240)
        draw_fitted(RSVP_LINES[1], xr(0.679), yr(0.790), "Helvetica-Oblique", col_size, 240)

        # Create QR code with verification URL (same payload as the download link)
        verify_url = f"{EVITE_BASE_URL}/verify.php/{base64.urlsafe_b64encode(verify_data.encode()).decode()}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(verify_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Convert PIL image to bytes
        qr_bytes = io.BytesIO()
        qr_img.save(qr_bytes, format='PNG')
        qr_bytes.seek(0)

        # QR bottom-left, admit count beside it
        qr_size = 91
        qr_y = yr(0.81) - qr_size
        c.drawImage(ImageReader(qr_bytes), xr(0.04), qr_y, width=qr_size, height=qr_size)
        draw_fitted(f"This Invite Admits {admits} person(s)", xr(0.373),
                    qr_y + qr_size / 2 - 4, "Helvetica", 10.5, 200)

        # Footer
        for i, line in enumerate(FOOTER_LINES):
            pass

        # "Validated" + vector checkmark as a real clickable link to the
        # verify URL (ZapfDingbats ✓ renders unreliably in some viewers).
        link_y = yr(0.945 + 2 * 0.019)
        label, font, size = "Validated", "Helvetica", 8.5
        text_w = stringWidth(label, font, size)
        gap, check_w = 4, 8          # space before check, check width
        link_w = text_w + gap + check_w
        link_x = (PAGE_WIDTH - link_w) / 2
        c.setFillColor(FOOTER_BLUE)
        c.setFont(font, size)
        c.drawString(link_x, link_y, label)

        # Drawn checkmark
        c.setStrokeColor(FOOTER_BLUE)
        c.setLineWidth(1.4)
        cx = link_x + text_w + gap
        c.line(cx, link_y + 4.5, cx + 3, link_y + 1.2)
        c.line(cx + 3, link_y + 1.2, cx + check_w, link_y + 8)

        c.linkURL(verify_url,
                  ((PAGE_WIDTH - link_w) / 2, link_y - 2,
                   (PAGE_WIDTH + link_w) / 2, link_y + 8.5),
                  relative=0, thickness=0)

        # Save PDF
        c.save()
        logger.info(f"Successfully generated e-vite for {name}")

    except Exception as e:
        logger.error(f"Error generating e-vite for {name}: {str(e)}")
        raise



def generate_evites(data_path, output_dir="output"):
    """Generate personalized e-vites from CSV data, register them in SQLite,
    and send the download link via Kenkom SMS (one SMS per phone number)."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    conn = init_db()
    logger.info("Starting e-vite generation...")
    logger.info(f"SMS sending {'ENABLED' if SEND_SMS else 'DISABLED (dry run)'}")
    if SEND_SMS and not KENKOM_API_KEY:
        logger.error("SEND_SMS is enabled but KENKOM_API_KEY is not set in .env")
        conn.close()
        return

    with open(data_path, 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = "Unknown"
            try:
                name = row['Name']
                phone = row['Phone']
                title = row.get('Title', '').strip()
                admits = int(row.get('Admits', '0').strip() or 0)

                # Skip rows without name or phone
                if not name or not phone:
                    logger.warning(f"Skipping row with missing name or phone: {row}")
                    continue

                # Register the e-vite (reuses the stored UUID/URL on re-runs)
                safe_phone = re.sub(r'[\\/:*?"<>|]', '_', phone)
                filename = f"{name}_{safe_phone}.pdf"
                evite = get_or_create_evite(conn, name, title, phone, admits, filename)

                # Generate PDF (QR encodes the same payload as the download link)
                output_path = os.path.join(output_dir, filename)
                generate_pdf(name, title, phone, admits, output_path, evite["verify_data"])
                logger.info(f"Successfully generated e-vite for {name} with UUID: {evite['uuid']}")

                # Upload copy named after the download URL's short ID
                upload_dir = "upload"
                os.makedirs(upload_dir, exist_ok=True)
                shutil.copyfile(output_path,
                                os.path.join(upload_dir,
                                             f"{evite['uuid'].split('-')[0]}.pdf"))

                # SMS each '/'-separated number with the download link
                message = (f"{format_greeting(title, name)}, "
                           f"Join us to celebrate Herbert Tindyebwa Murangira's 60th Birthday. "
                           f"Your e-vite: {evite['download_url']}")
                if len(message) > 160:
                    logger.warning(f"SMS for {name} is {len(message)} chars (>160)")
                for number in [p.strip() for p in phone.split('/') if p.strip()]:
                    if SEND_SMS:
                        ok, resp = send_sms_kenkom(number, message)
                        status = 'sent' if ok else 'failed'
                        log_sms(conn, evite["id"], number, status, resp)
                        if ok:
                            logger.info(f"SMS sent to {number}")
                        else:
                            logger.error(f"SMS to {number} failed: {resp}")
                    else:
                        log_sms(conn, evite["id"], number, 'dry_run', message)
                        logger.info(f"[DRY RUN] SMS to {number} ({len(message)} chars): {message}")

            except Exception as e:
                logger.error(f"Error processing {name}: {str(e)}")
                continue

    conn.close()
    logger.info("E-vite generation complete!")

if __name__ == "__main__":
    try:
        DATA_PATH = "guests.csv"
        
        logger.info("Starting e-vite generation...")
        generate_evites(DATA_PATH)
        logger.info("E-vite generation complete!")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise
