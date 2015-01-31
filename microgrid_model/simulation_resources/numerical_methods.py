

from numpy import inf
from numpy.linalg import cond, norm, solve
from scipy.sparse import csr_matrix, isspmatrix, isspmatrix_csr
from scipy.sparse.linalg import spsolve


class RungeKutta45(object):
    
    def __init__(self, step_size):
        self.step_size = step_size
        
        
    def get_updated_states(self, current_states, incremental_state_method):
        dt = self.step_size
        
        k1 = dt*incremental_state_method(current_states=current_states)
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


class NewtonRhapson(object):
    
    def __init__(self, tolerance):
        self.tolerance = tolerance


    def set_tolerance(self, new_tolerance):
        self.tolerance = new_tolerance
        return self.get_tolerance()


    def get_tolerance(self):
        return self.tolerance
        
    
    def find_roots(self,
                   get_current_states_method,
                   save_updated_states_method,
                   get_jacobian_method,
                   get_function_vector_method):
    
        fx = get_function_vector_method()
        k = 0
        while True:
            J = get_jacobian_method()


            if isspmatrix(J):
                if isspmatrix_csr(J) is False:
                    J = csr_matrix(J)
                if k > 100:
                    condition_number = cond(J.todense())
                h = spsolve(J, fx)
            else:
                if k > 100:
                    condition_number = cond(J)
                h = solve(J, fx)
            
            if k > 100 and condition_number > 50000:
                raise ValueError('system is likely unstable, Jacobian is ill-conditioned: %i' % condition_number)

            x_next = get_current_states_method() - h
            
            save_updated_states_method(x_next)
            fx = get_function_vector_method()
            
            error = norm(fx, inf)
            if error < self.tolerance:
                break
            k += 1
        return x_next, k
