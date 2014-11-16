

from itertools import count

class SystemChange(object):
    _system_change_ids = count(0)
    
    def __init__(self, start_time, end_time):
        
        self._system_change_id = self._system_change_ids.next() + 1
        
        if end_time is not None and (start_time > end_time):
            raise ValueError('End time of system change cannot come before the start time')
        
        self.start_time = start_time
        self.end_time = end_time
        
        self.enabled = True
        self.active = False
        

    def get_change_type(self):
        return self._change_type
        
    def get_change_id(self):
        return self._system_change_id
