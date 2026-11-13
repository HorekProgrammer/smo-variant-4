from typing import List, Optional, Tuple

from common.buffer import RingBuffer
from common.device import Device
from common.entities import Request


class PlacementDispatcher:
    def __init__(self, buffer: RingBuffer):
        self.buffer = buffer

    def accept_request(self, request: Request, time: float) -> Tuple[bool, Optional[Request]]:
        if self.buffer.has_free_slot():
            self.buffer.put_request(request, time)
            return True, None
        victim, _ = self.buffer.replace_latest(request, time)
        return False, victim


class SelectionDispatcher:
    """Selects free devices in a ring (Д2П2)."""

    def __init__(self, buffer: RingBuffer, devices: List[Device]):
        if not devices:
            raise ValueError("At least one device is required")
        self.buffer = buffer
        self.devices = devices
        self.device_pointer = 0

    def find_free_device(self) -> Optional[Device]:
        for offset in range(len(self.devices)):
            index = (self.device_pointer + offset) % len(self.devices)
            if self.devices[index].is_free:
                return self.devices[index]
        return None

    def assign_next(self, current_time: float) -> Optional[Tuple[Request, Device, float]]:
        if not self.buffer.has_requests():
            return None
        device = self.find_free_device()
        if device is None:
            return None
        request = self.buffer.pop_highest_priority()
        finish_time = device.start_processing(request, current_time)
        self.device_pointer = device.id % len(self.devices)
        return request, device, finish_time


# Names used in the reference implementation.
PostDispatcher = PlacementDispatcher
PickDispatcher = SelectionDispatcher

