import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from common.buffer import RingBuffer
from common.device import Device
from common.dispatchers import SelectionDispatcher
from common.entities import Request, RequestStatus
from common.source import Source


def request(name: str, source_id: int, time: float) -> Request:
    return Request(name, source_id, time)


class Variant4RulesTest(unittest.TestCase):
    def test_source_interval_is_uniform_and_bounded(self):
        source = Source(1, 2.0, 3.0, random.Random(1))
        for _ in range(20):
            next_time = source.schedule_next(10.0)
            self.assertGreaterEqual(next_time, 12.0)
            self.assertLessEqual(next_time, 13.0)

    def test_full_buffer_evicts_latest_previous_request(self):
        buffer = RingBuffer(3)
        first, second, third = [request(str(i), 1, float(i)) for i in range(3)]
        buffer.put_request(first, 0.0)
        buffer.put_request(second, 1.0)
        buffer.put_request(third, 2.0)
        newcomer = request("new", 2, 3.0)

        victim, index = buffer.replace_latest(newcomer, 3.0)

        self.assertIs(victim, third)
        self.assertEqual(victim.status, RequestStatus.EVICTED)
        self.assertIs(buffer.slots[index], newcomer)

    def test_selection_uses_source_priority_then_lifo_within_source(self):
        buffer = RingBuffer(3)
        low_priority = request("И2.1", 2, 0.0)
        old_high = request("И1.1", 1, 1.0)
        new_high = request("И1.2", 1, 2.0)
        for item in (low_priority, old_high, new_high):
            buffer.put_request(item, item.generated_at)

        self.assertIs(buffer.pop_highest_priority(), new_high)
        self.assertIs(buffer.pop_highest_priority(), old_high)
        self.assertIs(buffer.pop_highest_priority(), low_priority)

    def test_device_selection_moves_pointer_only_after_assignment(self):
        buffer = RingBuffer(1)
        devices = [Device(1, 1.0, random.Random(1)), Device(2, 1.0, random.Random(2))]
        dispatcher = SelectionDispatcher(buffer, devices)
        buffer.put_request(request("И1.1", 1, 0.0), 0.0)

        assigned = dispatcher.assign_next(0.0)

        self.assertEqual(assigned[1].id, 1)
        self.assertEqual(dispatcher.device_pointer, 1)


if __name__ == "__main__":
    unittest.main()

