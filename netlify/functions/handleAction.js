// netlify/functions/handleAction.js

const { generateContent, generateJsonContent } = require('./helpers/gemini');
const { sanitizeFilePath, getFileContent, commitFile } = require('./helpers/github');

// Prompts from llm_strategies.py
function get_prompt_for_bigger(content, doc_path, history_summary) {
    return `
        **Objective:** Expand the following document to be more comprehensive.

        **Instructions:**
        1.  **Analyze the existing content:** Understand the core topic and key points.
        2.  **Identify areas for expansion:** Add more details, examples, or explanations.
        3.  **Maintain the original tone and style.**
        4.  **Ensure the output is a complete, self-contained Markdown document.**
        5.  **Do not add any conversational text or introductory phrases like "Here is the expanded document".**

        **Document Path:** ${doc_path}
        **User's navigation history:**
        ${history_summary}

        **Original Content:**
        ---
        ${content}
        ---
    `;
}

function get_prompts_for_deeper(content, doc_path, history_summary) {
    return `
        **Objective:** Create a new, more detailed document that explores a specific sub-topic from the original document.

        **Instructions:**
        1.  **Analyze the original content and identify a key concept or phrase that can be expanded into a new document.**
        2.  **Generate a new document with a clear title and detailed content.**
        3.  **The new document should be a self-contained Markdown file.**
        4.  **Identify the exact phrase in the original document where the link to the new document should be inserted.**

        **Output Format (JSON):**
        {
          "new_doc_title": "A concise, descriptive title for the new document.",
          "new_doc_content": "The full Markdown content of the new document.",
          "link_phrase_in_original_doc": "The exact phrase from the original document where the link should be inserted."
        }

        **Document Path:** ${doc_path}
        **User's navigation history:**
        ${history_summary}

        **Original Content:**
        ---
        ${content}
        ---
    `;
}

exports.handler = async function (event, context) {
    if (event.httpMethod !== 'POST') {
        return {
            statusCode: 405,
            body: JSON.stringify({ error: 'Method Not Allowed' }),
            headers: { 'Content-Type': 'application/json' },
        };
    }

    try {
        const { doc_path, action_type, document_path_history } = JSON.parse(event.body);

        if (!doc_path || !action_type) {
            return {
                statusCode: 400,
                body: JSON.stringify({ error: 'Missing doc_path or action_type in request body' }),
                headers: { 'Content-Type': 'application/json' },
            };
        }

        const finalFilePath = sanitizeFilePath(doc_path);

        const { content: originalContent, sha: fileSha } = await getFileContent(finalFilePath);

        if (action_type === 'bigger') {
            const prompt = get_prompt_for_bigger(originalContent, doc_path, JSON.stringify(document_path_history));
            const newContent = await generateContent(prompt);

            await commitFile(finalFilePath, newContent, `Expand document: ${finalFilePath}`, fileSha);

            return {
                statusCode: 200,
                body: JSON.stringify({ message: `Document '${finalFilePath}' expanded successfully.` }),
                headers: { 'Content-Type': 'application/json' },
            };
        } else if (action_type === 'deeper') {
            const prompt = get_prompts_for_deeper(originalContent, doc_path, JSON.stringify(document_path_history));
            const llm_data = await generateJsonContent(prompt);

            const { new_doc_title, new_doc_content, link_phrase_in_original_doc } = llm_data;

            const new_filename = new_doc_title.replace(/\s+/g, '_').replace(/[<>:"/\\|?*]/g, '') + ".md";
            const new_doc_dir_path = finalFilePath.substring(0, finalFilePath.lastIndexOf('/')) + "/deeper_links";
            const new_doc_full_path = `${new_doc_dir_path}/${new_filename}`;

            await commitFile(new_doc_full_path, new_doc_content, `Create deeper document: ${new_doc_full_path}`);

            if (link_phrase_in_original_doc && originalContent.includes(link_phrase_in_original_doc)) {
                const link_to_new = `./deeper_links/${new_filename}`;
                const updatedContent = originalContent.replace(link_phrase_in_original_doc, `${link_phrase_in_original_doc} ([${new_doc_title}](${link_to_new}))`);

                await commitFile(finalFilePath, updatedContent, `Add link to deeper document: ${new_doc_full_path}`, fileSha);
            }

            return {
                statusCode: 200,
                body: JSON.stringify({ message: `Document '${new_doc_full_path}' created and linked successfully.` }),
                headers: { 'Content-Type': 'application/json' },
            };
        } else {
            return {
                statusCode: 400,
                body: JSON.stringify({ error: 'Invalid action_type' }),
                headers: { 'Content-Type': 'application/json' },
            };
        }

    } catch (error) {
        console.error('Error in handleAction function:', error);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: 'Internal Server Error', details: error.message }),
            headers: { 'Content-Type': 'application/json' },
        };
    }
};
