from itertools import count

from ..node import Node


class DGR(Node):
    _dgr_ids = count(0)

    def __init__(self, V0=None, theta0=None):
        Node.__init__(self, V0, theta0)
        
        self._dgr_id = self._dgr_ids.next() + 1
        
        self._node_type = 'DGR'

