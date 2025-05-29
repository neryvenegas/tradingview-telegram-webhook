from main import app  # pragma: no cover

# Render will still use gunicorn main:app; having this file lets you run
# `gunicorn wsgi:app` locally if you prefer.
