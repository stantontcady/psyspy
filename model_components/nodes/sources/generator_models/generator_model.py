from operator import itemgetter
from numpy import append, empty, nan

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
        
    
    def get_current_states(self, as_dictionary=False):
        states = empty(len(self.state_indicies))
        for state, index in self.state_indicies.iteritems():
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


    def initialize_states(self, initial_values):
        if type(initial_values) is not dict:
            initial_values = self.parse_state_vector(initial_values, as_dictionary=True)
        for state, initial_value in initial_values.iteritems():
            set_initial_conditions(self, state, initial_value)
            
        return self.get_current_states()

    
    def update_states(self, new_states):
        if type(new_states) is not dict:
            new_states = self.parse_state_vector(new_states, as_dictionary=True)
        for state, new_state in new_states.iteritems():
            setattr(self, state, append(getattr(self, state), new_state))
            
        return self.get_current_states()
        
    
    def _get_state_indices_sorted_by_index(self):
        return sorted(self.state_indicies.iteritems(), key=itemgetter(1))
        
    
    def get_incremental_states(self, Pout, as_dictionary=False):
        try:
            state_indices = self.state_indices
        except AttributeError:
            raise AttributeError('No state indices provided, cannot get incremental states')
            
        if as_dictionary is False:
            incremental_states = empty(len(state_indices))
        else:
            incremental_states = {}
            
        for state, index in self._get_state_indices_sorted_by_index():
            try:
                incremental_state_func = getattr(self, '_%s_incremental_model')
            except AttributeError:
                raise AttributeError('Could not get incremental model for %s state' % state)
            
            if as_dictionary is False:
                incremental_states[index] = incremental_state_func()
            else:
                incremental_states[state] = incremental_state_func()

        return incremental_states
 