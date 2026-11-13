import random
from typing import Optional

from common.entities import Request


class Device:
    """Service device with an exponentially distributed service time (ПЗ1)."""

    def __init__(self, device_id: int, mu: float, rng=None):
        if mu <= 0:
            raise ValueError("Service rate mu must be positive")
        self.id = device_id
        self.mu = mu
        self.rng = rng or random.Random()
        self.current_request: Optional[Request] = None
        self.finish_time: Optional[float] = None

    @property
    def is_free(self) -> bool:
        return self.current_request is None

    def start_processing(self, request: Request, current_time: float) -> float:
        if not self.is_free:
            raise RuntimeError(f"Device {self.id} is busy")
        request.mark_processing(current_time)
        self.current_request = request
        self.finish_time = current_time + self.rng.expovariate(self.mu)
        return self.finish_time

    def finish_processing(self, current_time: float) -> Request:
        if self.current_request is None:
            raise RuntimeError(f"Device {self.id} is already free")
        request = self.current_request
        request.mark_completed(current_time)
        self.current_request = None
        self.finish_time = None
        return request

    def state(self) -> str:
        if self.is_free:
            return f"П{self.id}(свободен)"
        return f"П{self.id}({self.current_request}, до {self.finish_time:.3f})"

