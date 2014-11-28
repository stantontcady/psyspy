from operator import itemgetter
from numpy import append, array, empty, nan

from model_components import set_initial_conditions, set_parameter_value


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

            
    def __repr__(self):
        try:
            return '\n'.join([line for line in self.repr_helper()])
        except AttributeError:
            return 'Basic generator model, no further details known'

            
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
        

    def initialize_states(self, V, theta, Pnetwork, Qnetwork, overwrite_current_values=True):
        if overwrite_current_values is not True:
            initial_values = empty(len(self.state_indicies))
        
        current_setpoints = self.get_current_setpoints()
        
        for state, index in self._get_state_indices_sorted_by_index():
            try:
                initial_value_func = getattr(self, '_%s_initial_value' % (state))
            except AttributeError:
                raise AttributeError('Could not get method that defines the initial value of the %s state of the %s model' % (state, self.model_type["full_name"].lower()))
                
            if overwrite_current_values is not True:
                initial_values[index] = initial_value_func(V, theta, Pnetwork, Qnetwork, current_setpoints)
            else:
                set_initial_conditions(self, state, initial_value_func(V, theta, Pnetwork, Qnetwork, current_setpoints))
            
        
        if overwrite_current_values is True:
            return self.get_current_states()
        else:
            return initial_values
        
    
    def get_current_states(self, as_dictionary=False):
        states = empty(len(self.state_indicies))
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
        

    def get_incremental_states(self, V, theta, current_states=None, current_setpoints=None, as_dictionary=False):
        try:
            state_indices = self.state_indicies
        except AttributeError:
            raise AttributeError('No state indices provided, cannot get incremental states')
            
        if as_dictionary is False:
            incremental_states = empty(len(state_indices))
        else:
            incremental_states = {}
        
        if current_states is None:
            current_states = self.get_current_states()
        if current_setpoints is None:
            current_setpoints = self.get_current_setpoints()
                    
        for state, index in self._get_state_indices_sorted_by_index():
            try:
                incremental_state_func = getattr(self, '_%s_incremental_model' % (state))
            except AttributeError:
                raise AttributeError('Could not get method that defines the incremental %s state of the %s model' % (state, self.model_type["full_name"]))
            
            if as_dictionary is False:
                incremental_states[index] = incremental_state_func(V, theta, 
                                                                   current_states=current_states,
                                                                   current_setpoints=current_setpoints)
            else:
                incremental_states[state] = incremental_state_func(V, theta, 
                                                                   current_states=current_states,
                                                                   current_setpoints=current_setpoints)

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
        

    def _get_state_indices_sorted_by_index(self):
        try:
            return sorted(self.state_indicies.iteritems(), key=itemgetter(1))
        except AttributeError:
            raise AttributeError('The %s model does not have a state indices dictionary.' % self.model_type['full_name'])
        
    
    def get_current_setpoints(self, as_dictionary=False):
        setpoints = empty(len(self.setpoint_indicies))
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
            return sorted(self.setpoint_indicies.iteritems(), key=itemgetter(1))
        except AttributeError:
            raise AttributeError('The %s model does not have a setpoint indices dictionary.' % self.model_type['full_name'])
    

    def set_reference_angle(self, reference_angle):
        self.reference_angle = reference_angle


    def set_reference_angular_velocity(self, reference_angular_velocity):
        self.reference_angular_velocity = reference_angular_velocity
 