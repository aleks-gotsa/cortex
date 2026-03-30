"""Vercel serverless entrypoint — re-exports the FastAPI app."""

from backend.main import app  # noqa: F401
