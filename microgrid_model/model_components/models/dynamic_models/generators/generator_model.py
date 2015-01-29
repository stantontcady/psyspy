from operator import itemgetter
from numpy import append, array, empty, nan

from ..helper_functions import set_initial_conditions, set_parameter_value
from microgrid_model.exceptions import GeneratorModelError


class GeneratorModel(object):
    def __init__(self, arg_values):
        try:
            parameter_defaults = self.parameter_defaults
        except AttributeError:
            print 'No default parameters provided for this model, cannot set model parameters.'
        
        for parameter, default_value in parameter_defaults.iteritems():
            value = arg_values[parameter]
            if value is None:
                value = default_value
            set_parameter_value(self, parameter, value)
        
        for state, _ in self._get_state_indices_sorted_by_index():
            set_initial_conditions(self, state, nan)
            
        self.reference_angle = None
        self.reference_angular_velocity = None
        
        self._save_state_methods('initial_value')
        self._save_state_methods('incremental_model')
        self._save_state_indices_sorted_by_index()

            
    def __repr__(self):
        try:
            return '\n'.join([line for line in self.repr_helper()])
        except AttributeError:
            return 'Basic generator model, no further details known'


    def _save_state_methods(self, method_type):
        # using strictly defined methods from the model takes precedence over inferring them
        try:
            method_names = self.state_methods[('%s_methods' % (method_type))]
        except AttributeError:
            # if methods are not defined, attempt to infer them from the state names
            try:
                state_indices = self.state_indices
                method_names = {}
                for state, _ in state_indices.iteritems():
                    if method_type == 'incremental_model':
                        method_name = '_d%s_dt_model' % state
                    else:
                        method_name = '_%s_%s' % (state, method_type)
                    method_names[state] = method_name

            except AttributeError:
                raise GeneratorModelError('no strictly defined methods or state indices provided, cannot get state methods')
        
        methods = {}
        for state, index in self._get_state_indices_sorted_by_index():
            try:
                methods[state] = getattr(self, '%s' % (method_names[state]))
            except AttributeError:
                raise GeneratorModelError('Could not get method that defines the ' \
                                          'incremental %s state of the %s model' %
                                          (state, self.model_type["full_name"]))

        setattr(self, '%s_methods' % method_type, methods)
        return methods

        
    def _get_initial_value_methods(self):
        try:
            methods = self.initial_value_methods
        except AttributeError:
            methods = self._save_state_methods('initial_value')

        return methods


    def _get_incremental_model_methods(self):
        try:
            methods = self.incremental_model_methods
        except AttributeError:
            methods = self._save_state_methods('incremental_model')

        return methods


    def set_model_parameters(self, parameter_dict):
        parameters_set = []
        for parameter, value in parameter_dict.iteritems():
            if parameter in self.parameter_defaults:
                setattr(self, '%s' % parameter, value)
                parameters_set.append(parameter)
            else:
                print 'Could not set parameter \'%s\' as it is not valid for this model.' % (parameter)
            
        parameters_not_set = []
        for parameter, _ in self.parameter_defaults.iteritems():
            if parameter not in parameters_set:
                parameters_not_set.append(parameter)
        print 'The following parameters remain unchanged: %s' % (', '.join(sorted(parameters_not_set)))
        return self.get_model_parameters()

        
    def get_model_parameters(self):
        parameter_dict = {}
        for parameter, _ in self.parameter_defaults.iteritems():
            parameter_dict[parameter] = getattr(self, '%s' % parameter)
        return parameter_dict
        

    def initialize_states(self, Vpolar, Pnetwork, Qnetwork, overwrite_current_values=True):
        initial_value_methods = self._get_initial_value_methods()

        if overwrite_current_values is not True:
            initial_values = empty(len(self.state_indices))
        
        current_setpoints = self.get_current_setpoints()
        
        for state, index in self._get_state_indices_sorted_by_index():
            method = initial_value_methods[state]
            initial_value = method(Vpolar, Pnetwork=Pnetwork, Qnetwork=Qnetwork, current_setpoints=current_setpoints)
            if overwrite_current_values is not True:
                initial_values[index] = initial_value
            else:
                set_initial_conditions(self, state, initial_value)
            
        
        if overwrite_current_values is True:
            return self.get_current_states()
        else:
            return initial_values
        
    
    def get_current_states(self, as_dictionary=False):
        states = empty(len(self.state_indices))
        for state, index in self._get_state_indices_sorted_by_index():
            try:
                states[index] = getattr(self, state)[-1]
            except AttributeError:
                print 'could not find index for state.'
                states[index] = nan
        if as_dictionary is True:
            return self.parse_state_vector(states, as_dictionary=True)
        else:
            return states


    def get_all_states(self, as_dictionary=False):
        if as_dictionary is False:
            states = ()
        else:
            states = {}
        for state, _ in self._get_state_indices_sorted_by_index():
            if as_dictionary is False:
                states += (getattr(self, state),)
            else:
                states[state] = getattr(self, state)
        
        return states


    def update_states(self, new_states):
        if type(new_states) is not dict:
            new_states = self.parse_state_vector(new_states, as_dictionary=True)
        for state, new_state in new_states.iteritems():
            setattr(self, state, append(getattr(self, state), new_state))
            
        return self.get_current_states()
        

    def get_incremental_states(self, Vpolar, current_states=None, current_setpoints=None, as_dictionary=False):
        incremental_methods = self._get_incremental_model_methods()

        if current_states is None:
            current_states = self.get_current_states()
        if current_setpoints is None:
            current_setpoints = self.get_current_setpoints()

        if as_dictionary is False:
            incremental_states = empty(len(incremental_methods))
        else:
            incremental_states = {}

        for state, index in self._get_state_indices_sorted_by_index():
            method = incremental_methods[state]
            incremental_state = method(Vpolar, current_states=current_states, current_setpoints=current_setpoints)

            if as_dictionary is False:
                incremental_states[index] = incremental_state
            else:
                incremental_states[state] = incremental_state

        return incremental_states
        
    
    def parse_state_vector(self, states, as_dictionary=False):
        if as_dictionary is False:
            return_val = ()
        else:
            return_val = {}
        # sorting according to index (the value in the state_indices dictionary) so they come out in the order expected
        for state, index in self._get_state_indices_sorted_by_index():
            if as_dictionary is False:
                return_val += (states[index],)
            else:
                return_val[state] = states[index]
        
        return return_val
    
    
    def _save_state_indices_sorted_by_index(self):
        try:
            state_indices = sorted(self.state_indices.iteritems(), key=itemgetter(1))
        except AttributeError:
            raise GeneratorModelError('The %s model does not have a state indices dict.' % self.model_type['full_name'])

        setattr(self, 'sorted_state_indices', state_indices)
        return state_indices


    def _get_state_indices_sorted_by_index(self):
        try:
            state_indices = self.sorted_state_indices
        except AttributeError:
            state_indices = self._save_state_indices_sorted_by_index()
        
        return state_indices


    def get_current_setpoints(self, as_dictionary=False):
        setpoints = empty(len(self.setpoint_indices))
        for setpoint, index in self._get_setpoint_indices_sorted_by_index():
            try:
                setpoints[index] = getattr(self, setpoint)[-1]
            except AttributeError:
                print 'could not find index for setpoint "%s".' % setpoint
                setpoints[index] = nan
        if as_dictionary is True:
            return self.parse_setpoint_vector(setpoints, as_dictionary=True)
        else:
            return setpoints
            
            
    def update_setpoints(self, new_setpoints):
        if type(new_setpoints) is not dict:
            new_setpoints = self.parse_state_vector(new_setpoints, as_dictionary=True)
        for setpoint, new_value in new_setpoints.iteritems():
            setattr(self, state, append(getattr(self, setpoint), new_value))
            
        return self.get_current_setpoints()

        
    def parse_setpoint_vector(self, setpoints, as_dictionary=False):
        if as_dictionary is False:
            return_val = ()
        else:
            return_val = {}
        # sorting according to index (the value in the setpoint_indices dictionary) so they come out in the order expected
        for setpoint, index in self._get_setpoint_indices_sorted_by_index():
            if as_dictionary is False:
                return_val += (setpoints[index],)
            else:
                return_val[setpoint] = setpoints[index]
        
        return return_val
        
    
    def shift_initial_torque_angle(self, angle_to_shift):
        if len(self.d) > 1:
            print 'Cannot shift angle, size of angle array is larger than 1'
            return False
        current_angle = self.d[0]
        self.d = array([current_angle - angle_to_shift])
        return self.d[0]


    def _get_setpoint_indices_sorted_by_index(self):
        try:
            return sorted(self.setpoint_indices.iteritems(), key=itemgetter(1))
        except AttributeError:
            raise AttributeError('The %s model does not have a setpoint indices dictionary.' % self.model_type['full_name'])
    

    def set_reference_angle(self, reference_angle):
        self.reference_angle = reference_angle


    def set_reference_angular_velocity(self, reference_angular_velocity):
        self.reference_angular_velocity = reference_angular_velocity


    def get_apparent_power_partial_derivatives(self, Vpolar, d=None):
        if d is None:
            d, _, _ = self.get_current_states()
        dPdV = self._dp_out_d_v_model(Vpolar, d)
        dPdtheta = self._dp_out_d_theta_model(Vpolar, d)
        dQdV = self._dq_out_d_v_model(Vpolar, d)
        dQdtheta = self._dq_out_d_theta_model(Vpolar, d)
        return ([dPdV, dPdtheta, dQdV, dQdtheta], [('P', 'V'),('P','theta'), ('Q', 'V'), ('Q','theta')])


    def get_all_partial_derivatives():
        pass

    
    def get_real_reactive_power_derivatives(self, Vpolar):
            
        generator_model_name = self.model_type['full_name']
        
        try:
            dp_out_d_theta_model = getattr(self, '%s' % ('_dp_out_d_theta_model'))
        except AttributeError:
            raise AttributeError('No dpout/dtheta model specified for %s model' % generator_model_name)
            
        try:
            dp_out_d_v_model = getattr(self, '%s' % ('_dp_out_d_v_model'))
        except AttributeError:
            raise AttributeError('No dpout/dV model specified for %s model' % generator_model_name)
        
        try:
            dq_out_d_theta_model = getattr(self, '%s' % ('_dq_out_d_theta_model'))
        except AttributeError:
            raise AttributeError('No dpout/dtheta model specified for %s model' % generator_model_name)
            
        try:
            dq_out_d_v_model = getattr(self, '%s' % ('_dq_out_d_v_model'))
        except AttributeError:
            raise AttributeError('No dpout/dV model specified for %s model' % generator_model_name)
        
        dp_out_d_theta = dp_out_d_theta_model(Vpolar)
        dp_out_d_v = dp_out_d_v_model(Vpolar)
        dq_out_d_theta = dq_out_d_theta_model(Vpolar)
        dq_out_d_v = dq_out_d_v_model(Vpolar)
        
        return dp_out_d_theta, dp_out_d_v, dq_out_d_theta, dq_out_d_v
    
 