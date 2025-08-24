# Boathouse Value-Tree Engine (Flask Implementation)

This project is an evolving implementation of the Boathouse Value-Tree Engine, currently built using Flask. It aims to create a system where user interactions, potentially driven by payments, lead to the creation and modification of content and tasks, managed as ValuePoints within a UserContext.

## Core Components

*   **`app.py`**: The main Flask application.
    *   Serves markdown files from the `RABBITHOLE/markdown` directory.
    *   Integrates with OpenAI's GPT models for content generation and modification (`/generate_document`, `/edit_document`).
    *   Manages `UserContext` (in-memory for now) to track user state, credits, and ValuePoints.
    *   Manages `ValuePoint` lifecycle (creation, completion).
    *   Includes placeholder webhook endpoints for Stripe (`/webhook/stripe`) and Lightning (`/webhook/lightning`).
    *   Provides an API endpoint (`/vp/complete`) to mark ValuePoints as complete.
*   **`models.py`**: Defines the Pydantic data models:
    *   `ValuePoint`: Represents tasks, payments, contracts, etc.
    *   `UserContext`: Holds user-specific data, including active/completed VPs and credits.
*   **`git_ops.py`**: Contains conceptual design and helper functions for future Git integration. Actual Git commands are not yet implemented.
*   **`RABBITHOLE/markdown/`**: Directory containing markdown content, which can be viewed and edited through the application.
*   **`templates/`**: Contains HTML templates for the Flask application (e.g., `index.html`).

## Key API Endpoints

*   `/`: Main page, displays file structure, user context, and active ValuePoints.
*   `/view_document/<path:doc_path>`: Displays a markdown document as HTML.
*   `/edit_document` (POST): Saves changes to a markdown document.
*   `/generate_document` (POST): Generates or alters markdown content using an LLM.
*   `/webhook/stripe` (POST): Placeholder for Stripe payment webhooks.
*   `/webhook/lightning` (POST): Placeholder for Lightning payment webhooks.
*   `/vp/complete` (POST): Marks a ValuePoint as complete for a user.

## Future Development (High-Level from Original Proposal)

*   Full Stripe and Lightning integration.
*   Persistent storage (SQLite/Postgres) for UserContext and ValuePoints.
*   Full GitOps layer for versioning all changes.
*   Deployment to TinyBox/Cloud.
*   More sophisticated ValuePoint spawning and UI interaction based on `ValuePoint.interface`.

For a more detailed architecture overview, see `docs/ARCHITECTURE.md`.

## Environment Variables

Set the following variables in the Netlify dashboard (Site → Settings → Environment):

- `PLAUSIBLE_DOMAIN`
- `PLAUSIBLE_SCRIPT_URL`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `CAL_PUBLIC_LINK`
