from fastapi import APIRouter
from pydantic import BaseModel
import httpx 
import json 
import re 

router = APIRouter()

class AltCodeRequest(BaseModel):
    code: str

@router.post("/altCode/")
async def get_alternative_code(request: AltCodeRequest):
    selected_code = request.code

    # Construct the prompt for Ollama
    prompt = f"""Given the following Perl code:
```perl
{selected_code}
```
Provide alternative suggestions or improvements for this Perl code. Focus on common Perl best practices, efficiency, or readability.
Respond with one or more distinct code blocks. Each code block should be marked with triple backticks and 'perl' for syntax highlighting (e.g., ```perl
...code...
```).
If you provide multiple suggestions, clearly label each one.""" 

    ollama_api_url = 'http://localhost:11434/api/generate' 
    request_payload = {
        'model': 'perlbot3:latest', 
        'prompt': prompt,
        'stream': True, 
        'options': {
            'temperature': 0.7, # Adjust for creativity (0.0-1.0)
            'num_predict': 500, # Max tokens to generate
        },
    }

    full_response = ''
    
    # Use httpx.AsyncClient for making asynchronous requests
    async with httpx.AsyncClient(timeout=None) as client: # Set timeout to None for long-running streams
        try:
            # Make the streaming POST request to Ollama
            async with client.stream("POST", ollama_api_url, json=request_payload, headers={"Content-Type": "application/json"}) as response:
                response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
                
                async for chunk in response.aiter_bytes():
                    # Ollama sends newline-delimited JSON objects
                    lines = chunk.decode('utf-8').split('\n')
                    for line in lines:
                        if line.strip(): # Ensure line is not empty
                            try:
                                json_data = json.loads(line)
                                if 'response' in json_data:
                                    full_response += json_data['response']
                                if json_data.get('done'):
                                    break # End of stream
                            except json.JSONDecodeError:
                                # Handle incomplete JSON lines or other non-JSON output
                                continue
                
        except httpx.RequestError as exc:
            print(f"An error occurred while requesting {exc.request.url!r}: {exc}")
            return {"alternatives": [{"label": "Error", "code": f"Backend Error: Could not connect to Ollama. {exc}"}]}
        except httpx.HTTPStatusError as exc:
            print(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc.response.text}")
            return {"alternatives": [{"label": "Error", "code": f"Backend Error from Ollama: {exc.response.status_code}. {exc.response.text}"}]}
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return {"alternatives": [{"label": "Error", "code": f"Backend Error: An unexpected error occurred. {e}"}]}

    suggestions = []
    # Regular expression to find Perl code blocks
    code_block_regex = r"```perl\n([\s\S]*?)\n```"
    
    matches = re.findall(code_block_regex, full_response)
    
    if matches:
        for match in matches:
            suggestions.append({"label": "Alternative", "code": match.strip()})
    else:
        # Fallback: If no code blocks are found, return the full response as a single suggestion
        if full_response.strip():
            suggestions.append({"label": "Alternative", "code": full_response.strip()})
        else:
            suggestions.append({"label": "No suggestions", "code": "No specific code suggestions received from AI, or response format was unexpected."})


    final_alternatives = []
    for i, suggestion_data in enumerate(suggestions):
        final_alternatives.append({
            "label": f"Alternative {i+1}", 
            "code": suggestion_data["code"]
        })

    return {"alternatives": final_alternatives}