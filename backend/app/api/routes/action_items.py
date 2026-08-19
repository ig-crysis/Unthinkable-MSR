from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.action_item import STATUS_DONE, STATUS_OPEN, ActionItem
from app.schemas.summary import ActionItemRead, ActionItemUpdate

router = APIRouter(prefix="/api/action-items", tags=["action-items"])


@router.patch("/{action_item_id}", response_model=ActionItemRead)
def update_action_item(
    action_item_id: str,
    payload: ActionItemUpdate,
    db: Session = Depends(get_db),
) -> ActionItem:
    item = db.get(ActionItem, action_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Action item not found.")

    if payload.status is not None:
        if payload.status not in (STATUS_OPEN, STATUS_DONE):
            raise HTTPException(status_code=400, detail=f"status must be '{STATUS_OPEN}' or '{STATUS_DONE}'.")
        item.status = payload.status
    if payload.owner is not None:
        item.owner = payload.owner
    if payload.due_date is not None:
        item.due_date = payload.due_date

    db.commit()
    db.refresh(item)
    return item
