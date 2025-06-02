from fastapi import APIRouter, HTTPException
from schemas.context import (CommentCodeRequest, CommentCodeResponse)
from langchain_groq import ChatGroq
from langchain.prompts import ( ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate)
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaLLM
import os
from dotenv import load_dotenv
import re
load_dotenv()


def clean_code_from_markdown(text):
    # Look for code blocks anywhere in the text
    code_block_pattern = r'```([\w-]*)?(?:\s+)?([\s\S]*?)```'
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    
    # If we found code blocks, return the content of the first one
    if matches:
        # matches will be a list of tuples: [(language, content), ...]
        language, content = matches[0]
        
        # Strip only trailing whitespace and leading/trailing blank lines
        lines = content.rstrip().split('\n')
        
        # Remove leading empty lines
        while lines and not lines[0].strip():
            lines.pop(0)
            
        # Remove trailing empty lines
        while lines and not lines[-1].strip():
            lines.pop()
            
        # Join the lines back together, preserving indentation
        if lines:
            return '\n'.join(lines)
        return ''
    
    # If no code blocks found, return original without trimming leading whitespace
    return text.rstrip()

llm = OllamaLLM(model="qwen2.5-coder:3b")

parser = StrOutputParser()

prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "You are an expert Perl developer generating contextually appropriate code. Output only raw Perl code without any formatting, markdown, or explanations.\n\n"
        "Project Context:\n"
        "- File: {fileName}\n"
        "- Structure: {projectStructure}\n"
        "- Current block: {currentBlock}\n"
        "- Code before cursor:{codePrefix}\n"
        "- Code after cursor:{codeSuffix}\n\n"
        "Available Resources:\n"
        "- Imported modules: {imports}\n"
        "- Used modules: {usedModules}\n"
        "- Defined variables:{variableDefinitions}\n"
        "- Related code structures:{relatedCodeStructures}\n"
        "- Import definitions:{importDefinitions}\n\n"
        "Instructions:\n"
        "1. Generate ONLY executable Perl code that can be inserted directly at the cursor position\n"
        "2. Use existing variables, functions, and modules when appropriate\n"
        "3. Match the project's code style and indentation.Strictly follow indentation\n"
        "4. Do not output markdown code fences, comments, or explanations\n"
        "5. Do not repeat imports already present\n"
        "6. Always generate some functional code even if the request is ambiguous\n"
        "7. If generating a function that exists in related code, use its signature and behavior as reference\n"
        "8. Use the provided context as reference for generating code and strictly follow indentation\n"
        "RESPONSE FORMAT:\n"
        "Only the exact code to insert, using existing indentation from prefix/suffix.Generate code at any cost"
    ),
    HumanMessagePromptTemplate.from_template(
        "User request:\n{question}\n\nGenerate the Perl code snippet."
    ),
])


chain = prompt | llm | parser


# Create the API router for "items"
router = APIRouter()

@router.post("/")
async def generateSuggestion(request: CommentCodeRequest):
    try:
        # Run the chain; passing in all template variables
        result: str = await chain.ainvoke(
            {
                "projectStructure": request.context.projectStructure,
                "fileName": request.context.fileName,
                "codePrefix": request.context.codePrefix,
                "codeSuffix": request.context.codeSuffix,
                "currentBlock": request.context.currentBlock,
                "imports": request.context.imports,
                "usedModules": request.context.usedModules,
                "variableDefinitions": request.context.variableDefinitions,
                "relatedCodeStructures": request.context.relatedCodeStructures,
                "importDefinitions": request.context.importDefinitions,
                "question": request.message,
            }
        )
        print(request.message)

        print(result)

        # Clean the code properly
        result = clean_code_from_markdown(result)
        print (result)
    except Exception as e:
        # Log or handle the error as needed
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {e}")

    # Return as a JSON body with a `code` field
    return CommentCodeResponse(code=result)
    