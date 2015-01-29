from itertools import count

from ..node import Node
from microgrid_model.exceptions import GeneratorModelError, NodeError

class DGR(Node):
    _dgr_ids = count(0)

    def __init__(self, V0=None, theta0=None):
        Node.__init__(self, V0, theta0)
        
        self._dgr_id = self._dgr_ids.next() + 1
        
        self._node_type = 'dgr'


    def get_apparent_power_partial_derivatives(self, Vpolar):
        generator_model = self.check_for_generator_model()
        if generator_model is False:
            raise NodeError('no generator model specified')
            
        partial_derivatives_method = self._check_for_generator_model_method('get_apparent_power_partial_derivatives')
        
        partial_derivatives_values, partial_derivatives_descriptors = generator_model.partial_derivatives_method(Vpolar)
        # there must be at least one partial or this model does not meet the minimum requirements
        if partial_derivatives_method == []:
            raise NodeError('generator model has no apparent partial derivatives defined')
        else:
            return None


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


    def initialize_states(self, Pnetwork, Qnetwork, Vpolar=None, overwrite_current_values=True):
        initialize_states_method = self._get_generator_model_method('initialize_states')
        
        # use passed in V and theta with precedence over getting it internally
        Vpolar = self._polar_voltage_helper(Vpolar)
        
        return initialize_states_method(Vpolar, Pnetwork, Qnetwork, overwrite_current_values=overwrite_current_values)
        
    
    def get_current_states(self, as_dictionary=False):
        return self.generator_model.get_current_states(as_dictionary=as_dictionary)
        

    def update_states(self, new_states):
        update_states_method = self._get_generator_model_method('update_states')
        return update_states_method(new_states)


    def get_incremental_states(self, Vpolar=None, current_states=None, current_setpoints=None, as_dictionary=False):
        incremental_states_method = self._get_generator_model_method('get_incremental_states')
        
        # use passed in V and theta with precedence over getting it internally
        Vpolar = self._polar_voltage_helper(Vpolar)
        
        return incremental_states_method(Vpolar, current_states=current_states, 
                                         current_setpoints=current_setpoints, as_dictionary=as_dictionary)

    
    def get_current_setpoints(self, as_dictionary=False):
        get_current_setpoints_method = self._get_generator_model_method('get_current_setpoints')
        return get_current_setpoints_method(as_dictionary=as_dictionary)


    def update_setpoints(self, new_setpoints):
        update_setpoint_method = self._get_generator_model_method('update_setpoints')
        return update_setpoints(new_setpoints)


    def _get_generator_model_method(self, method_name):
        if self.check_for_generator_model() is False:
            raise GeneratorModelError('No model provided for DGR %i' % self.get_id())
        
        method = self._check_for_generator_model_method(method_name)
        if method is False:
            raise GeneratorModelError('The %s model used for DGR %i does not have a %s method' %
                                      (self.generator_model.model_type['full_name'], self.get_id(), method_name))

        return method


    def get_real_reactive_power_output(self):
        model = self.check_for_generator_model()
        if model is False:
            P = nan
            Q = nan
        else:
            Vpolar = self.get_current_voltage()
            P = model.p_out_model(Vpolar)
            Q = model.q_out_model(Vpolar)
        
        return P, Q

    def get_apparent_power_partial_derivatives(self, Vpolar, d=None):
        pass


    def get_all_partial_derivatives():
        pass


    def get_real_reactive_power_derivatives(self, Vpolar):
        return self.generator_model.get_real_reactive_power_derivatives(Vpolar=Vpolar)