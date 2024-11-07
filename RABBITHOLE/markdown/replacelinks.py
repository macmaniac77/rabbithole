import os
import re

# Define the directory containing markdown files
base_dir = r"C:\Users\maclaine.morham\Downloads\MAC\rabbithole\RABBITHOLE\markdown"

# Regular expression patterns for different types of HTML <a> tags
patterns = [
    # Pattern for links with onclick="loadMarkdown(\'path/to/doc.md\')" (escaped single quotes)
    (r'<a href="#" onclick="loadMarkdown\(\\\'([^\']+)\.md\\\'\)">([^<]+)</a>', r'[\2](\1.md)'),
    
    # Pattern for links with data-md="path/to/doc.md"
    (r'<a href="#" data-md="([^"]+)\.md"[^>]*>([^<]+)</a>', r'[\2](\1.md)'),

    # New pattern for links with onclick="loadMarkdown('path/to/doc.md')" (unescaped single quotes)
    (r'<a href="#" onclick="loadMarkdown\(\'([^\']+)\.md\'\)">([^<]+)</a>', r'[\2](\1.md)')
]

# Function to convert HTML links to markdown with debug information
def convert_html_to_markdown(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    changes_made = False

    # Apply each pattern to replace HTML <a> tags with markdown [text](link.md)
    for pattern, replacement in patterns:
        new_content, num_subs = re.subn(pattern, replacement, new_content)
        if num_subs > 0:
            changes_made = True
            print(f"Replaced {num_subs} links in {file_path} using pattern {pattern}")

    # Write changes back to file if any replacements were made
    if changes_made:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Converted links in {file_path}")
    else:
        print(f"No changes made in {file_path}")

# Walk through the directory and process each .md file
for root, _, files in os.walk(base_dir):
    for file_name in files:
        if file_name.endswith('.md'):
            file_path = os.path.join(root, file_name)
            convert_html_to_markdown(file_path)

print("All conversions completed.")