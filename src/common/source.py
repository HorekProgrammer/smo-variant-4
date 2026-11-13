import random

from common.entities import Request


class Source:
    """Infinite source with a uniformly distributed generation interval (ИЗ2)."""

    def __init__(self, source_id: int, interval_min: float, interval_max: float, rng=None):
        if interval_min <= 0 or interval_max < interval_min:
            raise ValueError("Expected 0 < interval_min <= interval_max")
        self.id = source_id
        self.interval_min = interval_min
        self.interval_max = interval_max
        self.rng = rng or random.Random()
        self.next_generation_time = 0.0
        self.generated_count = 0

    def schedule_next(self, current_time: float) -> float:
        interval = self.rng.uniform(self.interval_min, self.interval_max)
        self.next_generation_time = current_time + interval
        return self.next_generation_time

    def generate_request(self, current_time: float) -> Request:
        self.generated_count += 1
        request = Request(
            id=f"И{self.id}.{self.generated_count}",
            source_id=self.id,
            generated_at=current_time,
        )
        self.schedule_next(current_time)
        return request

