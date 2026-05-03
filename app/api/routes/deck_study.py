from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session

from app.core.config import get_settings
from app.db.database import get_session
from app.deps import templates
from app.models.answer import Answer
from app.models.deck_study_run import DeckStudyRun
from app.models.exercise import Exercise
from app.models.exercise_deck import ExerciseDeck
from app.services import ai_service, deck_study_service

router = APIRouter(prefix="/study", tags=["study"])


@router.get("/decks/{deck_id}/start")
def start_deck_study(deck_id: int, db: Session = Depends(get_session)) -> RedirectResponse:
    try:
        run = deck_study_service.start_run(db, deck_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return RedirectResponse(url=f"/study/runs/{run.id}", status_code=303)


@router.get("/runs/{run_id}", response_class=HTMLResponse)
def deck_study_page(request: Request, run_id: int, db: Session = Depends(get_session)) -> HTMLResponse:
    run = db.get(DeckStudyRun, run_id)
    if not run:
        raise HTTPException(404, "Sessão não encontrada")
    deck = db.get(ExerciseDeck, run.deck_id)
    if not deck:
        raise HTTPException(404, "Deck não encontrado")
    queue = run.queue_ids()
    if run.completed_at or not queue:
        return templates.TemplateResponse(
            request,
            "study/complete.html",
            {"run": run, "deck": deck, "title": "Sessão concluída"},
        )
    ex = db.get(Exercise, queue[0])
    if not ex or ex.deck_id != run.deck_id:
        raise HTTPException(400, "Fila de estudo inválida")
    return templates.TemplateResponse(
        request,
        "study/run.html",
        {
            "run": run,
            "deck": deck,
            "exercise": ex,
            "remaining": len(queue),
            "title": f"Estudando: {deck.title[:120]}" + ("…" if len(deck.title) > 120 else ""),
        },
    )


@router.post("/runs/{run_id}/answer", response_class=HTMLResponse)
async def deck_study_submit(
    request: Request,
    run_id: int,
    db: Session = Depends(get_session),
    exercise_id: int = Form(...),
    user_answer: str = Form(...),
) -> HTMLResponse:
    run = db.get(DeckStudyRun, run_id)
    if not run or run.completed_at:
        raise HTTPException(400, "Sessão inválida ou já encerrada")
    deck = db.get(ExerciseDeck, run.deck_id)
    if not deck:
        raise HTTPException(404, "Deck não encontrado")
    queue = run.queue_ids()
    if not queue:
        raise HTTPException(400, "Fila vazia")
    if exercise_id != queue[0]:
        raise HTTPException(400, "Exercício fora da ordem da sessão")

    ex = db.get(Exercise, exercise_id)
    if not ex or ex.deck_id != run.deck_id:
        raise HTTPException(400, "Exercício não pertence a este deck")

    result, used_ai = await ai_service.evaluate_submitted_answer_with_fallback(
        question=ex.question,
        exercise_type=ex.exercise_type,
        reference_answer=ex.correct_answer,
        user_answer=user_answer,
        exercise_explanation=ex.explanation,
        settings=get_settings(),
    )

    ans = Answer(
        exercise_id=exercise_id,
        user_answer=user_answer.strip(),
        is_correct=result.is_correct,
        feedback=result.feedback,
    )
    db.add(ans)
    deck_study_service.apply_srs(db, exercise_id, result.is_correct)
    new_queue = deck_study_service.advance_queue(queue, result.is_correct)
    deck_study_service.update_run_queue(db, run, new_queue)
    db.refresh(run)

    deck_complete = not new_queue
    return templates.TemplateResponse(
        request,
        "study/_review_fragment.html",
        {
            "run": run,
            "deck": deck,
            "reviewed_question": ex.question,
            "reviewed_type": ex.exercise_type,
            "submitted_answer": ans.user_answer,
            "was_correct": result.is_correct,
            "feedback": result.feedback,
            "reference_answer": ex.correct_answer,
            "used_ai": used_ai,
            "remaining": len(new_queue),
            "deck_complete": deck_complete,
        },
    )


@router.get("/runs/{run_id}/current-card", response_class=HTMLResponse)
def deck_study_current_card(request: Request, run_id: int, db: Session = Depends(get_session)) -> HTMLResponse:
    run = db.get(DeckStudyRun, run_id)
    if not run:
        raise HTTPException(404, "Sessão não encontrada")
    deck = db.get(ExerciseDeck, run.deck_id)
    if not deck:
        raise HTTPException(404, "Deck não encontrado")
    if run.completed_at:
        return templates.TemplateResponse(
            request,
            "study/_done_fragment.html",
            {"run": run, "deck": deck},
        )
    queue = run.queue_ids()
    if not queue:
        return templates.TemplateResponse(
            request,
            "study/_flow_notice.html",
            {
                "notice_title": "Fila desta sessão vazia",
                "notice_body": (
                    "Não há próximo cartão nesta execução. Pode ser aba antiga, sessão já encerrada em outra aba "
                    "ou um estado incomum. Abra de novo a página da sessão ou a lista do deck."
                ),
                "primary_href": f"/study/runs/{run_id}",
                "primary_label": "Abrir página da sessão",
                "secondary_href": f"/exercises?deck_id={deck.id}",
                "secondary_label": "Lista do deck",
            },
        )
    ex = db.get(Exercise, queue[0])
    if not ex or ex.deck_id != run.deck_id:
        return templates.TemplateResponse(
            request,
            "study/_flow_notice.html",
            {
                "notice_title": "Fila inválida",
                "notice_body": "O próximo item da sessão não pôde ser carregado. Volte à página da sessão ou comece um deck novo.",
                "primary_href": f"/study/runs/{run_id}",
                "primary_label": "Abrir página da sessão",
                "secondary_href": f"/exercises?deck_id={deck.id}",
                "secondary_label": "Lista do deck",
            },
        )
    return templates.TemplateResponse(
        request,
        "study/_card_fragment.html",
        {
            "run": run,
            "deck": deck,
            "exercise": ex,
            "remaining": len(queue),
        },
    )


@router.get("/runs/{run_id}/session-complete-panel", response_class=HTMLResponse)
def deck_study_session_complete_panel(request: Request, run_id: int, db: Session = Depends(get_session)) -> HTMLResponse:
    run = db.get(DeckStudyRun, run_id)
    if not run:
        raise HTTPException(404, "Sessão não encontrada")
    deck = db.get(ExerciseDeck, run.deck_id)
    if not deck:
        raise HTTPException(404, "Deck não encontrado")
    if not run.completed_at:
        return templates.TemplateResponse(
            request,
            "study/_flow_notice.html",
            {
                "notice_title": "Ainda não dá para encerrar por aqui",
                "notice_body": (
                    "Este endereço só mostra o resumo final depois que você respondeu o último cartão "
                    "e a sessão foi gravada como concluída. Se você abriu este link por engano ou em outra aba, "
                    "volte à tela de correção (botão «Concluir sessão») ou à página da sessão."
                ),
                "primary_href": f"/study/runs/{run_id}",
                "primary_label": "Abrir sessão do deck",
                "secondary_href": f"/exercises?deck_id={deck.id}",
                "secondary_label": "Lista do deck",
            },
        )
    return templates.TemplateResponse(
        request,
        "study/_done_fragment.html",
        {"run": run, "deck": deck},
    )
