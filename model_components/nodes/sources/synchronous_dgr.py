from inspect import currentframe, getargvalues, getargspec
from itertools import count
from operator import itemgetter
from math import pi
from numpy import append, array, empty, nan

from model_components import set_initial_conditions, set_parameter_value
from dgr import DGR
from generator_models import GeneratorModel, StructurePreservingModel

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
        
    
    def initialize_states(self, Pnetwork, Qnetwork, V=None, theta=None, overwrite_current_values=True):
        V, theta = self._voltage_helper(V, theta)

        if self.check_for_generator_model() is False:
            raise AttributeError('No model provided for synchronous DGR %i' % self.get_id())
            
        initialize_method = self._check_for_generator_model_method('initialize_states')
        if initialize_method is False:
            raise AttributeError('The %s model does not have a method to initialize its states' % (self.generator_model.model_type['full_name']))
        
        return initialize_method(V, theta, Pnetwork, Qnetwork, overwrite_current_values=overwrite_current_values)
        
    
    def get_current_states(self, as_dictionary=False):
        return self.generator_model.get_current_states(as_dictionary=as_dictionary)


    def get_incremental_states(self, V=None, theta=None, current_states=None, current_setpoints=None, as_dictionary=False):
        V, theta = self._voltage_helper(V, theta)

        if self.check_for_generator_model() is False:
            raise AttributeError('No model provided for synchronous DGR %i' % self.get_id())
        
        incremental_method = self._check_for_generator_model_method('get_incremental_states')
        if incremental_method is False:
            raise AttributeError('The %s model does not have a method to get incremental states' % (self.generator_model.model_type['full_name']))
        
        return incremental_method(V, theta,
                                  current_states=current_states, current_setpoints=current_setpoints,
                                  as_dictionary=as_dictionary)


    def update_states(self, new_states):
        self.generator_model.update_states(new_states)
        
    
    def get_current_setpoints(self, as_dictionary=False):
        return self.generator_model.get_current_setpoints(as_dictionary=as_dictionary)
        
    
    def get_real_reactive_power_output(self):
        model = self.check_for_generator_model()
        if model is False:
            P = nan
            Q = nan
        else:
            V, theta = self.get_current_voltage()
            P = model.p_out_model(V, theta)
            Q = model.q_out_model(V, theta)
        
        return P, Q

        
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
        
    
    def get_real_reactive_power_derivatives(self, V, theta):
        generator_model = self.check_for_generator_model()
        if generator_model is False:
            raise AttributeError('No generator model specified')
            
        generator_model_name = generator_model.model_type['full_name']
        
        dp_out_d_theta_model = self._check_for_generator_model_method('dp_out_d_theta_model')
        if dp_out_d_theta_model is False:
            raise AttributeError('No dpout/dtheta model specified for %s model' % generator_model_name)
            
        dp_out_d_v_model = self._check_for_generator_model_method('dp_out_d_v_model')
        if dp_out_d_v_model is False:
            raise AttributeError('No dpout/dV model specified for %s model' % generator_model_name)
            
        dq_out_d_theta_model = self._check_for_generator_model_method('dq_out_d_theta_model')
        if dq_out_d_theta_model is False:
            raise AttributeError('No dpout/dtheta model specified for %s model' % generator_model_name)
            
        dq_out_d_v_model = self._check_for_generator_model_method('dq_out_d_v_model')
        if dq_out_d_v_model is False:
            raise AttributeError('No dpout/dV model specified for %s model' % generator_model_name)
        
        dp_out_d_theta = dp_out_d_theta_model(V, theta)
        dp_out_d_v = dp_out_d_v_model(V, theta)
        dq_out_d_theta = dq_out_d_theta_model(V, theta)
        dq_out_d_v = dq_out_d_v_model(V, theta)
        
        return dp_out_d_theta, dp_out_d_v, dq_out_d_theta, dq_out_d_v


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
