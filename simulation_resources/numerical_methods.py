

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
    

# def rk4(f, x0, simulation_time, , dt = 0.0001):
#     num_steps = int(float(tend)/dt+1)
#     x = empty((num_steps,x0.shape[0]))
#     t_vec = empty(num_steps)
#     x[0,:] = x0
#     t = 0
#     for i in range(0,num_steps-1):
#         t_vec[i] = t
#         k1 = dt*f(x[i,:],t,parameters)
#         k2 = dt*f(x[i,:]+0.5*k1,t,parameters)
#         k3 = dt*f(x[i,:]+0.5*k2,t,parameters)
#         k4 = dt*f(x[i,:]+k2,t,parameters)
#         x[i+1,:] = x[i,:]+(1/6.)*(k1+2*k2+2*k3+k4)
#         t = t + dt
#     t_vec[i+1] = t + dt
#     return [x, t_vec]