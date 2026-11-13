import heapq
import os
import random
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.buffer import RingBuffer
from common.device import Device
from common.dispatchers import PlacementDispatcher, SelectionDispatcher
from common.source import Source


@dataclass(order=True)
class Event:
    time: float
    type_priority: int
    entity_id: int
    sequence: int
    event_type: str = field(compare=False)


class Model:
    """Discrete-event simulation for queueing-system variant 4."""

    def __init__(
        self,
        buffer_capacity: int,
        sources_params: Sequence[Tuple[float, float]],
        devices_params: Sequence[float],
        seed: Optional[int] = None,
    ):
        if not sources_params:
            raise ValueError("At least one source is required")
        if not devices_params:
            raise ValueError("At least one device is required")

        master_rng = random.Random(seed)
        self.current_time = 0.0
        self.buffer = RingBuffer(buffer_capacity)
        self.sources = [
            Source(i + 1, a, b, random.Random(master_rng.randrange(2**63)))
            for i, (a, b) in enumerate(sources_params)
        ]
        self.devices = [
            Device(i + 1, mu, random.Random(master_rng.randrange(2**63)))
            for i, mu in enumerate(devices_params)
        ]
        self.placement_dispatcher = PlacementDispatcher(self.buffer)
        self.selection_dispatcher = SelectionDispatcher(self.buffer, self.devices)
        self._events: List[Event] = []
        self._event_sequence = 0

        self.total_generated = 0
        self.total_processed = 0
        self.total_rejected = 0
        self.total_waiting_time = 0.0
        self.last_event = "Модель инициализирована"
        self.last_actions: List[str] = []

        for source in self.sources:
            self._schedule("GENERATION", source.id, source.schedule_next(0.0))

    def _schedule(self, event_type: str, entity_id: int, time: float) -> None:
        self._event_sequence += 1
        # At equal times, completions precede generations.
        priority = 0 if event_type == "COMPLETE" else 1
        heapq.heappush(
            self._events,
            Event(time, priority, entity_id, self._event_sequence, event_type),
        )

    def _dispatch(self) -> None:
        while True:
            assigned = self.selection_dispatcher.assign_next(self.current_time)
            if assigned is None:
                return
            request, device, finish_time = assigned
            self._schedule("COMPLETE", device.id, finish_time)
            self.last_actions.append(
                f"{request} -> П{device.id} до t={finish_time:.3f} (Д2Б4, Д2П2)"
            )

    def step(self) -> bool:
        if not self._events:
            return False
        event = heapq.heappop(self._events)
        self.current_time = event.time
        self.last_actions = []

        if event.event_type == "GENERATION":
            source = self.sources[event.entity_id - 1]
            request = source.generate_request(self.current_time)
            self.total_generated += 1
            self._schedule("GENERATION", source.id, source.next_generation_time)
            accepted, evicted = self.placement_dispatcher.accept_request(
                request, self.current_time
            )
            self.last_event = f"Источник И{source.id} создал {request}"
            if accepted:
                self.last_actions.append(f"{request} записана в буфер (Д1ОЗ1)")
            else:
                self.total_rejected += 1
                self.last_actions.append(
                    f"{evicted} вытеснена, {request} записана вместо неё (Д1ОО4)"
                )
        else:
            device = self.devices[event.entity_id - 1]
            request = device.finish_processing(self.current_time)
            self.total_processed += 1
            self.total_waiting_time += request.waiting_time
            self.last_event = f"Прибор П{device.id} завершил {request}"
            self.last_actions.append(f"{request} покинула систему")

        self._dispatch()
        return True

    @property
    def rejection_probability(self) -> float:
        return self.total_rejected / self.total_generated if self.total_generated else 0.0

    def calendar_state(self) -> str:
        ordered = sorted(self._events)
        if not ordered:
            return "пуст"
        labels = [
            f"{event.event_type[:3]}:{event.entity_id}@{event.time:.3f}"
            for event in ordered
        ]
        return ", ".join(labels)

    def state_lines(self) -> List[str]:
        devices = " | ".join(device.state() for device in self.devices)
        sources = " | ".join(
            f"И{s.id}(создано {s.generated_count}, след. {s.next_generation_time:.3f})"
            for s in self.sources
        )
        return [
            f"[t={self.current_time:8.3f}] СОБЫТИЕ: {self.last_event}",
            f"ДЕЙСТВИЯ: {'; '.join(self.last_actions) or 'нет'}",
            f"КАЛЕНДАРЬ: {self.calendar_state()}",
            f"БУФЕР: {self.buffer.state()} ({self.buffer.occupied_count}/{self.buffer.capacity})",
            f"УКАЗАТЕЛИ: УБ={self.buffer.write_pointer + 1} | УП={self.selection_dispatcher.device_pointer + 1}",
            f"ИСТОЧНИКИ: {sources}",
            f"ПРИБОРЫ: {devices}",
            f"СЧЁТЧИКИ: создано={self.total_generated}, обработано={self.total_processed}, "
            f"отказов={self.total_rejected}, Pотк={self.rejection_probability:.4f}",
        ]

    def print_state(self) -> None:
        print("-" * 88)
        print("\n".join(self.state_lines()))

