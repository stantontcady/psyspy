from itertools import count

from ..node import Node


class DGR(Node):
    _dgr_ids = count(0)

    def __init__(self, V0=None, theta0=None):
        Node.__init__(self, V0, theta0)
        
        self._dgr_id = self._dgr_ids.next() + 1
        
        self._node_type = 'dgr'

    def check_for_generator_model(self):
        try:
            model = self.generator_model
        except AttributeError:
            return False
        
        return model


    def _check_for_generator_model_method(self, method_name):
        try:
            model = self.check_for_generator_model()
            if model is not False:
                method = getattr(model, method_name)
                return method
        except AttributeError:
            pass
        return False