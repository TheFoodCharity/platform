# COMP4800 - The Food Charity Association of Canada Platform

## Development Environment

The app is developed as a standard [Django 6.0](https://docs.djangoproject.com/en/6.0/) project, packaged as a container
for easy deployment.

### Setup

Prerequisites:

- [`uv`](https://docs.astral.sh/uv/)
- [Docker](https://www.docker.com/)

You'll need to have a Postgres database accessible. If you do not, one can be started using `docker compose up -d`.

```shell
# Install dependencies and a compatible Python interpreter
uv sync --dev

# Activate the virtual environment (optional)
# If activated, you can remove the `uv run` prefix from commands
source .venv/bin/activate # Linux/MacOS
.venv/bin/activate.bat    # Windows

# Register pre-commit hooks
uv run prek install

# Copy example environment file
cp .env.example .env
# Be sure to update this as needed

# Start the development server
uv run ./manage.py migrate
uv run ./manage.py runserver
```

In a second terminal, start the Tailwind watcher while working on templates or CSS:

```shell
cd theme/static_src
npm run dev
```

If the UI looks like plain HTML, the Tailwind CSS probably needs to be rebuilt:

```shell
cd theme/static_src
npm run build
```

### Common Tasks

Below are some common tasks that may come in handy.

```shell
# Create a new migration
uv run ./manage.py makemigrations
# List all the migrations
uv run ./manage.py showmigrations

# Start a Python REPL
uv run ./manage.py shell

# Run unit tests
uv run ./manage.py test

# Create an admin account
uv run ./manage.py createsuperuser
```
