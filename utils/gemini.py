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


# --- Final Updated Function for Precise Error Detection ---
async def get_code_errors(perl_code: str) -> list:
    """
    Sends Perl code to the Gemini API to find errors.
    Includes robust logic to extract and repair JSON from the AI's response.
    """
    prompt = f"""
You are an expert Perl developer. Your task is to analyze the following Perl code and find all possible syntax and logical errors.

CRITICAL INSTRUCTION 1: For each error you find, you MUST return both a code_chunk (about 10 words) that contains the error, and the specific error_token (the exact word/symbol that is wrong). The code_chunk must be an EXACT copy from the source code.

CRITICAL INSTRUCTION 2: Your entire response must be a single JSON array, enclosed in a markdown code block like this: json ... .

CRITICAL INSTRUCTION 3: Inside the JSON, all backslash characters \\ within any string MUST be properly escaped as \\\\.

For each error, provide the information in a JSON array format.
Each object must have these keys: "code_chunk", "error_token", and "message".

--- EXAMPLE ---
Code:
`my $user = "guest";
if ($user == "admin") {{
    print "Welcome admin!";
}}`

Response:
json
[
  {{
    "code_chunk": "if ($user == \\"admin\\")",
    "error_token": "==",
    "message": "Logical Error: Using numeric equality `==` on strings. For string comparison, you should use `eq`."
  }}
]


If you find no errors, you MUST return an empty array: [].

Here is the Perl code:

perl
{perl_code}

"""

    try:
        response = await model.generate_content_async(prompt)
        raw_text = response.text
        
        # Step 1: Find the JSON block in the response.
        match = re.search(r'```json\s*([\s\S]*?)\s*```', raw_text)
        
        if not match:
            print(f"Warning: No valid JSON markdown block found in the API response. Full response: {raw_text}")
            return []

        json_string = match.group(1)
        
        # Step 2: Try to parse the block, with a fallback to fix backslashes.
        try:
            # First attempt to parse the extracted JSON.
            errors = json.loads(json_string)
        except json.JSONDecodeError as e:
            # If it fails due to an escape error, try to fix it.
            if "Invalid \\escape" in str(e):
                print("Warning: Extracted JSON has invalid backslashes. Attempting to fix...")
                # This regex replaces single backslashes with double backslashes.
                fixed_json_string = re.sub(r'(?<!\\)\\(?!["\\/bfnrt])', r'\\\\', json_string)
                try:
                    # Retry parsing with the fixed string.
                    errors = json.loads(fixed_json_string)
                    print("Successfully fixed and parsed JSON.")
                except json.JSONDecodeError as e2:
                    # If it still fails, we give up.
                    print(f"Failed to parse JSON even after fixing backslashes: {e2}")
                    print(f"Original (extracted) string was: {json_string}")
                    return []
            else:
                # It's a different, more serious JSON error.
                print(f"Failed to parse extracted JSON: {e}")
                print(f"Extracted string was: {json_string}")
                return []

        if isinstance(errors, list):
            print(f"Backend Info: Received {len(errors)} errors from the Gemini API.")
            return errors
        else:
            print(f"Gemini response was not a valid JSON list: {json_string}")
            return []

    except Exception as e:
        print(f"An error occurred while checking code with Gemini: {e}")
        return []