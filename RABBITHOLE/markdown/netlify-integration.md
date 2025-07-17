# Netlify Integration Overview

This document outlines how to connect the Rabbit Hole documentation system to Netlify.
Users can generate or update Markdown files through serverless functions.

## Architecture

- **Frontend (Netlify)**: Static site built from `index.html` or a React project.
  Users submit prompts to generate or edit documents.
- **Backend (Netlify Functions)**: Functions in `netlify/functions` call Gemini or
  OpenAI and commit changes to GitHub using Octokit.
- **GitHub Repository**: Markdown lives under `RABBITHOLE/markdown`. Commits keep
  the site in sync with new documents.

## Environment Variables

Set these variables in Netlify so the functions can reach external services:

- `GITHUB_TOKEN` – personal access token with repo access.
- `GITHUB_REPO_OWNER` – repository owner.
- `GITHUB_REPO_NAME` – repository name.
- `GEMINI_API_KEY` – Gemini key for text generation.
- `OPENAI_API_KEY` – optional key for OpenAI models.
- `XAI_API_KEY` – optional key for xAI models.
- `ANTHROPIC_API_KEY` – optional key for Anthropic Claude.
- `DEEPSEEK_API_KEY` – optional key for DeepSeek.
- `GIT_BRANCH` – branch to commit to (`main` by default).

## Workflow

1. **User Request** – The frontend captures the path of the document being viewed
   and posts it (along with the user's click history) to a Netlify Function.
2. **Function Call** – The handler generates text with Gemini and decides whether
   to create or update a file.
3. **Git Commit** – The file content is committed via Octokit using the sanitized
   path.
4. **Site Update** – Netlify rebuilds when new commits arrive, publishing the
   updated rabbit hole.

## Security Considerations

- Environment variables are only visible to serverless functions, keeping keys
  private.
- Sanitize file paths with `sanitizeFilePath` to avoid writes outside
  `RABBITHOLE/markdown`.
- Add authentication or rate limiting to prevent spam on a public instance.

With this setup, anyone can request new branches or edits, and the site will grow
automatically.
