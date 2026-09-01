# Bhaskar Voting System using Block-Chain

A simple Django voting web app built for local development / a final-year
college project. Users sign up, verify their email with a one-time
password (OTP), and cast exactly one vote. Every vote is appended to a
small local blockchain so the record is tamper-evident.

## Features

- Sign up with username, email, and password
- Email OTP verification (6-digit code, 10-minute expiry) before voting is allowed
- One vote per verified account, enforced at the database level (not just in the UI)
- Candidate/party list with an optional symbol and short bio
- A minimal SHA-256 hash-chained "blockchain" — one block per vote, chained to
  the previous block's hash — with a `/chain/` page that re-checks every
  hash and reports whether the chain is intact
- Public per-vote receipt code (a one-way hash) so a voter can prove their
  vote is on the chain without the chain revealing who they are
- Live results page with vote counts and percentages
- Django admin panel for managing candidates (votes and blocks are shown
  read-only in the admin — they're append-only by design)
- Local/dev-only email: OTPs print to the terminal by default (Django's
  "console" email backend), so nothing needs to be configured to try it out

## Project layout

```
bvsbc/
├── manage.py
├── requirements.txt
├── bvsbc/              # project settings, root urls
├── voting/             # the one app: models, views, forms, templates
│   ├── models.py       # VoterProfile, EmailOTP, Candidate, Vote, Block
│   ├── blockchain.py   # hashing / chain-verification logic
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── admin.py
│   ├── management/commands/seed_candidates.py
│   └── templates/voting/
├── templates/base.html # shared page layout
└── static/css/style.css
```

## Requirements

- Python 3.10+
- pip

## Setup (first time)

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply database migrations
python manage.py migrate

# 4. (Optional) create an admin account, to manage candidates from /admin/
python manage.py createsuperuser

# 5. Add a few sample candidates so the app has something to show
python manage.py seed_candidates
```

## Running the app

```bash
python manage.py runserver
```

Then open **http://127.0.0.1:8000/** in your browser.

## Using the app

1. Click **Sign up**, and register with a username, a real-looking email
   (it doesn't need to exist — see the email note below), and a password.
2. You'll be sent to the **verify your email** page. Look at the terminal
   where `runserver` is running — the OTP is printed there as part of a
   mock "email" (subject, to, and the code itself). Copy the 6-digit code.
3. Enter the code on the verify page. You'll be logged in automatically.
4. Go to **Vote**, pick one candidate, and submit. You cannot vote again
   with the same account afterwards.
5. Check **Results** for the live tally, or **Blockchain** to see every
   vote as a chained, hashed block and confirm the chain is still valid.
6. Candidates are managed from **/admin/** (needs the superuser account
   from step 4 above) — add, edit, or remove candidates there.

## About the email step (OTP delivery)

By default this project uses Django's **console email backend**
(`EMAIL_BACKEND` in `bvsbc/settings.py`), so "sending" an email just
prints it to the terminal. This is intentional: it keeps the whole
project runnable with zero external accounts or API keys, which matters
for a local demo.

To send real emails instead (e.g. for a live demo), open
`bvsbc/settings.py` and swap the email block for real SMTP settings —
for example, Gmail with an
[app password](https://myaccount.google.com/apppasswords):

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-16-char-app-password'
```

Keep real credentials out of source control — load them from environment
variables (`os.environ.get(...)`) rather than hardcoding them, especially
before pushing the project to GitHub.

## About the "blockchain"

This is a teaching-scale implementation, not a production blockchain:

- Each vote creates one `Block` row: `index`, `timestamp`, `data` (the
  candidate name and a one-way vote receipt hash), `previous_hash`, and
  `hash` (SHA-256 of everything above).
- The first block (`index 0`) is an automatically-created genesis block.
- `voting/blockchain.py` has a `verify_chain()` function that re-computes
  every block's hash from scratch and checks it against both the stored
  hash and the next block's `previous_hash`. The `/chain/` page runs this
  live, so editing a `Block` row directly in the database (e.g. via
  `/admin/` or a raw SQL query) will make the chain show up as broken from
  that point onward.
- There's no mining, proof-of-work, or networking — the goal is to make
  the "one immutable, verifiable record per vote" idea visible and
  demonstrable, not to reimplement Bitcoin.

## Double-vote prevention

Voting is guarded twice:

1. **Application logic** — the `vote` view checks for an existing `Vote`
   for the logged-in user before showing the ballot.
2. **Database constraint** — `Vote.voter` is a `OneToOneField`, so the
   database itself refuses a second `Vote` row for the same user even if
   the application-level check were bypassed.

## Resetting the demo data

To start over with a clean slate (fresh votes, fresh chain, same
candidates and users):

```bash
python manage.py shell -c "from voting.models import Vote, Block, VoterProfile; Vote.objects.all().delete(); Block.objects.all().delete(); VoterProfile.objects.update(has_voted=False)"
```

Or, for a fully clean install, delete `db.sqlite3` and re-run
`python manage.py migrate` followed by `seed_candidates`.
