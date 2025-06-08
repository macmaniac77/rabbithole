# AGENT TASKS

The repository is a dynamic documentation website built with Flask. Markdown files live under `RABBITHOLE/markdown` and are organized as shown in `RABBITHOLE/ProjectFileTree.md`. The Flask app (`app.py`) builds a folder tree, serves Markdown as HTML and raw text, supports editing, and can generate new documents with OpenAI. The interface (`templates/index.html`) loads and edits files via JavaScript, while the root `index.html` is a separate landing page.

## Ultimate Goal
Recreate this system in TypeScript so that an agent can maintain and extend the documentation.

## Task Sequence
1. Use Node.js with Express to implement a server equivalent to `app.py`:
   - Build a recursive function to gather the folder structure from `RABBITHOLE/markdown`.
   - Serve the main interface at `/` with the folder structure.
   - Provide `/view_document/<path>` to return both HTML and Markdown.
   - Provide `/edit_document` to save updates.
   - Provide `/generate_document` to call OpenAI to alter or create documents.
2. Rebuild the UI from `templates/index.html` in TypeScript, using a Markdown parser such as `marked` and highlight.js for syntax highlighting.
3. Ensure links that end in `.md` load documents using the fetch logic; external links open in new tabs.
4. Implement editing, saving, and document generation features mirroring the current Flask implementation.
5. Keep the root `index.html` as a landing page linking to the new docs viewer.
