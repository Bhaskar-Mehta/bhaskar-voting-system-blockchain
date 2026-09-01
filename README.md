# Bhaskar Voting System using Block-Chain

A simple Django-based online voting system with email OTP verification
and a blockchain-style, tamper-evident vote ledger — built as a final
year college project.

## Features

- Sign up with username, email, and password
- Email OTP verification (6-digit code, 10-minute expiry) before voting is allowed
- One vote per verified account, enforced at the database level
- Candidate/party list with an optional symbol and short bio
- A minimal SHA-256 hash-chained "blockchain" — one block per vote,
  chained to the previous block's hash — with a live chain-integrity check
- Public per-vote receipt code so a voter can confirm their vote is on
  the chain without revealing who they voted for
- Live results page with vote counts and percentages
- Django admin panel for managing candidates
- Local/dev-only email: OTPs print to the terminal by default, so
  nothing needs to be configured to try it out

## Quick start

\`\`\`bash
python -m venv venv
source venv/bin/activate        # Windows: venv\\Scripts\\activate

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
python manage.py seed_candidates
python manage.py runserver
\`\`\`

Then open **http://127.0.0.1:8000/**.

## Tech stack

Python, Django, SQLite (default local dev database), HTML/CSS.

## Note

> If you kept the `bvsbc/` folder as the project root, `cd bvsbc` before
> running the commands above, and see `bvsbc/README.md` for full setup
> details, how the OTP email flow works, and how the blockchain and
> double-vote prevention are implemented.
