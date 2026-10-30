from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

@dataclass
class Client:
    id: Optional[int]
    name: str
    contact: Optional[str] = None
    notes: str = ""

@dataclass
class Task:
    id: Optional[int]
    title: str
    client_id: Optional[int] = None
    description: str = ""
    status: str = "todo"           # todo | in_progress | done | cancelled
    priority: int = 2              # 1 high, 2 normal, 3 low
    due_date: Optional[date] = None
    planned_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    price_kopecks: Optional[int] = None      # ожидаемая сумма
    hours_estimated: Optional[float] = None
    hours_spent: float = 0.0                 # денормализация, обновляется триггером логики

@dataclass
class Income:
    id: Optional[int]
    date: date
    amount_kopecks: int
    type: str                       # active | passive
    task_id: Optional[int] = None
    description: str = ""

@dataclass
class TimeSession:
    id: Optional[int]
    task_id: int
    start: datetime
    end: Optional[datetime] = None
    note: str = ""