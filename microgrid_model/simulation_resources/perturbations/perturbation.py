from logging import debug

from itertools import count

from ...helper_functions import check_method_exists_and_callable


class Perturbation(object):
    _perturbation_ids = count(0)
    
    def __init__(self, start_time, affected_model, end_time=None):
        
        self._perturbation_id = self._perturbation_ids.next() + 1
        
        if end_time is not None and (start_time > end_time):
            raise ValueError('End time of a perturbation cannot come before the start time')
        
        self.start_time = start_time
        self.end_time = end_time
        
        self.enabled = True
        self.active = False
        self.affected_model = affected_model
        
        check_activate_method = check_method_exists_and_callable(self, '_activate')
        if check_activate_method is None or check_activate_method is False:
            debug('Perturbation %i does not have a method for activation it, it will be disabled.' % (self._perturbation_id))
            self.enabled = False
        
        check_deactivate_method = check_method_exists_and_callable(self, '_deactivate')
        if check_deactivate_method is None or check_deactivate_method is False:
            if end_time is not None:
                debug('Perturbation %i does not have a method for deactivation, it will be disabled.' % (self._perturbation_id))
                self.enabled = False
        
                

    def get_perturbation_type(self):
        return self._perturbation_type


    def get_id(self):
        return self._perturbation_id


# may be removed in the future
    def admittance_matrix_recompute_required(self):
        return False


    def activate(self):
        # do not need to try / except here because _activate was checked during initialization of instance
        self._activate()
        self.active = True


    def deactivate(self):
        self._deactivate()
        self.active = False
