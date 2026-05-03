from pydantic import BaseModel, Field


class MaterialCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    content: str = Field(min_length=1)
    source_type: str
    difficulty_level: str


class MaterialUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    content: str = Field(min_length=1)
    source_type: str
    difficulty_level: str
