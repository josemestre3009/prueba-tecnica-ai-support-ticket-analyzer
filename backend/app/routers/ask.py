from fastapi import APIRouter

from ..ai.service import answer_question
from ..schemas import AskRequest, AskResponse

router = APIRouter()


@router.post("/ask", response_model=AskResponse, summary="Pregunta en lenguaje natural sobre los tickets")
async def ask(request: AskRequest):
    answer = await answer_question(request.question)
    return AskResponse(question=request.question, answer=answer)
