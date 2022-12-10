from ..printing import print_pb_insts
from ..short_pulse_feature import short_pulse_feature


def test_empty_input() -> None:
    assert short_pulse_feature([]) == []


def test_single_channel() -> None:
    pb_insts = [
        (0b000000000000001000000001, 0, 0, 8),
        (0b000000000000001000000010, 0, 0, 10),
    ]
    expected = [
        (0b100000000000001000000001, 0, 0, 10),
        (0b101000000000001000000010, 0, 0, 10),
    ]
    assert short_pulse_feature(pb_insts) == expected


def test_single_on_off_short_long() -> None:
    pb_insts = [
        (0b000000000000000000000001, 0, 0, 2),
        (0b000000000000000000000000, 0, 0, 8),
        (0b000000000000000000000001, 0, 0, 10),
    ]
    expected = [
        (0b001000000000000000000001, 0, 0, 10),
        (0b101000000000000000000001, 0, 0, 10),
    ]
    assert short_pulse_feature(pb_insts) == expected


def test_single_on_short_off_short() -> None:
    pb_insts = [
        (0b000000000000000000000001, 0, 0, 2),  # 0
        (0b000000000000000000000000, 0, 0, 4),  # 1]
        (0b000000000000000000000001, 0, 0, 10),  # 2
    ]
    expected = [
        (0b001000000000000000000001, 0, 0, 10),  # 0
        (0b101000000000000000000001, 0, 0, 10),  # 1
    ]
    assert short_pulse_feature(pb_insts) == expected


def test_double_on_short_short_short() -> None:
    pb_insts = [
        (0b000000000000000000000001, 0, 0, 2),  # 0
        (0b000000000000000000000010, 0, 0, 4),  #
        (0b000000000000000000000001, 0, 0, 14),  #
    ]
    expected = [
        (0b001000000000000000000001, 0, 0, 10),  # 0
        (0b010000000000000000000010, 0, 0, 10),  #
        (0b000000000000000000000001, 0, 0, 14),  #
    ]
    assert short_pulse_feature(pb_insts) == expected


def test_always_on_with_short_middle() -> None:
    pb_insts = [
        (0b000000000000000000000001, 0, 0, 2),  # 0
        (0b000000000000000000000011, 0, 0, 4),  # 1
        (0b000000000000000000000001, 0, 0, 14),  # 2
    ]
    expected = [
        (0b001000000000000000000001, 0, 0, 10),  # 0
        (0b010000000000000000000011, 0, 0, 10),  # 1
        (0b000000000000000000000001, 0, 0, 14),  # 2
    ]
    assert short_pulse_feature(pb_insts) == expected


def test_always_on_with_short_end() -> None:
    pb_insts = [
        (0b000000000000000000000001, 0, 0, 2),  # 0
        (0b000000000000000000000011, 0, 0, 2),  # 1
    ]
    expected = [
        (0b001000000000000000000001, 0, 0, 10),  # 0
        (0b001000000000000000000011, 0, 0, 10),  # 1
    ]
    assert short_pulse_feature(pb_insts) == expected
