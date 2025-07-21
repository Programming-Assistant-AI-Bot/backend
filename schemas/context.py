from pydantic import BaseModel
from typing import List, Dict


class ImportDefinition(BaseModel):
    filepath: str
    content: str


class RelatedCodeStructure(BaseModel):
    title: str
    content: str
    path: str
    type: str
    score: float


class ContextPayload(BaseModel):
    codePrefix: str
    codeSuffix: str
    currentBlock: str

    # e.g. { "My::Utils": ["add","multiply"], … }
    imports: Dict[str, List[str]]

    usedModules: List[str]
    variableDefinitions: List[str]
    fileName: str
    projectStructure: str

    # e.g. { "My::Utils": [ImportDefinition, …], … }
    importDefinitions: Dict[str, List[ImportDefinition]]

    relatedCodeStructures: List[RelatedCodeStructure]

class CommentCodeRequest(BaseModel):
    message: str
    context: ContextPayload


class CommentCodeResponse(BaseModel):
    code: str


class CodeCompletionRequest(BaseModel):
    codePrefix: str
    codeSuffix: str
    # e.g. { "My::Utils": ["add","multiply"], … }
    imports: Dict[str, List[str]]

    usedModules: List[str]
    variableDefinitions: List[str]

    # e.g. { "My::Utils": [ImportDefinition, …], … }
    importDefinitions: Dict[str, List[ImportDefinition]]

    relatedCodeStructures: List[RelatedCodeStructure]

    currentBlock: str