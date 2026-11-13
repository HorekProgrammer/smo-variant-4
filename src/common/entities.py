from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RequestStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    EVICTED = "evicted"


@dataclass
class Request:
    id: str
    source_id: int
    generated_at: float
    status: RequestStatus = RequestStatus.CREATED
    queued_at: Optional[float] = None
    queue_order: Optional[int] = None
    started_at: Optional[float] = None
    exited_at: Optional[float] = None

    def mark_queued(self, time: float, order: int) -> None:
        self.status = RequestStatus.QUEUED
        self.queued_at = time
        self.queue_order = order

    def mark_processing(self, time: float) -> None:
        self.status = RequestStatus.PROCESSING
        self.started_at = time

    def mark_completed(self, time: float) -> None:
        self.status = RequestStatus.COMPLETED
        self.exited_at = time

    def mark_evicted(self, time: float) -> None:
        self.status = RequestStatus.EVICTED
        self.exited_at = time

    @property
    def waiting_time(self) -> float:
        end = self.started_at if self.started_at is not None else self.exited_at
        return 0.0 if end is None else end - self.generated_at

    @property
    def service_time(self) -> float:
        if self.started_at is None or self.exited_at is None:
            return 0.0
        return self.exited_at - self.started_at

    def __repr__(self) -> str:
        return self.id

