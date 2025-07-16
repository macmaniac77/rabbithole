// netlify/functions/commitFileToGitHub.js

const { sanitizeFilePath, getFileContent, commitFile } = require('./helpers/github');

exports.handler = async function(event, context) {
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      body: JSON.stringify({ error: 'Method Not Allowed' }),
      headers: { 'Content-Type': 'application/json' },
    };
  }

  try {
    const { filePath, content, commitMessage, isUpdate } = JSON.parse(event.body);

    if (!filePath || content === undefined || !commitMessage) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'Missing filePath, content, or commitMessage in request body' }),
        headers: { 'Content-Type': 'application/json' },
      };
    }

    const finalFilePath = sanitizeFilePath(filePath);

    let sha;
    if (isUpdate) {
        try {
            const file = await getFileContent(finalFilePath);
            sha = file.sha;
        } catch (error) {
            if (error.status === 404) {
                 return {
                    statusCode: 404,
                    body: JSON.stringify({ error: 'File not found for update.', path: finalFilePath }),
                    headers: { 'Content-Type': 'application/json' },
                };
            }
            throw error;
        }
    }

    await commitFile(finalFilePath, content, commitMessage, sha);

    return {
      statusCode: 200,
      body: JSON.stringify({ message: `File '${finalFilePath}' processed successfully.` }),
      headers: { 'Content-Type': 'application/json' },
    };

  } catch (error) {
    console.error('Error in commitFileToGitHub function:', error);
    let statusCode = 500;
    let errorMessage = 'Internal Server Error';
    if (error.status) {
        statusCode = error.status;
        errorMessage = error.message;
    }
    return {
      statusCode: statusCode,
      body: JSON.stringify({ error: errorMessage, details: error.message }),
      headers: { 'Content-Type': 'application/json' },
    };
  }
};
