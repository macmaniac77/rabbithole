from typing import Dict, Optional # Add Optional

def get_prompt_for_bigger(document_content: str, document_id: str, path_history_summary: Optional[str] = None) -> str:
    """
    Generates a prompt for the LLM to expand the given document content.
    """
    history_context_str = ""
    if path_history_summary:
        history_context_str = f"""
Context: The user reached the current document ('{document_id}') through a specific navigation path.
Summary of this path:
{path_history_summary}
---
"""

    prompt = f"""
{history_context_str}
The following content is from the document titled '{document_id}'.
Your task is to expand this content significantly, making it 'bigger'.
This means adding more details, explanations, examples, elaborations,
and supporting information where appropriate, keeping in mind the provided navigation context if available.
Ensure the expanded content maintains a coherent flow and stays true to the original subject matter.
Do not just add a little bit; aim for a substantial increase in depth and breadth.
Do not include any introductory or concluding phrases like "Here's the expanded content:" or "Okay, I've expanded it.".
Just provide the fully expanded version of the text.

Original content of '{document_id}':
---
{document_content}
---

Expanded content:
"""
    return prompt

def get_prompts_for_deeper(document_content: str, document_id: str, path_history_summary: Optional[str] = None) -> str:
    history_context_str = ""
    if path_history_summary:
        history_context_str = f"""
Context: The user reached the current document ('{document_id}') through a specific navigation path.
Summary of this path:
{path_history_summary}
---
"""
    
    prompt = f"""
{history_context_str}
You are an AI assistant tasked with making the document '{document_id}' 'deeper' by identifying a core concept within it and generating a new, separate article about that concept, taking into account the user's navigation history if provided. You will also specify where to link this new article from the original document.

Please perform the following steps based on the original content provided below:

1.  **Identify a Core Concept**: Analyze the original content and identify a single, specific, and significant core concept, phrase, or term that is suitable for expansion into a new, detailed document.
2.  **Suggest a Title for the New Document**: Create a concise, descriptive, and engaging title for the new document about this core concept. The title should be suitable for use as a filename (e.g., avoid special characters).
3.  **Specify the Linking Phrase**: Identify the exact phrase or sentence in the original document where a link to this new document should be inserted. This phrase should be directly related to the core concept.
4.  **Generate Content for the New Document**: Write a comprehensive new article about the identified core concept. This article should be detailed, informative, and stand alone as a new piece of content.

Original content of '{document_id}':
---
{document_content}
---

Please provide your response as a JSON object with the following exact keys:
"core_concept": "The core concept you identified",
"new_doc_title": "The title you suggest for the new document",
"link_phrase_in_original_doc": "The exact phrase from the original document to be linked",
"new_doc_content": "The full content for the new document you generated"
"""
    # Example of expected JSON output format is part of the prompt in llm_strategies.py
    return prompt

# Example usage (for testing, not part of the file's normal execution):
if __name__ == '__main__':
    sample_doc_id_b = "My Sample Document for Bigger"
    sample_content_b = "This is a short document. It needs more content."
    sample_history_b = "User navigated from Homepage -> Section A -> My Sample Document for Bigger"
    
    prompt_b_no_hist = get_prompt_for_bigger(sample_content_b, sample_doc_id_b)
    print("--- PROMPT FOR BIGGER (No History) ---")
    print(prompt_b_no_hist)

    prompt_b_with_hist = get_prompt_for_bigger(sample_content_b, sample_doc_id_b, sample_history_b)
    print("\n--- PROMPT FOR BIGGER (With History) ---")
    print(prompt_b_with_hist)

    sample_doc_id_d = "My Sample Document for Deeper"
    sample_content_d = "The main idea is about photosynthesis, which is crucial for plants. We also touch on cellular respiration."
    sample_history_d = "User read Introduction to Biology -> Plant Processes -> My Sample Document for Deeper"
    
    prompt_d_no_hist = get_prompts_for_deeper(sample_content_d, sample_doc_id_d)
    print("\n--- PROMPT FOR DEEPER (No History - expects JSON response from LLM) ---")
    print(prompt_d_no_hist)

    prompt_d_with_hist = get_prompts_for_deeper(sample_content_d, sample_doc_id_d, sample_history_d)
    print("\n--- PROMPT FOR DEEPER (With History - expects JSON response from LLM) ---")
    print(prompt_d_with_hist)
