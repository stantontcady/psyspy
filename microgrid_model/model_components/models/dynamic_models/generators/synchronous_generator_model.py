

from ..dynamic_model import DynamicModel


class SynchronousGeneratorModel(DynamicModel):
    
    def __init__(self, FILL IN):
        set_initial_conditions(self, 'P', P)
        
        DynamicModel.__init__(self, voltage_magnitude_static=False, voltage_angle_static=False)


    def _prepare_for_initial_value_calculation(self):
        # need to emulate a PV bus during initial value
        self.make_voltage_magnitude_static()


    def _prepare_for_dynamic_simulation(self):
        pass