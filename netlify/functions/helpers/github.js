// netlify/functions/helpers/github.js

const { Octokit } = require('@octokit/rest');

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const GITHUB_REPO_OWNER = process.env.GITHUB_REPO_OWNER;
const GITHUB_REPO_NAME = process.env.GITHUB_REPO_NAME;
const GIT_BRANCH = process.env.GIT_BRANCH || 'main';

if (!GITHUB_TOKEN || !GITHUB_REPO_OWNER || !GITHUB_REPO_NAME) {
    console.error('Missing one or more GitHub environment variables: GITHUB_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME');
}

const octokit = new Octokit({ auth: GITHUB_TOKEN });

function sanitizeFilePath(filePath, baseDir = 'RABBITHOLE/markdown') {
    const relativePath = filePath.startsWith('/') ? filePath.substring(1) : filePath;
    let fullPath = `${baseDir}/${relativePath}`;
    const parts = fullPath.split('/');
    const normalizedParts = [];
    for (const part of parts) {
        if (part === '..') {
            if (normalizedParts.length > 0 && normalizedParts[normalizedParts.length - 1] !== baseDir.split('/')[0]) {
                normalizedParts.pop();
            } else {
                throw new Error('Invalid file path: attempts to navigate above allowed directory.');
            }
        } else if (part !== '.' && part !== '') {
            normalizedParts.push(part);
        }
    }
    fullPath = normalizedParts.join('/');
    if (!fullPath.startsWith(baseDir)) {
        throw new Error(`Invalid file path: '${filePath}' resolves outside of the allowed '${baseDir}' directory.`);
    }
    if (!fullPath.endsWith('.md')) {
        fullPath += '.md';
    }
    return fullPath;
}

async function getFileContent(filePath) {
    const { data: existingFile } = await octokit.repos.getContent({
        owner: GITHUB_REPO_OWNER,
        repo: GITHUB_REPO_NAME,
        path: filePath,
        ref: GIT_BRANCH,
    });
    return {
        content: Buffer.from(existingFile.content, 'base64').toString('utf-8'),
        sha: existingFile.sha,
    };
}

async function commitFile(filePath, content, commitMessage, sha) {
    await octokit.repos.createOrUpdateFileContents({
        owner: GITHUB_REPO_OWNER,
        repo: GITHUB_REPO_NAME,
        path: filePath,
        message: commitMessage,
        content: Buffer.from(content).toString('base64'),
        sha: sha,
        branch: GIT_BRANCH,
    });
}

module.exports = {
    sanitizeFilePath,
    getFileContent,
    commitFile,
};
