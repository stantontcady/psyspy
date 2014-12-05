

class RungeKutta45(object):
    
    def __init__(self, step_size):
        self.step_size = step_size
        
        
    def get_nodal_state_update(self, node):
        dt = self.step_size
        current_states = node.get_current_states()
        
        k1 = dt*node.get_incremental_states()
        k2 = dt*node.get_incremental_states(current_states=(current_states + 0.5*k1))
        k3 = dt*node.get_incremental_states(current_states=(current_states + 0.5*k2))
        k4 = dt*node.get_incremental_states(current_states=(current_states + k2))
        return current_states + (1/6.)*(k1 + 2*k2 + 2*k3 + k4)
