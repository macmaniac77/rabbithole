# Agent Instructions

This repository hosts a Flask application and a static Markdown library stored under `RABBITHOLE/markdown`. The site is designed as a "rabbit hole"—a deep, hyperlinked knowledge base that can grow automatically through AI generated content.

## Development Guidelines

- Keep the `main` branch clean. Commit descriptive messages and avoid force pushes.
- Follow PEP8 for all Python code (`*.py`). Use explicit imports and docstrings for new functions.
- After modifying Python files run:
  ```bash
  python -m py_compile $(git ls-files '*.py')
  ```
  This ensures there are no syntax errors.

## Gemini Integration

- Future expansions will use Google's Gemini model via the `google-generativeai` library. Obtain an API key and expose it as `GEMINI_API_KEY` in the environment.
- When integrating, create a small wrapper module (e.g., `gemini_utils.py`) that handles generation requests. Keep this separate from existing OpenAI functions in `app.py`.
- Generated Markdown files should be saved under `RABBITHOLE/markdown`. Sanitize file names with simple ASCII characters.

## Stripe Webhook Flow

1. A successful payment event from Stripe triggers a webhook.
2. The webhook calls the Gemini wrapper to generate new content or expand existing pages based on user prompts.
3. New content is written to the Markdown directory and committed back to the repository using the GitHub API.

This workflow allows paying users to expand the rabbit hole while keeping the front page static and the backend updated via GitHub.

## Document Conventions

- Every Markdown file should begin with a single `#` header naming the topic.
- Use relative links (e.g., `[title](../path/file.md)`) to connect pages. Avoid absolute URLs whenever possible.
- Keep paragraphs under 120 characters per line for readability.
