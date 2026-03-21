# Street Art Bot (Python)

Telegram bot for self-guided and live street art tours. Uses **uv** for the virtual environment and dependencies.

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed

## Setup

From the `new_version` directory:

```bash
cd new_version
uv sync
```

This creates `.venv/` (if missing), resolves dependencies from `pyproject.toml` + `uv.lock`, and installs the `bot` package in editable mode.

Copy environment variables:

```bash
cp .env.example .env
# edit .env — BOT_TOKEN, MONGO_URL, ADMIN_IDS
```

### MongoDB Atlas (`mongodb+srv://`)

Use your full Atlas connection string. Wrap it in **double quotes** in `.env` if it contains `&`:

```env
MONGO_URL="mongodb+srv://user:password@cluster0.xxxxx.mongodb.net/YourDbName?retryWrites=true&w=majority"
```

The bot uses the database name from the URI path (`YourDbName`). To override, set `MONGO_DB_NAME`.

If the password contains special characters (`@`, `:`, `/`, etc.), [URL-encode it](https://www.mongodb.com/docs/manual/reference/connection-string/) in the URI.

## Run

```bash
uv run python -m bot.main
```

Or activate the venv manually:

```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m bot.main
```

## Updating dependencies

```bash
uv add <package>
# or edit pyproject.toml, then:
uv lock
uv sync
```

## Legacy `requirements.txt`

Dependencies are defined in `pyproject.toml`. To export a `requirements.txt` for other tools:

```bash
uv export --no-hashes -o requirements.txt
```
