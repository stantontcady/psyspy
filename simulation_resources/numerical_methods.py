

class RungeKutta45(object):
    
    def __init__(self, step_size):
        self.step_size = step_size
        
        
    def get_updated_states(self, current_states, incremental_state_method):
        dt = self.step_size
        
        k1 = dt*incremental_state_method()
        k2 = dt*incremental_state_method(current_states=(current_states + 0.5*k1))
        k3 = dt*incremental_state_method(current_states=(current_states + 0.5*k2))
        k4 = dt*incremental_state_method(current_states=(current_states + k2))
        return current_states + (1/6.)*(k1 + 2*k2 + 2*k3 + k4)


class ForwardEuler(object):
    
    def __init__(self, step_size):
        self.step_size = step_size
        
    
    def get_updated_states(self, current_states, incremental_state_method):
        dt = self.step_size
        
        return current_states + dt*incremental_state_method()