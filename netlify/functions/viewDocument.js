// netlify/functions/viewDocument.js

const { sanitizeFilePath, getFileContent } = require('./helpers/github');

exports.handler = async function(event, context) {
  if (event.httpMethod !== 'GET') {
    return {
      statusCode: 405,
      body: JSON.stringify({ error: 'Method Not Allowed' }),
      headers: { 'Content-Type': 'application/json' },
    };
  }

  try {
    const docPath = event.queryStringParameters?.path;
    if (!docPath) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'Missing path query parameter' }),
        headers: { 'Content-Type': 'application/json' },
      };
    }

    const finalFilePath = sanitizeFilePath(docPath);
    const { content } = await getFileContent(finalFilePath);

    return {
      statusCode: 200,
      body: JSON.stringify({ markdown_content: content }),
      headers: { 'Content-Type': 'application/json' },
    };
  } catch (error) {
    console.error('Error in viewDocument function:', error);
    let statusCode = 500;
    let errorMessage = 'Internal Server Error';
    if (error.status === 404) {
      statusCode = 404;
      errorMessage = 'Document not found';
    }
    return {
      statusCode,
      body: JSON.stringify({ error: errorMessage, details: error.message }),
      headers: { 'Content-Type': 'application/json' },
    };
  }
};
