import google.generativeai as genai
import json
from langchain_ollama import OllamaLLM
import asyncio
import re

# Replace with your actual Gemini API key
genai.configure(api_key="AIzaSyC0coFyomfjU26ViF5ShUABamuXcSJNGVc") 

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

# --- Final Updated Function for Reliable Error Detection ---
async def get_code_errors(perl_code: str) -> list:
    """
    Sends Perl code to the Gemini API to find errors.
    The prompt is now simplified to maximize the error detection rate.
    """
    # --- NEW, SIMPLIFIED PROMPT ---
    prompt = f"""
You are an expert Perl developer. Your task is to analyze the following Perl code and identify ALL possible syntax and logical errors. Your top priority is to find every single error.

This includes:
- Syntax errors (e.g., missing semicolons).
- Undeclared variables.
- Typos in function names.
- Logical errors (e.g., using == on strings instead of eq).

For each error you find, provide the information in a JSON array format.
Each object must have only these two keys: "line" and "message".

- "line": The exact line number where the error occurs (1-indexed).
- "message": A clear, concise description of the error.

CRITICAL: In the final JSON output, all backslash characters \\ within the message string MUST be properly escaped as \\\\.

--- EXAMPLE ---
Code:
`my $val = 10;
if ($val eq 10) {{ print "ok" }}`

Response:
[
  {{
    "line": 2,
    "message": "Logical Error: Using string comparison 'eq' on a number. Use '==' for numeric comparison."
  }}
]

If you find no errors, you MUST return an empty array: [].

Here is the Perl code:

perl
{perl_code}

"""

    try:
        response = await model.generate_content_async(prompt)
        
        # Check if response is valid
        if not response or not response.text:
            print("Warning: Received empty response from Gemini API")
            return []
        
        # Clean the response
        cleaned_json = response.text.strip()
        
        # Remove common markdown formatting
        if cleaned_json.startswith("```json"):
            cleaned_json = cleaned_json[7:]
        if cleaned_json.endswith("```"):
            cleaned_json = cleaned_json[:-3]
        
        cleaned_json = cleaned_json.strip()
        
        # Check if the cleaned response is empty
        if not cleaned_json:
            print("Warning: Empty response after cleaning")
            return []
        
        try:
            errors = json.loads(cleaned_json)
        except json.JSONDecodeError as e:
            if "Invalid \\escape" in str(e):
                print("Warning: Received invalid JSON from API. Attempting to fix backslashes...")
                fixed_json = re.sub(r'(?<!\\)\\(?!["\\/bfnrt])', r'\\\\', cleaned_json)
                try:
                    errors = json.loads(fixed_json)
                    print("Successfully fixed and parsed JSON.")
                except json.JSONDecodeError as e2:
                    print(f"Failed to parse JSON even after fixing backslashes: {e2}")
                    print(f"Original response: {response.text}")
                    return []
            else:
                print(f"JSON parsing error: {e}")
                print(f"Response text: {cleaned_json}")
                return []

        if isinstance(errors, list):
            return errors
        else:
            print(f"Gemini response was not a valid JSON list: {cleaned_json}")
            return []

    except Exception as e:
        print(f"An error occurred while checking code with Gemini: {e}")
        return []