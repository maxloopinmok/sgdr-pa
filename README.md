# SG Dividends Reports — PythonAnywhere deployment

Presentation-only Django app. The companion laptop deployment scrapes SGX and
pushes events to this site via a future `/sync/` endpoint. This app never
touches SGX directly — no Playwright, no Postgres, no Docker, no qcluster.

## What's in here

```
pythonanywhere/
├── manage.py
├── requirements.txt          ← just Django + whitenoise
├── config/
│   ├── settings.py           ← single-file settings, SQLite, Whitenoise
│   ├── urls.py
│   └── wsgi.py               ← WSGI entrypoint linked from PA's Web tab
├── apps/
│   ├── companies/            ← Company model + curated 97-name universe
│   │   ├── data/             ← mainboard_universe.py + index_membership.py
│   │   └── management/commands/seed_mainboard_companies.py
│   ├── events/               ← Event model + calendar views + window helper
│   └── core/                 ← landing / about / disclaimer / health
├── templates/                ← every page (calendar, list, detail panel)
└── static/                   ← breakpoints.js
```

What's intentionally **not** here (lives only on the laptop):
`services/sgx/`, `jobs/`, `apps/reports/`, `apps/scheduler/`, Playwright,
psycopg, dj-database-url, gunicorn, Docker, Caddy.

## One-time setup on PA (free tier)

Open a Bash console on PA. (You already have one.)

### 1. Upload the code

**Option A — git (recommended).** Create a fresh repo with the contents of
this `pythonanywhere/` folder, push to GitHub, then on PA:

```bash
cd ~
git clone https://github.com/<you>/<repo>.git sgdr
cd sgdr
```

**Option B — zip and upload.** On your laptop:

```powershell
Compress-Archive -Path C:\Users\maxlo\src\sgdividendsreports\pythonanywhere\* -DestinationPath sgdr.zip
```

Upload `sgdr.zip` via PA → Files tab → Home directory → Upload. Then in PA Bash:

```bash
cd ~
mkdir -p sgdr
cd sgdr
unzip ../sgdr.zip
```

### 2. Create a virtualenv and install deps

```bash
cd ~/sgdr
python3.11 -m venv .venv          # 3.10/3.11/3.12 all fine
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Set environment variables

PA → Web tab → "Environment variables" section, add:

```
DJANGO_SETTINGS_MODULE   = config.settings
DJANGO_SECRET_KEY        = <generate a long random string>
DJANGO_DEBUG             = False
DJANGO_ALLOWED_HOSTS     = <yourname>.pythonanywhere.com,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS = https://<yourname>.pythonanywhere.com
GOATCOUNTER_SITE_CODE    =                    # fill after step 6
SYNC_SHARED_TOKEN        = <generate a long random string>
```

To generate a SECRET_KEY in the PA Bash:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Initial migrate + seed + collectstatic

```bash
cd ~/sgdr
source .venv/bin/activate
python manage.py migrate
python manage.py seed_mainboard_companies     # populates the 97 curated companies
python manage.py collectstatic --noinput
python manage.py createsuperuser              # for /admin/
```

### 5. Configure the Web tab

PA → Web tab → "Add a new web app":

- **Domain:** `<yourname>.pythonanywhere.com` (free)
- **Python version:** 3.11 (or whichever you used for the venv)
- **Framework:** Manual configuration

Then on the resulting Web tab page:

- **Source code:** `/home/<yourname>/sgdr`
- **Working directory:** `/home/<yourname>/sgdr`
- **Virtualenv:** `/home/<yourname>/sgdr/.venv`
- **WSGI configuration file:** click the blue link to edit. Replace its
  contents with:

  ```python
  import os, sys
  path = "/home/<yourname>/sgdr"
  if path not in sys.path:
      sys.path.insert(0, path)
  os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
  from config.wsgi import application  # noqa: F401
  ```

- **Static files:** add a mapping
  - URL: `/static/`
  - Directory: `/home/<yourname>/sgdr/staticfiles`

Click **Reload** at the top of the Web tab.

### 6. Sign up for GoatCounter

- Go to https://www.goatcounter.com/signup
- Pick a code (e.g. `sgdividendsreports`) → that becomes your dashboard at
  `https://<code>.goatcounter.com`
- Set `GOATCOUNTER_SITE_CODE = <code>` in PA's Web → Environment variables
- Reload the web app
- Visit `https://<yourname>.pythonanywhere.com/` — pageview should appear in
  GoatCounter within seconds

### 7. (Later) Wire the laptop sync

The `/sync/` endpoint and the laptop-side push script will be added in a
following step. Until then the SQLite DB only has the 97 curated companies
and zero events — the calendars will be empty placeholders.

## Updating later

After editing files locally, push to git (or re-upload zip) and on PA:

```bash
cd ~/sgdr
git pull                           # if using git
source .venv/bin/activate
pip install -r requirements.txt    # only if requirements changed
python manage.py migrate           # only if migrations changed
python manage.py collectstatic --noinput
# Then click "Reload" on the Web tab.
```
