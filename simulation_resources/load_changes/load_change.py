from itertools import count

from ..system_change import SystemChange


class LoadChange(SystemChange):
    _load_change_ids = count(0)
    
    def __init__(self, affected_load, start_time, end_time=None):
        
        # the load change class expects an object of type node, not bus, but it may be possible to extract the node from the bus if there's only one node attached to the bus
        if affected_load.get_node_type() == 'bus':
            connected_loads = affected_load.get_connected_loads()
            if len(connected_loads) == 1:
                # if node passed in is actually a bus but it only has one load, change affected target
                affected_load = connected_loads[0]

        SystemChange.__init__(self, start_time, end_time)
        
        self._load_change_id = self._load_change_ids.next() + 1
        
        self._change_type = 'load_change'
        
        self.affected_load = affected_load
