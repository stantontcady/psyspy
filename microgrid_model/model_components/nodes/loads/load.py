from itertools import count

from ..node import Node


class Load(Node):
    _load_ids = count(0)

    def __init__(self, V0=None, theta0=None):
        Node.__init__(self, V0, theta0)
        
        self._load_id = self._load_ids.next() + 1
        
        self._node_type = 'load'