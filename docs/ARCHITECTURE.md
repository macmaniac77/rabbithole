# Boathouse Value-Tree Engine - Architecture Overview (Flask-based)

This document outlines the architecture of the Boathouse Value-Tree Engine, currently implemented as a Flask application.

## 1. High-Level Goal

To create a platform where transactions, tasks, or ideas become "Value Points" (VPs) in a living tree, driving content creation and system evolution. The system is designed for local execution with future cloud mirroring and deterministic APIs for AI agent integration.

## 2. Core Layers & Components (Current Implementation)

*   **Presentation Layer (Flask UI & Templates)**:
    *   **`templates/index.html`**: Primary user interface, rendered by Flask. Displays markdown file navigation, user context information (credits, active VPs), and allows interaction with VPs (e.g., marking as complete).
    *   **Markdown Rendering**: Markdown files from `RABBITHOLE/markdown/` are rendered as HTML for viewing.

*   **Application Layer (Flask - `app.py`)**:
    *   **Request Handling**: Manages incoming HTTP requests for viewing/editing documents, AI content generation, webhook processing, and ValuePoint management.
    *   **User Context Management**:
        *   Identifies users (currently via a simple hardcoded ID, planned for JWT).
        *   Stores and retrieves `UserContext` objects (currently in-memory, planned for SQLite/Postgres). `UserContext` tracks active/completed VPs, user credits, and last inputs.
    *   **ValuePoint Engine (Core Logic in `app.py`)**:
        *   Manages `ValuePoint` instances (defined in `models.py`, stored in-memory).
        *   Handles creation of VPs (e.g., sample VPs, VPs from payments).
        *   Processes VP completion via `/vp/complete`, updating `UserContext`.
        *   Includes placeholder logic for spawning child VPs.
    *   **LLM Integration**: Interfaces with OpenAI API (`/generate_document`, `/edit_document`) to modify or create markdown content based on prompts and user context.
    *   **Commerce Gateway (Placeholders)**:
        *   `/webhook/stripe` and `/webhook/lightning`: Endpoints to receive payment notifications. Currently, they log data and create "payment" VPs. Full SDK integration is pending.

*   **Data Layer (`models.py` & In-Memory Storage)**:
    *   **`models.py`**: Contains Pydantic definitions for `ValuePoint` and `UserContext`.
    *   **In-Memory Dictionaries**: `user_contexts` and `value_points_db` in `app.py` currently serve as temporary storage.
    *   **File System (`RABBITHOLE/markdown/`)**: Stores the actual content (markdown files) that VPs might relate to or that the LLM modifies.

*   **Git Ops Layer (`git_ops.py` - Conceptual)**:
    *   **`git_ops.py`**: Defines helper functions for preparing commit messages and identifying changed files.
    *   **Conceptual Commits**: Calls to `commit_and_push` are integrated into `app.py` at points like VP completion or document modification, but these currently only log intent. Actual Git CLI operations are not yet implemented.
    *   **Goal**: To commit every significant context change and content modification to a Git repository.

## 3. Data Models

*   **`ValuePoint`**: (See `models.py` for full definition)
    *   `id`, `title`, `vp_type` (payment, contract, task, etc.), `price_usd`, `price_sat`, `next` (child VPs), `expires`, `interface` (UI slug), `creditable`, `btc_commit`.
*   **`UserContext`**: (See `models.py` for full definition)
    *   `user_id`, `active_vps`, `completed_vps`, `credits_usd`, `credits_sat`, `last_input`, `infra` (local path, mirror URL, etc.).

## 4. API Endpoints (Key Examples)

*   `/` (GET): Serves the main UI.
*   `/view_document/<path:doc_path>` (GET): Serves rendered markdown.
*   `/edit_document` (POST): Updates markdown files.
*   `/generate_document` (POST): Uses LLM to generate/update markdown.
*   `/webhook/stripe` (POST): Stripe webhook.
*   `/webhook/lightning` (POST): Lightning webhook.
*   `/vp/complete` (POST): Marks a VP as done.

## 5. Planned Evolution (Key Items from Original Proposal)

*   **Database Persistence**: Transition from in-memory storage to SQLite (dev) and Postgres (prod) for `UserContext` and `ValuePoint` data.
*   **Full Commerce Integration**: Implement Stripe SDK and LNbits (or similar) for robust payment processing.
*   **Robust Git Operations**: Fully implement Git CLI interactions, including handling PATs/SSH keys and push queues for offline scenarios.
*   **Authentication**: Implement JWT-based authentication.
*   **Dedicated UI for VPs**: Develop specific UIs for different `ValuePoint.interface` slugs, potentially beyond simple markdown rendering.
*   **Deployment**: Package for TinyBox (Docker-Compose) and cloud mirroring.
