# Agent Instructions and Tasks

This repository hosts a dynamic documentation website, a "rabbit hole" of hyperlinked knowledge under `RABBITHOLE/markdown`, powered by a Flask application (`app.py`) and a static landing page (`index.html`). Markdown files are served as HTML or raw text, editable via a JavaScript-driven interface (`templates/index.html`), and expandable through AI-generated content (currently OpenAI, with planned Gemini integration). The ultimate goal is to recreate this system in TypeScript, enabling an agent to maintain and extend the knowledge base.

## Development Guidelines

- **Main Branch Hygiene**: Keep `main` clean with descriptive commit messages. Avoid force pushes.
- **Python Standards**: Adhere to PEP8 for Python files (`*.py`). Use explicit imports and docstrings for new functions. Validate syntax post-modification:
  ```bash
  python -m py_compile $(git ls-files '*.py')
  ```
- **TypeScript Standards**: For the TypeScript rewrite, follow clean code principles: simplicity, readability, meaningful naming. Use ESLint with Airbnb style guide for consistency.
- **Markdown Conventions**: Every Markdown file starts with a single `#` header naming the topic. Use relative links (e.g., `[title](../path/file.md)`) and keep paragraphs under 120 characters for readability.
- **File Naming**: Sanitize generated Markdown file names to simple ASCII characters, stored under `RABBITHOLE/markdown`.

## System Overview

- **Current Architecture**:
  - **Flask App (`app.py`)**: Builds a folder tree from `RABBITHOLE/markdown` (see [ProjectFileTree](../RABBITHOLE/ProjectFileTree.md)), serves Markdown as HTML or raw text, supports editing, and generates new documents via OpenAI.
  - **Interface (`templates/index.html`)**: JavaScript-driven UI for loading, editing, and viewing documents.
  - **Landing Page (`index.html`)**: Static entry point linking to the documentation viewer.
- **Future Architecture**: A TypeScript-based system using Node.js/Express, replicating Flask functionality with a modern, type-safe stack, integrating AI (OpenAI and Gemini) for content generation.

## Gemini Integration

- **Setup**: Use Google’s Gemini model via the `google-generativeai` library. Expose the API key as `GEMINI_API_KEY` in the environment.
- **Implementation**: Create a `gemini_utils` module (Python: `gemini_utils.py`, TypeScript: `geminiUtils.ts`) to handle generation requests, separate from OpenAI logic in `app.py` or its TypeScript equivalent.
- **Workflow**: Generated Markdown files are saved under `RABBITHOLE/markdown`, sanitized, and committed to the repository via the GitHub API.

## Stripe Webhook Flow

1. A successful Stripe payment triggers a webhook.
2. The webhook invokes the Gemini wrapper (or OpenAI) to generate or expand Markdown content based on user prompts.
3. New content is saved under `RABBITHOLE/markdown` and committed to the repository via the GitHub API, keeping the front page static and the backend updated.

## Task Sequence for TypeScript Migration

To recreate the system in TypeScript, enabling an agent to maintain and extend the documentation, follow these prioritized steps:

1. **Set Up Node.js/Express Server**:
   - Initialize a TypeScript project with Node.js, Express, and dependencies (`marked`, `highlight.js`).
   - Implement a recursive function to build the folder structure from `RABBITHOLE/markdown`, mirroring Flask’s logic.
   - Define routes:
     - `/`: Serve the main interface with the folder structure.
     - `/view_document/<path>`: Return Markdown as HTML (parsed with `marked`) or raw text, using `highlight.js` for syntax highlighting.
     - `/edit_document`: Accept POST requests to save updated Markdown content.
     - `/generate_document`: Call OpenAI (and later Gemini) to create or modify documents.
   - **Example** (simplified route for document viewing):
     ```typescript
     import { Request, Response } from 'express';
     import { marked } from 'marked';
     import fs from 'fs/promises';
     import path from 'path';

     const viewDocument = async (req: Request, res: Response) => {
       const docPath = path.join('RABBITHOLE/markdown', req.params.path);
       try {
         const content = await fs.readFile(docPath, 'utf-8');
         const html = marked(content);
         res.json({ html, markdown: content });
       } catch (error) {
         res.status(404).json({ error: 'Document not found' });
       }
     };
     ```

2. **Rebuild UI in TypeScript**:
   - Convert `templates/index.html` to a TypeScript/React (or similar) frontend.
   - Use `marked` for Markdown parsing and `highlight.js` for syntax highlighting.
   - Implement fetch logic for `.md` links to load documents via `/view_document/<path>`. External links open in new tabs.
   - Add editing and saving features via `/edit_document` and document generation via `/generate_document`.

3. **Integrate AI Content Generation**:
   - Implement OpenAI integration in TypeScript, mirroring Flask’s `app.py` logic.
   - Add Gemini support via a `geminiUtils.ts` module, ensuring compatibility with the Stripe webhook flow.
   - Save generated files under `RABBITHOLE/markdown` and commit via GitHub API.

4. **Maintain Static Landing Page**:
   - Keep `index.html` as a static entry point, linking to the TypeScript-based documentation viewer at `/`.

5. **Testing and Validation**:
   - Test routes with Jest/Supertest for server-side logic.
   - Validate UI functionality (document loading, editing, generation) with Cypress.
   - Ensure Markdown files adhere to conventions (header, relative links, line length).