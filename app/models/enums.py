from enum import Enum


class SourceType(str, Enum):
    MANUAL_TEXT = "manual_text"
    CLASS_SUMMARY = "class_summary"
    PHRASE = "phrase"
    GRAMMAR_TOPIC = "grammar_topic"
    VOCABULARY = "vocabulary"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ExerciseType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    TRANSLATION = "translation"
    WRITING = "writing"
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
