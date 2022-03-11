'''
Created on Mar 6, 2022

@author: Benedikt Ursprung
'''
from confocal_measure.post_processor.processors import post_processors
from typing import Sequence


class PostProcessorManager:
    
    def __init__(self): 
        self.processors = post_processors
        self.value = 0
        self.values = [1, 2, 3]
        self.ready = False
        
    def get_value(self):
        if self.ready:
            return self.value
        
    def get_values(self):
        if self.ready:
            return self.values      

    def post_process(self,
                     x:Sequence,
                     y:Sequence,
                     post_processor:str='gauss'): 
        post_process = self.processors[post_processor]   
        self.value, self.values = post_process(x, y)
        self.set_ready(True)
        return (self.value, self.values)
                                
    def set_ready(self, ready:bool):
        self.ready = ready
