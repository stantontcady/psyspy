from inspect import currentframe, getargvalues, getargspec
from itertools import count
from operator import itemgetter
from math import pi
from numpy import append, array, empty, nan

from model_components import set_initial_conditions, set_parameter_value
from dgr import DGR
from generator_models import StructurePreservingModel

from IPython import embed

class SynchronousDGR(DGR):
    
    _synchronous_dgr_ids = count(0)
    
    def __init__(self,
                 model='structure_preserving',
                 V0=None,
                 theta0=None,
                 parameters={},
                 initial_states={}):
                 
        DGR.__init__(self, V0, theta0)
        
        self._synchronous_dgr_id = self._synchronous_dgr_ids.next() + 1
        
        # concatenate the parameter and initial state dictionaries into one so that they can be passed to the
        # generator model as keyword arguments
        model_kwargs = dict(**parameters)
        model_kwargs.update(initial_states)
        
        if model == 'classical':
            self.generator_model = ClassicalModel()
        elif model == 'structure_preserving':
            self.generator_model = StructurePreservingModel(**model_kwargs)
            
        self._node_type = 'SynchronousDGR'
        
        self.model_functions =  [
            "set_model_parameters",
            "get_model_parameters",
            "get_current_states",
            "get_all_states",
            "parse_state_vector",
            "initialize_states",
            "update_states",
            "get_incremental_states"]

            
    def __repr__(self):
        return '\n'.join([line for line in self.repr_helper()])

    
    def repr_helper(self, simple=False, indent_level_increment=2):
        V, theta = self.get_current_node_voltage()
        
        object_info = ['<Synchronous DGR #%i>' % (self._synchronous_dgr_id)]
        if simple is False:
            object_info.append('%sCurrent voltage' % (''.rjust(indent_level_increment)))
            object_info.append('%sMagnitude, V: %0.3f pu' % (''.rjust(2*indent_level_increment), V))
            object_info.append('%sAngle, %s : %0.4f rad' % (''.rjust(2*indent_level_increment),
                                                            u'\u03B8'.encode('UTF-8'), theta))
        object_info.extend(['%s%s' % (''.rjust(indent_level_increment), line)
                            for line in self.generator_model.repr_helper(simple=simple,
                                                                         indent_level_increment=indent_level_increment)])
        return object_info
        
    
    def initialize_states(self, V=None, theta=None, overwrite_current_values=True):
        V, theta = self._voltage_helper(V, theta)

        if self._check_for_generator_model() is False:
            raise AttributeError('No model provided for synchronous DGR %i' % self.get_id())
            
        initialize_method = self._check_for_generator_model_method('initialize_states')
        if initialize_method is False:
            raise AttributeError('The %s model does not have a method to initialize its states' % (self.generator_model.model_type['full_name']))
        
        return initialize_method(V, theta, overwrite_current_values=overwrite_current_values)


    def get_incremental_states(self, V=None, theta=None, as_dictionary=False):
        V, theta = self._voltage_helper(V, theta)

        if self._check_for_generator_model() is False:
            raise AttributeError('No model provided for synchronous DGR %i' % self.get_id())
        
        incremental_method = self._check_for_generator_model_method('get_incremental_states')
        if incremental_method is False:
            raise AttributeError('The %s model does not have a method to initialize its states' % (self.generator_model.model_type['full_name']))
        
        return incremental_method(V, theta, as_dictionary=as_dictionary)


    def _check_for_generator_model(self):
        try:
            model = self.generator_model
        except AttributeError:
            return False
        
        return model


    def _check_for_generator_model_method(self, method_name):
        try:
            method = getattr(self.generator_model, method_name)
        except AttributeError:
            return False
        return method

