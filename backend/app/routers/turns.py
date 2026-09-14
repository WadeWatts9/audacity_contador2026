from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.game import Game
from app.models.account import Account
from app.models.turn import TurnRecord
from app.schemas.turn import AdvanceTurnRequest, TurnStateResponse
from app.routers.auth import get_admin_user
from app.engine.turn_processor import TurnProcessor
from app.engine.rules_catalog import BOARD_SQUARES
from app.routers.ws import manager

router = APIRouter(prefix="/turns", tags=["turns"])

@router.get("/squares")
async def get_board_squares():
    """Retorna el catálogo completo de las 12 casillas del tablero y sus variantes."""
    return BOARD_SQUARES

@router.post("/advance/{game_code}")
async def advance_turn(
    game_code: str,
    data: AdvanceTurnRequest,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Avanza el turno al siguiente equipo en orden y ejecuta el proceso estricto de inicio de turno:
    1. Liberar depósitos y pagar intereses (E05, plazo fijo)
    2. Pagar bonificaciones diferidas (E01)
    3. Cobrar cuotas y deudas por orden de creación (E02, E14)
    4. Descontar turno perdido o habilitar tirada
    """
    g_res = await db.execute(select(Game).where(Game.code == game_code.upper().strip()))
    game = g_res.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada.")

    if game.status == "finalizada":
        raise HTTPException(status_code=400, detail="La partida está finalizada y el tablero se encuentra fijado.")

    turn_order = game.turn_order or []
    if not turn_order:
        raise HTTPException(status_code=400, detail="El orden de turnos no está configurado.")

    # Avanzar índice de equipo en el orden de juego
    next_order_index = (game.current_team_order_index + 1) % len(turn_order)
    if next_order_index == 0:
        game.current_turn_number += 1  # Nueva ronda completa
    game.current_team_order_index = next_order_index

    active_account_id = turn_order[next_order_index]
    acc_res = await db.execute(select(Account).where(Account.id == active_account_id))
    active_team = acc_res.scalar_one_or_none()
    if not active_team:
        raise HTTPException(status_code=400, detail="Equipo activo no encontrado.")

    # Procesar inicio de turno (pasos 1 a 4)
    start_results = await TurnProcessor.process_turn_start(
        session=db,
        game=game,
        team_account=active_team,
        approver_id=admin_user.id
    )

    # Registrar el turno en el historial
    square_info = None
    if data.square_id:
        for sq in BOARD_SQUARES:
            if sq["id"] == data.square_id:
                square_info = sq
                break

    summary = f"Turno {game.current_turn_number} - {active_team.account_name}."
    if start_results["turn_lost"]:
        summary += f" Pierde el turno por sanción previa. Turnos restantes por cumplir: {active_team.lost_turns}."
    elif data.dice_roll:
        summary += f" Tirada de dado: {data.dice_roll}."
        if square_info:
            summary += f" Casilla {square_info['id']}: {square_info['name']}."

    record = TurnRecord(
        game_id=game.id,
        team_account_id=active_team.id,
        turn_number=game.current_turn_number,
        opportunity_number=active_team.turn_opportunities_count,
        dice_roll=data.dice_roll,
        square_number=data.square_id,
        square_name=square_info["name"] if square_info else None,
        was_turn_lost=1 if start_results["turn_lost"] else 0,
        action_summary=summary,
        details_json={
            "notes": data.notes,
            "events_executed": start_results["events_executed"]
        }
    )
    db.add(record)
    await db.commit()

    # Difundir evento WebSocket a todos los dispositivos
    await manager.broadcast(game.code, "TURN_ADVANCED", {
        "turn_number": game.current_turn_number,
        "team_id": active_team.id,
        "team_name": active_team.account_name,
        "opportunity_number": active_team.turn_opportunities_count,
        "turn_lost": start_results["turn_lost"],
        "dice_roll": data.dice_roll,
        "square_id": data.square_id,
        "square_name": square_info["name"] if square_info else None,
        "events_executed": start_results["events_executed"],
        "balance_available": active_team.balance_available,
        "balance_reserved": active_team.balance_reserved
    })

    return {
        "current_turn_number": game.current_turn_number,
        "active_team": {
            "id": active_team.id,
            "name": active_team.account_name,
            "lost_turns": active_team.lost_turns,
            "turn_lost_this_round": start_results["turn_lost"],
            "can_roll": not start_results["turn_lost"]
        },
        "events_executed": start_results["events_executed"]
    }
