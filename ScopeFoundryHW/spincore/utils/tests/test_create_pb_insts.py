import numpy as np

from ..pb_instructions import (_create_insts_lengths, _create_pb_insts,
                               create_pb_insts)
from ..printing import print_pb_insts
from ..pulse_blaster_channel import PulseBlasterChannel
from ..short_pulse_feature import has_short_pulses


def generate_pb_channels(t1):
    c0, c1 = 2 ** 0, 2 ** 1
    return [PulseBlasterChannel(c0, [6], [10]), PulseBlasterChannel(c1, [t1, 16], [8, 14])]


def test_create_insts_lengths():
    t1 = 2
    p = 22

    c0, c1 = 2 ** 0, 2 ** 1
    expected_length = np.array([t1,  6-t1,  t1+2,  8-t1,  0,  14, p])
    expected_insts = np.array([0, c1, c0, c1, c0, c1, c1])

    l, i = _create_insts_lengths(generate_pb_channels(t1), p)
    assert bool(np.all(l == expected_length))
    assert bool(np.all(i == expected_insts))


def test__create_pb_insts():
    t1 = 2
    p = 22

    pb_insts = _create_pb_insts(
        *_create_insts_lengths(generate_pb_channels(t1), p))
    expected = [
        (0b000, 0, 0, t1),
        (0b010, 0, 0, 6-t1),
        (0b011, 0, 0, t1+2),
        (0b001, 0, 0, 8-t1),
        (0b010, 0, 0, 14),
        (0b000, 0, 0, p),
    ]
    # print("test__create_pb_insts")
    # print_pb_insts(pb_insts)
    # print_pb_insts(expected)
    for i, e in zip(pb_insts, expected):
        assert i == e


def test_create_pb_insts_cont():
    t1 = 2
    p = 22

    pb_insts = create_pb_insts(generate_pb_channels(t1), p)
    expected = [
        (0b001000000000000000000000, 0, 0, 10),
        (0b010000000000000000000010, 0, 0, 10),
        (0b010000000000000000000011, 0, 0, 10),
        (0b011000000000000000000001, 0, 0, 10),
        (0b000000000000000000000010, 0, 0, 14),
        (0b000000000000000000000000, 6, 0, p),
    ]
    # print_pb_insts(pb_insts)
    # print_pb_insts(expected)
    for i, e in zip(pb_insts, expected):
        assert i == e


def test_create_pb_insts():
    t1 = 2
    p = 22

    pb_insts = create_pb_insts(generate_pb_channels(t1), p, continuous=False)
    expected = [
        (0b001000000000000000000000, 0, 0, 10),
        (0b010000000000000000000010, 0, 0, 10),
        (0b010000000000000000000011, 0, 0, 10),
        (0b011000000000000000000001, 0, 0, 10),
        (0b000000000000000000000010, 0, 0, 14),
        (0b000000000000000000000000, 0, 0, p),
    ]
    # print_pb_insts(pb_insts)
    # print_pb_insts(expected)
    for i, e in zip(pb_insts, expected):
        assert i == e


def test_create_pb_insts_empty():
    pb_insts = create_pb_insts([])
    expected = []
    for i, e in zip(pb_insts, expected):
        assert i == e


def test_has_short_pulses():
    assert has_short_pulses(create_pb_insts(
        generate_pb_channels(0), 20, continuous=False), 2)


def test_has_not_short_pulses():
    assert not has_short_pulses(create_pb_insts(
        [PulseBlasterChannel(2 ** 0, [60], [100]), PulseBlasterChannel(2 ** 1, [300, 16], [400, 14])], 20, continuous=False), 2)
