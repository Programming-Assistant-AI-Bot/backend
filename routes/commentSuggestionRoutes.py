from fastapi import APIRouter, HTTPException
from schemas.context import (CommentCodeRequest, CommentCodeResponse)
from langchain_groq import ChatGroq
from langchain.prompts import ( ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate)
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv
load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(model="llama-3.3-70b-versatile",groq_api_key=groq_api_key)

parser = StrOutputParser()

prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "You are a Perl programming expert assistant that generates contextually relevant code. "
        "Your task is to generate Perl code that fits seamlessly within the existing codebase. "
        "Consider the following project context when generating code:\n\n"
        "Project Structure:\n{projectStructure}\n\n"
        "Current File: {fileName}\n\n"
        "Code Prefix (code before cursor):\n```perl\n{codePrefix}\n```\n\n"
        "Code Suffix (code after cursor):\n```perl\n{codeSuffix}\n```\n\n"
        "Current Block: {currentBlock}\n\n"
        "Imported Modules: {imports}\n\n"
        "Used Modules: {usedModules}\n\n"
        "Variable Definitions: {variableDefinitions}\n\n"
        "Related Code Structures:\n{relatedCodeStructures}\n\n"
        "Import Definitions:\n{importDefinitions}\n\n"
        "IMPORTANT GUIDELINES:\n"
        "1. Only output raw Perl code (no markdown, no explanations)\n" 
        "2. Ensure code is compatible with the imported modules\n"
        "3. Follow Perl best practices and maintain consistent style with existing code\n"
        "4. Use existing functions and variables when appropriate\n"
        "5. Respect the current block scope\n"
        "6. If implementing a new function, ensure it follows existing patterns\n"
        "7. Consider performance, readability, and maintainability\n"
    ),
    HumanMessagePromptTemplate.from_template(
        "User comment:\n{question}\n\nGenerate appropriate Perl code."
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
    except Exception as e:
        # Log or handle the error as needed
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {e}")

    # Return as a JSON body with a `code` field
    return CommentCodeResponse(code=result)
    