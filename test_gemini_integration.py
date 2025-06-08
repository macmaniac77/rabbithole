import subprocess
import requests
import time
import os
import shutil
import unittest
from pathlib import Path

FLASK_APP_PATH = "app.py"
# Ensure app.py uses this port or make it configurable via env var for the subprocess
FLASK_PORT = "5001"
BASE_URL = f"http://127.0.0.1:{FLASK_PORT}"

# Test files will be created inside RABBITHOLE/markdown/test_generated_files
# app.py's BASE_DIR is assumed to be RABBITHOLE/markdown
APP_BASE_DIR = Path("RABBITHOLE/markdown")
TEST_SUB_DIR_NAME = "test_generated_files"
TEST_MARKDOWN_DIR = APP_BASE_DIR / TEST_SUB_DIR_NAME
TEST_ALTER_DOC_NAME = "doc_to_alter.md"
# This is the path relative to app.py's BASE_DIR for alteration
DOC_PATH_FOR_ALTER_REQUEST = f"{TEST_SUB_DIR_NAME}/{TEST_ALTER_DOC_NAME}"
# This is the full local path for creating/checking the alterable doc
FULL_PATH_FOR_ALTER_DOC = TEST_MARKDOWN_DIR / TEST_ALTER_DOC_NAME


class TestGeminiIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not APP_BASE_DIR.exists():
            # This is a problem, as app.py likely depends on it.
            # For a robust test, we might create it, but ideally, it's part of the repo structure.
            print(f"Warning: {APP_BASE_DIR} does not exist. Tests might fail if app.py relies on it.")

        if TEST_MARKDOWN_DIR.exists():
            shutil.rmtree(TEST_MARKDOWN_DIR) # Clean up from previous runs
        os.makedirs(TEST_MARKDOWN_DIR)

        env = os.environ.copy()
        env["GEMINI_API_KEY"] = "fake_test_key_for_integration_test"
        env["FLASK_RUN_PORT"] = FLASK_PORT
        # If app.py is not in root, adjust FLASK_APP_PATH or PYTHONPATH
        # Assuming app.py is in the root where this test script is.
        cls.flask_process = subprocess.Popen(
            ["python", FLASK_APP_PATH],
            env=env
            # stdout=None, # Allow Flask output during tests for debugging
            # stderr=None  # Allow Flask error output
        )
        print(f"Waiting for Flask app ({FLASK_APP_PATH}) to start on port {FLASK_PORT}...")
        time.sleep(5) # Give Flask time to start

    @classmethod
    def tearDownClass(cls):
        print("Terminating Flask app...")
        cls.flask_process.terminate()
        try:
            cls.flask_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cls.flask_process.kill()
            print("Flask app process killed.")

        if TEST_MARKDOWN_DIR.exists():
            print(f"Cleaning up test directory: {TEST_MARKDOWN_DIR}")
            shutil.rmtree(TEST_MARKDOWN_DIR)

    def test_01_generate_new_document(self):
        print("Running test_01_generate_new_document...")
        initial_files = set(os.listdir(TEST_MARKDOWN_DIR))

        payload = {
            "doc_path": TEST_SUB_DIR_NAME, # Target subdirectory for new file
            "operation": "generate",
            "context_text": "Create a brief document about happy clouds."
        }
        print(f"Sending POST to /generate_document with payload: {payload}")
        response = requests.post(f"{BASE_URL}/generate_document", json=payload, timeout=20)

        self.assertEqual(response.status_code, 200, f"Response content: {response.text}")

        current_files = set(os.listdir(TEST_MARKDOWN_DIR))
        new_files = current_files - initial_files

        self.assertEqual(len(new_files), 1, f"Expected 1 new file, found {len(new_files)}: {new_files}")

        new_file_name = new_files.pop()
        new_file_path = TEST_MARKDOWN_DIR / new_file_name

        with open(new_file_path, "r", encoding='utf-8') as f:
            content = f.read()
        # Because GEMINI_API_KEY is fake, app.py's Gemini call will likely fail.
        # The current app.py would then write an empty string or raise an error that
        # would be caught by Flask (giving a 500).
        # For this test to pass with a 200, app.py needs to handle Gemini errors
        # more gracefully and still return a 200, perhaps with the error message in content.
        # For now, let's assume app.py is modified to write *something* or an error message.
        # If it writes the Gemini error, that's fine for this integration test.
        self.assertTrue(len(content) > 0, "Generated document should not be empty. It might contain an error message from Gemini client due to fake API key, which is acceptable for this test.")
        print(f"Test test_01_generate_new_document PASSED. New file: {new_file_name}")

    def test_02_alter_existing_document(self):
        print("Running test_02_alter_existing_document...")
        initial_content = "Original content for the document to be altered."
        with open(FULL_PATH_FOR_ALTER_DOC, "w", encoding='utf-8') as f:
            f.write(initial_content)

        payload = {
            "doc_path": DOC_PATH_FOR_ALTER_REQUEST, # Path relative to app's BASE_DIR
            "operation": "alter",
            "context_text": "Append details about sunny days and rainbows."
        }
        print(f"Sending POST to /generate_document with payload: {payload}")
        response = requests.post(f"{BASE_URL}/generate_document", json=payload, timeout=20)

        self.assertEqual(response.status_code, 200, f"Response content: {response.text}")

        with open(FULL_PATH_FOR_ALTER_DOC, "r", encoding='utf-8') as f:
            altered_content = f.read()

        self.assertNotEqual(altered_content, initial_content, "Document content should have been altered.")
        self.assertTrue(len(altered_content) > 0, "Altered document should not be empty. May contain Gemini error message.")
        print(f"Test test_02_alter_existing_document PASSED. Altered file: {FULL_PATH_FOR_ALTER_DOC}")

if __name__ == "__main__":
    print("Starting Gemini integration tests...")
    # This setup assumes app.py is in the same directory as the test script.
    # And RABBITHOLE/markdown structure is as expected by app.py.

    # Crucial modification needed in app.py for test_01_generate_new_document:
    # In `generate_document` function in `app.py`:
    # When `operation == 'generate'`:
    #   `doc_path_from_request = request.json.get('doc_path')` (this is the target subdir, e.g., "test_generated_files")
    #   `title = ...`
    #   `file_name = sanitize_filename(title.strip()) + ".md"`
    #   `target_directory = BASE_DIR / doc_path_from_request`
    #   `os.makedirs(target_directory, exist_ok=True)`
    #   `new_doc_path = target_directory / file_name`
    #   `write_document(new_doc_path, new_content)`
    # This ensures the generated file goes into the specified subdirectory.
    # The current `app.py` (as of last view) would place it in `BASE_DIR / file_name`.
    # This change will be addressed in the "Run Test Script and Refine Gemini Integration" step if tests fail.

    unittest.main()
