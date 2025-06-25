# AGENT TASKS

The repository is a dynamic documentation website built with Flask. Markdown files live under `RABBITHOLE/markdown` and are organized as shown in `RABBITHOLE/ProjectFileTree.md`. The Flask app (`app.py`) builds a folder tree, serves Markdown as HTML and raw text, supports editing, and can generate new documents with OpenAI. The interface (`templates/index.html`) loads and edits files via JavaScript, while the root `index.html` is a separate landing page. The goal is to keep the implementation simple with plain HTML and JavaScript (no TypeScript).

## Ultimate Goal
Maintain and extend this documentation website using plain HTML and JavaScript. Begin with a front-end only version that can be served on Netlify. Once that is stable, add a simple backend (Flask or Node.js) to store edits, generate new Markdown files, and keep a change history of documents.

## Task Sequence
### Phase 1 – Front-End MVP (HTML + JS)
1. Set up a basic site with `/public/index.html`, `/src/app.js`, and a `/src/markdown` folder. Use `marked.js` and `highlight.js` to render Markdown.
2. Implement navigation: clicking an `.md` link fetches and renders that file.
3. Add an “Edit” button that swaps the viewer for a `<textarea>` and saves changes to `localStorage`.
4. Provide a form to create new links and stub a “Generate Document” button that only logs prompts to the console.
5. Include breadcrumbs, a random page button, and optional “Goosebumps mode” choices.

### Phase 2 – Backend for Persistence
1. Use Flask or Node.js (plain JavaScript) to mirror the current server:
   - Recursively build the folder structure from `RABBITHOLE/markdown`.
   - Serve the main interface at `/` with the folder tree.
   - Provide `/view_document/<path>` to return HTML and Markdown.
   - Provide `/edit_document` to persist edits and record change history (e.g., save versioned copies or commit to Git).
   - Provide `/generate_document` for OpenAI-backed creation or alteration.
2. Update the front-end to communicate with these endpoints and handle editing, generation, and history display.
