from pydantic import BaseModel, Field


class ExerciseCreate(BaseModel):
    material_id: int | None = None
    question: str = Field(min_length=1)
    exercise_type: str
    correct_answer: str = Field(min_length=1)
    explanation: str | None = None


class ExerciseAnswerForm(BaseModel):
    exercise_id: int
    user_answer: str = Field(min_length=1)
