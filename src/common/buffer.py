from typing import List, Optional, Tuple

from common.entities import Request


class RingBuffer:
    """Common ring buffer implementing Д1ОЗ1, Д1ОО4 and Д2Б4."""

    def __init__(self, capacity: int):
        if capacity < 1:
            raise ValueError("Buffer capacity must be at least one")
        self.capacity = capacity
        self.slots: List[Optional[Request]] = [None] * capacity
        self.write_pointer = 0
        self._queue_sequence = 0

    @property
    def occupied_count(self) -> int:
        return sum(request is not None for request in self.slots)

    def has_free_slot(self) -> bool:
        return self.occupied_count < self.capacity

    def has_requests(self) -> bool:
        return self.occupied_count > 0

    def _mark_and_store(self, index: int, request: Request, time: float) -> None:
        self._queue_sequence += 1
        request.mark_queued(time, self._queue_sequence)
        self.slots[index] = request
        self.write_pointer = (index + 1) % self.capacity

    def put_request(self, request: Request, time: float) -> int:
        if not self.has_free_slot():
            raise RuntimeError("Cannot insert into a full buffer")
        for offset in range(self.capacity):
            index = (self.write_pointer + offset) % self.capacity
            if self.slots[index] is None:
                self._mark_and_store(index, request, time)
                return index
        raise RuntimeError("Free buffer slot was not found")

    def replace_latest(self, request: Request, time: float) -> Tuple[Request, int]:
        """Evict the request that was most recently put into the full buffer."""
        if self.has_free_slot():
            raise RuntimeError("Replacement is only valid for a full buffer")
        index, victim = max(
            enumerate(self.slots),
            key=lambda pair: pair[1].queue_order if pair[1] is not None else -1,
        )
        assert victim is not None
        victim.mark_evicted(time)
        self._mark_and_store(index, request, time)
        return victim, index

    def pop_highest_priority(self) -> Request:
        """Choose the lowest source id, then the newest request of that source."""
        candidates = [(index, request) for index, request in enumerate(self.slots) if request]
        if not candidates:
            raise RuntimeError("Cannot select from an empty buffer")
        index, request = min(
            candidates,
            key=lambda pair: (pair[1].source_id, -pair[1].queue_order),
        )
        self.slots[index] = None
        return request

    def state(self) -> str:
        return "[" + ", ".join(str(item) if item else "_" for item in self.slots) + "]"


# The reference project calls this object Buffer; retain that convenient API.
Buffer = RingBuffer

