// netlify/functions/commitFileToGitHub.js

// Ensure you have 'octokit' as a dependency.
// You'll need to add it to your project's package.json and install it.
// For this subtask, we assume it will be available in the Netlify environment.

const { Octokit } = require('@octokit/rest'); // Correct import for Octokit v18+

// Get the GitHub token, repository owner, and repository name from environment variables
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const GITHUB_REPO_OWNER = process.env.GITHUB_REPO_OWNER; // e.g., 'YourGitHubUsername'
const GITHUB_REPO_NAME = process.env.GITHUB_REPO_NAME;   // e.g., 'your-repo-name'
const GIT_BRANCH = process.env.GIT_BRANCH || 'main';      // Default to 'main' branch

if (!GITHUB_TOKEN || !GITHUB_REPO_OWNER || !GITHUB_REPO_NAME) {
  console.error("Missing one or more GitHub environment variables: GITHUB_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME");
}

const octokit = new Octokit({ auth: GITHUB_TOKEN });

// Helper function to sanitize file paths, ensuring they are relative and within markdown folder
function sanitizeFilePath(filePath, baseDir = 'RABBITHOLE/markdown') {
    // Remove any leading slashes to ensure it's treated as relative to baseDir
    const relativePath = filePath.startsWith('/') ? filePath.substring(1) : filePath;

    // Combine with baseDir
    let fullPath = `${baseDir}/${relativePath}`;

    // Normalize: remove '..' and '.'
    const parts = fullPath.split('/');
    const normalizedParts = [];
    for (const part of parts) {
        if (part === '..') {
            if (normalizedParts.length > 0 && normalizedParts[normalizedParts.length -1] !== baseDir.split('/')[0]) { // Avoid going above baseDir's root component
                normalizedParts.pop();
            } else {
                // Trying to go above the intended base directory root part
                throw new Error('Invalid file path: attempts to navigate above allowed directory.');
            }
        } else if (part !== '.' && part !== '') {
            normalizedParts.push(part);
        }
    }
    fullPath = normalizedParts.join('/');

    // Final check to ensure it's still within the base directory or a subdirectory of it.
    if (!fullPath.startsWith(baseDir)) {
        throw new Error(`Invalid file path: '${filePath}' resolves outside of the allowed '${baseDir}' directory.`);
    }
    if (!fullPath.endsWith('.md')) {
        fullPath += '.md'; // Ensure it's a markdown file if no extension provided
    }
    return fullPath;
}


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

    let finalFilePath;
    try {
        finalFilePath = sanitizeFilePath(filePath);
    } catch (e) {
        console.error("Error sanitizing file path:", e.message);
        return {
            statusCode: 400,
            body: JSON.stringify({ error: 'Invalid file path provided.', details: e.message }),
            headers: { 'Content-Type': 'application/json' },
        };
    }


    const fileContentBase64 = Buffer.from(content).toString('base64');

    let sha;
    if (isUpdate) { // If isUpdate is true, we need the SHA of the existing file
        try {
            const { data: existingFile } = await octokit.repos.getContent({
                owner: GITHUB_REPO_OWNER,
                repo: GITHUB_REPO_NAME,
                path: finalFilePath,
                ref: GIT_BRANCH,
            });
            sha = existingFile.sha;
        } catch (error) {
            // If file not found, and it's an update, it's an error.
            // If it's not an update, then not finding it is fine.
            if (error.status === 404 && !isUpdate) {
                // This is fine, we are creating a new file
            } else if (error.status === 404 && isUpdate) {
                 console.error(`File not found for update at path: ${finalFilePath}`, error);
                 return {
                    statusCode: 404,
                    body: JSON.stringify({ error: 'File not found for update.', path: finalFilePath }),
                    headers: { 'Content-Type': 'application/json' },
                };
            }
            else {
                throw error; // Re-throw other errors
            }
        }
    }

    await octokit.repos.createOrUpdateFileContents({
      owner: GITHUB_REPO_OWNER,
      repo: GITHUB_REPO_NAME,
      path: finalFilePath,
      message: commitMessage,
      content: fileContentBase64,
      sha: sha, // Include SHA if updating an existing file, otherwise it's undefined for new files
      branch: GIT_BRANCH,
    });

    return {
      statusCode: 200,
      body: JSON.stringify({ message: `File '${finalFilePath}' processed successfully on branch '${GIT_BRANCH}'.` }),
      headers: { 'Content-Type': 'application/json' },
    };

  } catch (error) {
    console.error('Error in commitFileToGitHub function:', error);
    let statusCode = 500;
    let errorMessage = 'Internal Server Error';
    if (error.status) { // Octokit errors often have a status
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
