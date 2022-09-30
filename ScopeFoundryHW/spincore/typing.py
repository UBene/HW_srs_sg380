'''
Created on Sep 29, 2022

@author: bened
'''
from typing import Dict, List, Tuple

PBInstruction = Tuple[int, int, int, float]
PBInstructions = List[PBInstruction]
PlotLines = Dict[str, Tuple[List[float], List[int]]]  # {channel_name: (x-coordinates,y-coordinates)}
ChannelsLookUp = Dict[int, str]  # {channel_number: channel_name}
