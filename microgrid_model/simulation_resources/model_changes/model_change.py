from logging import debug

from itertools import count


class ModelChange(object):
    _model_change_ids = count(0)
    
    def __init__(self, start_time, affected_model, end_time=None):
        
        self._model_change_id = self._model_change_ids.next() + 1
        
        if end_time is not None and (start_time > end_time):
            raise ValueError('End time of model change cannot come before the start time')
        
        self.start_time = start_time
        self.end_time = end_time
        
        self.enabled = True
        self.active = False
        self.affected_model = affected_model


    def get_change_type(self):
        return self._change_type


    def get_change_id(self):
        return self._model_change_id


# may be removed in the future
    def admittance_matrix_recompute_required(self):
        return False


    def activate(self):
        try:
            self._activate_model_change()
            self.active = True
        except AttributeError:
            debug('Could not activate model change %i, no method for activating it' % self._model_change_id)


    def deactivate(self):
        try:
            self._deactivate_model_change()
            self.active = False
        except AttributeError:
            debug('Could not deactivate model change %i, no method for deactivating it' % self._model_change_id)


    def toggle_change(self):
        if self.enabled is True:
            if self.active is False:
                try:
                    self._activate_model_change()
                    self.active = True
                except AttributeError:
                    debug('Could not activate model change %i, no method for activating it' % self._model_change_id)
                
            else:
                try:
                    self._deactivate_model_change()
                except AttributeError:
                    debug('Could not deactivate model change %i, no method for deactivating it' % self._model_change_id)
                self.active = False
