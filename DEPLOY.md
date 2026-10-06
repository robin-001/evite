# Event Zone — deploy notes (Ubuntu / Apache / MySQL)

App: React SPA (static `frontend/dist`) + Django REST API (`backend/`) + MySQL.
Domain: https://events.angstrom-technologies.ug

## 1. Server setup

```bash
# System deps (once)
sudo apt install python3-venv mysql-server apache2
sudo a2enmod proxy proxy_http rewrite headers

# App dirs
sudo mkdir -p /var/www/events
cd /var/www/events
git clone https://github.com/robin-001/evite.git app
cd app/backend
python3 -m venv venv
venv/bin/pip install -r requirements.txt gunicorn
venv/bin/python -m playwright install chromium
venv/bin/python -m playwright install-deps chromium   # system libs

# Config
cp ../.env.example .env    # then fill in values

# Database
mysql -u root -p -e "CREATE DATABASE evite CHARACTER SET utf8mb4; \
  CREATE USER 'evite'@'localhost' IDENTIFIED BY '<password>'; \
  GRANT ALL ON evite.* TO 'evite'@'localhost';"
venv/bin/python manage.py migrate
venv/bin/python manage.py collectstatic
venv/bin/python manage.py createsuperuser

# Frontend build
cd ../frontend && npm ci && npm run build   # outputs dist/
```

## 2. gunicorn service — `/etc/systemd/system/evite.service`

```ini
[Unit]
Description=Event Zone Django backend
After=network.target mysql.service

[Service]
User=www-data
WorkingDirectory=/var/www/events/app/backend
ExecStart=/var/www/events/app/backend/venv/bin/gunicorn config.wsgi \
    --bind 127.0.0.1:8000 --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```

`sudo systemctl enable --now evite`

## 3. Apache vhost — events.angstrom-technologies.ug

```apache
<VirtualHost *:443>
    ServerName events.angstrom-technologies.ug
    # ... TLS certs as existing ...

    DocumentRoot /var/www/events/app/frontend/dist

    # API → Django
    ProxyPass        /api/ http://127.0.0.1:8000/api/
    ProxyPassReverse /api/ http://127.0.0.1:8000/api/

    # Generated PDFs / artwork
    Alias /media/ /var/www/events/app/backend/media/
    <Directory /var/www/events/app/backend/media>
        Require all granted
        Options -Indexes
    </Directory>

    # Legacy e-vites (kept working)
    Alias /evite/verify.php /var/www/events/app/verify.php
    # /evite/download/  → existing directory with server-download/.htaccess
    #                     + index.php inside it

    # SPA fallback — everything else to React
    <Directory /var/www/events/app/frontend/dist>
        Require all granted
        FallbackResource /index.html
    </Directory>
</VirtualHost>
```

## 4. Legacy download dir

Upload the contents of `server-download/` (`index.php` + `.htaccess`) into the
`/evite/download/` directory — it redirects the bare directory to the verify
page and disables listing. Generated guest PDFs land in
`backend/media/events/<id>/cards/<uuid8>.pdf`.

## 5. Before going live

- `DJANGO_DEBUG=false`, a real `DJANGO_SECRET_KEY` (32+ bytes)
- `SEND_SMS=true` only when ready to spend SMS credit
- `GOOGLE_CLIENT_ID` set in both `.env` and as `VITE_GOOGLE_CLIENT_ID`
  before `npm run build`
