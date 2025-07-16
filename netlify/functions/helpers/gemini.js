// netlify/functions/helpers/gemini.js

const { GoogleGenerativeAI } = require('@google/generative-ai');

const GEMINI_API_KEY = process.env.GEMINI_API_KEY;

if (!GEMINI_API_KEY) {
    console.error('GEMINI_API_KEY environment variable not set.');
}

const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);

async function generateContent(prompt) {
    const model = genAI.getGenerativeModel({ model: 'gemini-pro' });
    const result = await model.generateContent(prompt);
    const response = await result.response;
    return await response.text();
}

async function generateJsonContent(prompt) {
    const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash-latest' });
    const generation_config = { response_mime_type: 'application/json' };
    const result = await model.generateContent(prompt, generation_config);
    const response = await result.response;
    return JSON.parse(await response.text());
}

module.exports = {
    generateContent,
    generateJsonContent,
};
