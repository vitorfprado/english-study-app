from datetime import datetime

from sqlalchemy import desc
from sqlmodel import Session, select

from app.models.study_session import StudySession


def list_sessions(session: Session) -> list[StudySession]:
    stmt = select(StudySession).order_by(desc(StudySession.created_at))
    return list(session.exec(stmt).all())


def get_session_by_id(session: Session, session_id: int) -> StudySession | None:
    return session.get(StudySession, session_id)


def create_session(session: Session, title: str, notes: str | None, started_at: datetime | None) -> StudySession:
    row = StudySession(
        title=title,
        notes=notes,
        started_at=started_at or datetime.utcnow(),
        finished_at=None,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def finish_session(session: Session, study_session: StudySession) -> StudySession:
    study_session.finished_at = datetime.utcnow()
    session.add(study_session)
    session.commit()
    session.refresh(study_session)
    return study_session
