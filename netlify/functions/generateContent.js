// netlify/functions/generateContent.js

// Ensure you have 'google-auth-library' and '@google/generative-ai' as dependencies.
// You'll need to add them to your project's package.json and install them.
// For this subtask, we assume these will be available in the Netlify environment
// by adding them to package.json in a later step or manually.

const { GoogleGenerativeAI } = require('@google/generative-ai');

// Get the API key from environment variables
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;

if (!GEMINI_API_KEY) {
  console.error("GEMINI_API_KEY environment variable not set.");
  // In a real scenario, you might want to prevent the function from even deploying
  // or have more robust error handling if the key is missing at runtime.
}

const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);

exports.handler = async function(event, context) {
  // Only allow POST requests
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      body: JSON.stringify({ error: 'Method Not Allowed' }),
      headers: { 'Content-Type': 'application/json' },
    };
  }

  try {
    const { prompt_text, title_prompt_text } = JSON.parse(event.body);

    if (!prompt_text || !title_prompt_text) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'Missing prompt_text or title_prompt_text in request body' }),
        headers: { 'Content-Type': 'application/json' },
      };
    }

    const model = genAI.getGenerativeModel({ model: 'gemini-pro' }); // Or your preferred model

    // Generate content
    let generatedContent = "";
    try {
      const contentResult = await model.generateContent(prompt_text);
      const contentResponse = await contentResult.response;
      generatedContent = await contentResponse.text();
    } catch (e) {
      console.error('Error generating content from Gemini:', e);
      generatedContent = `Error generating content: ${e.message}`;
      // Decide if you want to fail the whole function or return partial success
    }

    // Generate title
    let generatedTitle = "";
    try {
      const titleResult = await model.generateContent(title_prompt_text);
      const titleResponse = await titleResult.response;
      generatedTitle = await titleResponse.text();
    } catch (e) {
      console.error('Error generating title from Gemini:', e);
      generatedTitle = `Error generating title: ${e.message}`;
      // Decide if you want to fail the whole function or return partial success
    }

    // Sanitize title (simple example, consider more robust sanitization)
    generatedTitle = generatedTitle.replace(/[
]/g, ' ').trim();


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
