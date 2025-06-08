# Project Documentation: Rabbithole System

## Project Overview

The Rabbithole system is a dynamic content management and task automation platform with integrated AI capabilities. It allows users to interact with version-controlled Markdown documents, manage tasks and value exchanges (ValuePoints), and leverage AI for content generation and modification. The system incorporates payment processing via Stripe and Lightning Network, and maintains a versioned history of user and content states using Git.

## Architecture

### Backend

The backend is a Flask-based Python application. Key components include:

-   **`app.py`**: Serves as the main application entry point. It handles HTTP routing, core business logic, webhook processing (Stripe, Lightning), and integrates other modules.
-   **`database.py`**: Defines SQLAlchemy ORM models for database interaction and manages database sessions. It includes functions for table creation and session provision.
-   **`models.py`**: Contains Pydantic models used for data validation, serialization, and defining the structure of data objects like ValuePoints and UserContexts.
-   **`auth_utils.py`**: Provides utilities for JWT (JSON Web Token) based user authentication, including token creation, decoding, and route protection decorators.
-   **`git_ops.py`**: Manages all Git operations. This includes initializing repositories, committing user context data and markdown files, and pushing changes to a remote repository.
-   **`llm_strategies.py`**: Contains functions dedicated to generating specific prompts for interacting with Large Language Models (LLMs), tailoring requests for tasks like content expansion or detailed exploration.

### Database

-   The system uses **SQLite** as its database, accessed via the **SQLAlchemy ORM**.
-   Key database models (tables) include:
    -   `DBAuthUser`: Stores user authentication credentials (username, hashed password).
    -   `DBUserContext`: Manages user-specific state, including credit balances (USD, SATs), lists of active and completed ValuePoints, last user input, and other contextual data.
    -   `DBValuePoint`: Represents tasks, payments, contracts, or other "value points" within the system, defining their properties and relationships.

### Frontend Content

-   Primary content is managed as **Markdown files** located within the `RABBITHOLE/markdown/` directory and its subdirectories.
-   The Flask application renders these Markdown files dynamically.
-   Core HTML templates like `index.html` (main interface) and potentially `view.html` (if used for specific document views) are located in the `templates/` directory.

### GitOps Workflow

-   The `git_ops.py` module implements a GitOps-style workflow for versioning critical data.
-   User contexts (state, credits, etc.) are serialized as JSON files and committed to `RABBITHOLE_GIT_REPO/state/`.
-   Markdown documents, when created or modified through application workflows (especially LLM actions), are copied from the working directory (`RABBITHOLE/markdown/`) to `RABBITHOLE_GIT_REPO/markdown_content/` and committed.
-   This separate Git repository (`RABBITHOLE_GIT_REPO`) maintains a history of changes to both user states and managed content.
-   Markdown files within this Git repository are updated with **frontmatter metadata**, including `last_updated` (date) and `version` (Git commit hash of the file), to track revisions.

### AI Integration

-   The system leverages **Google Gemini** (via the `google.generativeai` or `genai` library) for AI-powered content operations.
-   Functionalities like "bigger" (expanding content) and "deeper" (generating detailed sub-topics and linking them) are driven by LLM interactions.
-   `llm_strategies.py` is responsible for the "prompt engineering" aspect, crafting the specific instructions sent to the LLM to achieve desired outcomes.

## Key Features

-   **Dynamic Markdown Content**: Serves and renders Markdown files, allowing for easy content creation and management.
-   **User Authentication**: Secure user registration and login using JWT-based authentication.
-   **ValuePoint System**: A flexible system for defining and managing tasks, payments, contracts, and other value exchanges.
-   **Payment Integration**:
    -   **Stripe Webhooks**: For processing fiat currency payments and triggering associated actions.
    -   **Lightning Network Webhooks**: For processing Bitcoin Lightning payments (via LNbits) and updating user credits.
-   **LLM-Powered Content Operations**:
    -   Content generation based on user prompts.
    -   Content modification features like "make it bigger" (expand) and "go deeper" (create linked, detailed articles).
-   **Git-Based Versioning**: All user context data and system-managed markdown content are version-controlled in a dedicated Git repository, providing history and auditability.

## Code Documentation

This project uses **docstrings** to document Python modules, classes, and functions, adhering to standard Python documentation practices.

For detailed explanations of specific functionalities, parameters, return values, and design choices, developers are encouraged to **read the docstrings directly within the source code**.

Key modules to start exploring include:
-   `app.py`: For understanding the overall application flow, routing, and integration points.
-   `git_ops.py`: For details on how Git versioning is implemented.
-   `database.py`: For the structure of database models.
-   `webhook_stripe` and `webhook_lightning` functions within `app.py` for payment processing logic.

By consulting the inline docstrings, developers can gain a deeper understanding of the system's components and their interactions.
