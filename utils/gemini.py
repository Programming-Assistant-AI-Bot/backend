import google.generativeai as genai
import json

# Replace with your actual Gemini API key
genai.configure(api_key="AIzaSyANS1TCO4NDxO9g6c2gtQoQGFYFVeKAKQA")

# Load the model with safety settings
model = genai.GenerativeModel('gemini-2.0-flash',
    safety_settings=[
        {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}
    ]
)

def generate_session_title(text: str) -> str:
    try:
        response = model.generate_content(
            f"Convert this text into a clear, concise title (3-5 words): '{text}'. "
            "Follow these rules: "
            "1. Use title case "
            "2. No ending punctuation "
            "3. Focus on main keywords "
            "4. Keep it descriptive but short "
            "5. Should be a summarized meaningful title "
            "6. Do not use the words like Perl, Code, Script "
            "eg: Query: Write a program to add 2 numbers  title: Addition of Two Numbers"
        )
        return response.text.strip('"').strip("'").replace("\n", " ") if response and response.text else "Title generation failed"
    except Exception as e:
        return f"Error: {str(e)}"

# --- New Function: Code Error Checking ---
# This is the new asynchronous function for finding errors in code.
# It uses the same 'model' object defined above.

async def get_code_errors(perl_code: str) -> list:
    """
    Sends Perl code to the Gemini API to find syntax and logical errors.

    Args:
        perl_code: A string containing the Perl code to check.

    Returns:
        A list of error dictionaries, or an empty list if no errors are found
        or if the API response is invalid.
    """
    prompt = f"""
You are an expert Perl developer and a very strict, line-by-line code linter.
Your task is to analyze the following Perl code and identify ALL possible errors.

CRITICAL INSTRUCTION 1: Do not stop after finding the first error. You MUST report every single error you find in the code.

CRITICAL INSTRUCTION 2: The location data (line, start, end) MUST be precise. For example, if an undeclared variable is used on line 10, the "line" number in your JSON response MUST be 10. Do not report the line where the variable should have been declared or where the hash was defined. Pinpoint the exact location of the usage error.

This includes:

Syntax errors (e.g., missing semicolons, incorrect operators).

Undeclared variables (due to use strict).

Typos in variable or function names.

Potential logical errors.

For each error you find, provide the information in a JSON array format.
Each object in the array must have these keys: "line", "start", "end", and "message".

"line": The exact line number where the error occurs (1-indexed).

"start": The starting column number of the error on that line (0-indexed).

"end": The ending column number of the error on that line (0-indexed).

"message": A clear, concise description of the error.

If you find no errors, you MUST return an empty array: [].

Here is the Perl code:


{perl_code}
```
"""

    try:
        # We use the async version of the call here because this function is async
        response = await model.generate_content_async(prompt)

        # The model's response text might have markdown formatting (```json ... ```)
        # We need to clean it to get the raw JSON string.
        cleaned_json = response.text.strip().replace("```json", "").replace("```", "").strip()

        # Parse the cleaned string into a Python list of dictionaries
        errors = json.loads(cleaned_json)
        
        # Basic validation to ensure we have a list
        if isinstance(errors, list):
            return errors
        else:
            print(f"Gemini response was not a valid JSON list: {cleaned_json}")
            return []

    except Exception as e:
        # If anything goes wrong (API error, JSON parsing error),
        # return an empty list so the extension doesn't crash.
        print(f"An error occurred while checking code with Gemini: {e}")
        return []

    
def getResponse(text: str) ->str:
    try:
        response = model.generate_content(
            f"You are a chatbot called Archelon specialized for perl language coding, answer this one in detail if it asks for explain explain this,: '{text}'. "
            "Follow these rules: "
            "1. Use title case "
            "2. No ending punctuation "
            "3. Focus on main keywords "
            "4. Keep it descriptive but short "
        )
        return response.text.strip('"').strip("'").replace("\n", " ") if response and response.text else "Response generation failed"
    except Exception as e:
        return f"Error: {str(e)}"
