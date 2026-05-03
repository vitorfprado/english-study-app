from pydantic import BaseModel, Field


class AnswerCreate(BaseModel):
    exercise_id: int
    user_answer: str = Field(min_length=1)
