from inspect import currentframe, getargvalues, getargspec
from itertools import count
from operator import itemgetter
from math import pi
from numpy import append, array, empty, nan

from dgr import DGR
from ...generator_models import GeneratorModel, StructurePreservingModel
from ...helper_functions import set_initial_conditions, set_parameter_value

from IPython import embed


class SynchronousDGR(DGR):
    
    _synchronous_dgr_ids = count(0)
    
    def __init__(self,
                 model=None,
                 model_type='structure_preserving',
                 V0=None,
                 theta0=None,
                 parameters={},
                 initial_setpoints={}):
                 
        DGR.__init__(self, V0, theta0)
        
        self._synchronous_dgr_id = self._synchronous_dgr_ids.next() + 1
        
        if model is not None:
            # if issubclass(eval(generator.__class__.__name__), DGR) is False:
            #     raise TypeError('Generator must be an instance of the DGR class or a subclass of it')
            pass
        else:
            # concatenate the parameter and initial state dictionaries into one so that they can be passed to the
            # generator model as keyword arguments
            model_kwargs = dict(**parameters)
            model_kwargs.update(initial_setpoints)
        
            if model_type == 'classical':
                self.generator_model = ClassicalModel()
            elif model_type == 'structure_preserving':
                self.generator_model = StructurePreservingModel(**model_kwargs)
            
        self._node_type = 'synchronous_dgr'


    def __repr__(self):
        return '\n'.join([line for line in self.repr_helper()])

    
    def repr_helper(self, simple=False, indent_level_increment=2):
        V, theta = self.get_current_voltage()
        
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


        
    def shift_initial_torque_angle(self, angle_to_shift):
        method = self._check_for_generator_model_method('shift_initial_torque_angle')
        if method is False:
            raise AttributeError('Cannot shift initial torque angle, method for doing so does not exist')
        return method(angle_to_shift)
        
    
    def set_reference_angle(self, reference_angle):
        method = self._check_for_generator_model_method('set_reference_angle')
        if method is False:
            raise AttributeError('Cannot set reference angle, method for doing so does not exist')
        return method(reference_angle)


    def set_reference_angular_velocity(self, reference_angular_velocity):
        method = self._check_for_generator_model_method('set_reference_angular_velocity')
        if method is False:
            raise AttributeError('Cannot set reference angular velocity, method for doing so does not exist')
        return method(reference_angular_velocity)
