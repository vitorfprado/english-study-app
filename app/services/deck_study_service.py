import random
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.models.deck_study_run import DeckStudyRun
from app.models.exercise import Exercise
from app.models.exercise_deck import ExerciseDeck
from app.models.exercise_srs import ExerciseSrs


def advance_queue(queue: list[int], correct: bool) -> list[int]:
    """Se errou, recoloca o cartão após ~2 outros (fila curta estilo aprendizado do Anki)."""
    if not queue:
        return []
    current = queue[0]
    rest = queue[1:]
    if correct:
        return rest
    insert_at = min(2, len(rest))
    return rest[:insert_at] + [current] + rest[insert_at:]


def start_run(session: Session, deck_id: int) -> DeckStudyRun:
    deck = session.get(ExerciseDeck, deck_id)
    if not deck:
        raise ValueError("Deck não encontrado")
    stmt = select(Exercise).where(Exercise.deck_id == deck_id)  # type: ignore[arg-type]
    exercises = list(session.exec(stmt).all())
    ids = [e.id for e in exercises if e.id is not None]
    if not ids:
        raise ValueError("Deck sem exercícios")
    random.shuffle(ids)
    run = DeckStudyRun(deck_id=deck_id, queue_ids_json="[]", completed_at=None)
    run.set_queue_ids(ids)
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def apply_srs(session: Session, exercise_id: int, correct: bool) -> None:
    now = datetime.utcnow()
    row = session.get(ExerciseSrs, exercise_id)
    if not row:
        row = ExerciseSrs(
            exercise_id=exercise_id,
            due_at=now,
            interval_days=0.0,
            ease=2.5,
            repetitions=0,
            lapses=0,
            updated_at=now,
        )
    if correct:
        if row.repetitions == 0:
            row.interval_days = 1.0
        elif row.repetitions == 1:
            row.interval_days = 6.0
        else:
            row.interval_days = max(1.0, round(row.interval_days * row.ease, 2))
        row.repetitions += 1
        row.ease = min(3.0, row.ease + 0.05)
        row.due_at = now + timedelta(days=row.interval_days)
    else:
        row.lapses += 1
        row.repetitions = 0
        row.interval_days = 0.0
        row.ease = max(1.3, row.ease - 0.25)
        row.due_at = now
    row.updated_at = now
    session.add(row)


def update_run_queue(session: Session, run: DeckStudyRun, new_queue: list[int]) -> None:
    run.set_queue_ids(new_queue)
    if not new_queue:
        run.completed_at = datetime.utcnow()
    session.add(run)
    session.commit()
    session.refresh(run)
