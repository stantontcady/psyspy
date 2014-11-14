

from itertools import count

class SystemChange(object):
    _system_change_ids = count(0)
    
    def __init__(self, start_time, end_time):
        
        self._system_change_id = self._system_change_ids.next() + 1
        
        self.enabled = True
        

    def get_change_type(self):
        return self._change_type