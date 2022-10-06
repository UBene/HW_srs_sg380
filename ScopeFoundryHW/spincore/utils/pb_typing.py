'''
Created on Sep 29, 2022

@author: Benedikt Ursprung
'''
from typing import Dict, List, Tuple, Union

# PULSE PROGRAM INSTRUCTIONS
Flags = int
# flags is an integer representing the output state of the pulse blaster.
# Generally, flags in its binary representation, the i-th least significant bit,
# tells the (i-1)-th channel to turn high or low.
#
# E.g: flags=5 represents that physical channels 0 and 2 are high and the others low
#     as the binary representation of 5 is 0b000000000000000000000101
# To generate flags that represent channel 12 on use: 2**12
#
# Note XOR (^) arithmetic:
# (2**12) ^ (2**15) -> a flags that represents channels 12 and 15 on.
# (2**12) ^ (2**15) ^ (2**12) -> a flags that represents channels 15 on only.
# Note that (2**15) is equal to (1<<15)

Duration = int  # a multiple of PERIOD = 1/500 MHz
Inst = int  # see enum in spincore.py
InstArgument = int

PBInstruction = Tuple[Flags, Inst, InstArgument, Duration]
PBInstructions = List[PBInstruction]


# PLOTTING
# {channel_name: (x-coordinates,y-coordinates)}
PlotLines = Dict[str, Tuple[List[float], List[int]]]
ChannelsLookUp = Dict[int, str]  # {channel_number: channel_name}
