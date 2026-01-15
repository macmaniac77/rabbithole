// netlify/functions/generateContent.js

const { generateContent } = require('./helpers/gemini');

exports.handler = async function(event, context) {
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      body: JSON.stringify({ error: 'Method Not Allowed' }),
      headers: { 'Content-Type': 'application/json' },
    };
  }

  try {
    const { prompt_text, title_prompt_text } = JSON.parse(event.body);

    if (!prompt_text) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'Missing prompt_text in request body' }),
        headers: { 'Content-Type': 'application/json' },
      };
    }

    const generatedContent = await generateContent(prompt_text);
    let generatedTitle = null;
    if (title_prompt_text) {
      generatedTitle = (await generateContent(title_prompt_text)).replace(/\n/g, ' ').trim();
    }

    return {
      statusCode: 200,
      body: JSON.stringify({
        title: generatedTitle,
        content: generatedContent,
      }),
      headers: { 'Content-Type': 'application/json' },
    };

  } catch (error) {
    console.error('Error in generateContent function:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Internal Server Error', details: error.message }),
      headers: { 'Content-Type': 'application/json' },
    };
  }
};
