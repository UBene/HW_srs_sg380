from .pb_typing import Flags, PBInstructions


def print_flags_lengths(flags_list, lengths) -> None:
    print("{:<24} ns".format("flags"))
    for flags, length in zip(flags_list, lengths):
        print(f"{flags:024b}", length)


def print_pb_insts(pb_insts: PBInstructions) -> None:
    print("{:<24} inst ns".format("flags"))
    for flags, inst, inst_data, length in pb_insts:
        print(f"{flags:024b} {inst}, {inst_data} {length}")


def print_flags(flags: Flags):
    print(" ".join([f'{i:02}' for i in reversed(range(24))]), 'bitnumber')
    print(" ".join([f'{i:2}' for i in f"{flags:024b}"]), 'bit')
