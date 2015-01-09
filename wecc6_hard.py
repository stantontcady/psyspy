from math import cos, radians, sin
from simulation_resources import NewtonRhapson, RungeKutta45

from matplotlib.pylab import plot, figure, show, ylim
from numpy import arange, array, concatenate, empty, zeros, set_printoptions

from IPython import embed


def incremental_state_method_bus(current_theta, i, j, k):
    '''
    theta is an array of thetas
    i is the bus for which the network flow is being computed
    j and k are the buses to which bus i is connected
    '''
    result = network_flow(current_theta, i, j, k)
    result += U[i]
    result /= D[i]
    return result


def incremental_state_method(current_states=None):
    if current_states is None:
        current_theta = theta
    else:
        current_theta = get_current_theta(omit_first_element=False)

    result = empty(n)
    
    for i in range(0, n):
        j = connected_indices[i][0]
        k = connected_indices[i][1]
        result[i] = incremental_state_method_bus(current_theta, i, j, k)
    return result


def network_flow(current_theta, i, j, k):
    '''
    B is the susceptance matrix
    theta is an array of thetas
    i is the bus for which the network flow is being computed
    j and k are the buses to which bus i is connected
    '''
    global B
    # sign does not math because defnition of B has different sign
    return B[i, j]*sin(current_theta[i] - current_theta[j]) + B[i,k]*sin(current_theta[i] - current_theta[k])
    
    
def get_updated_states(solver):
    global theta
    return solver.get_updated_states(theta, incremental_state_method)


def integrate(theta0, n, tsim, tstep):
    num_steps = int(tsim/tstep)
    theta_array = empty((num_steps, n))
    t_vector = empty(num_steps)
    # theta is a global var
    save_new_theta(theta0)
    t = 0.
    solver = RungeKutta45(step_size=tstep)
    for k in range(0, num_steps):
        theta = get_updated_states(solver)
        theta_array[k, :] = theta
        t_vector[k] = t
        t += tstep
        if t >= 1.0 and t < (1.0 + tstep):
            U[5] = -1.1
    return theta_array, t_vector

        
def find_theta0(n):
    # initial guess is all zeros
    save_new_theta(zeros(n-1))
    # need to find the thetas that satisfy the network constraints
    # that is, given V_i = 1pu for all i, we want to find the voltage angles that satisfy the network constraints for the given power outputs and draws of the generators and loads, respectively
    solver = NewtonRhapson(tolerance=0.001)
    theta0, _ = solver.find_roots(get_current_states_method=get_current_theta,
                                  save_updated_states_method=save_new_theta,
                                  get_jacobian_method=generate_jacobian_matrix,
                                  get_function_vector_method=get_function_vector)
    return theta0


def get_current_theta(omit_first_element=True):
    # using globl var
    global theta
    if omit_first_element is True:
        return theta[1:]
    else:
        return theta


def save_new_theta(new_theta):
    global theta
    theta = concatenate((zeros(1), new_theta))


def get_function_vector():
    global n
    global connected_indices
    m = n - 1
    current_theta = get_current_theta(omit_first_element=False)
    function_vector = zeros(m)
    for i in range(0, m):
        l = i + 1
        j = connected_indices[l][0]
        k = connected_indices[l][1]
        function_vector[i] = network_flow(current_theta, l, j, k) + U[l]
        
    return function_vector
        

def generate_jacobian_matrix():
    
    # global vars
    global theta
    global n
    global B
    global connected_indices
    m = n - 1
    J = zeros((m, m))
    current_theta = get_current_theta(omit_first_element=False)
    for i in range(0, m):
        l = i + 1
        j = connected_indices[l][0]
        k = connected_indices[l][1]
        J[i,i] = B[l,j]*cos(current_theta[l] - current_theta[j]) + B[l,k]*cos(current_theta[l] - current_theta[k])
        if j != 0:
            J[i,j-1] = -1*B[l,j]*cos(current_theta[l] - current_theta[j])
        if k != 0:
            J[i,k-1] = -1*B[l,k]*cos(current_theta[l] - current_theta[k])
    
    return J
    
    
set_printoptions(linewidth=175)
n = 6
tsim = 3
tstep = 0.001

# theta is used as a global var, initialize it to nothing
theta = empty(n)
# generator setpoints and load power draws
U = array([0.716, 1.63, 0.85, -1.0, -1.25, -0.9])
# generator and load first order time constants
D = array([0.0125, 0.00679, 0.00479, 0.00125, 0.000679, 0.000479])
connected_indices = array([[4,5],[4,3],[5,3],[1,2],[1,0],[2,0]])

# susceptance matrix (optimal ordering shouldnt matter here as all buses have same number of incident lines (2))
B = array(
    [[ 13.5301147 ,   0.        ,   0.        ,   0.        ,  -7.01262272,  -6.68449198],
    [  0.        ,  11.68171717,   0.        ,  -7.43494424,  -4.47427293,   0.        ],
    [  0.        ,   0.        ,  10.36447891,  -6.27352572,   0.        ,  -4.37445319],
    [  0.        ,  -7.43494424,  -6.27352572,  13.52946996,   0.        ,   0.        ],
    [ -7.01262272,  -4.47427293,   0.        ,   0.        ,  11.24589565,   0.        ],
    [ -6.68449198,   0.        ,  -4.37445319,   0.        ,   0.        ,  10.80094517]]
)

# theta0 = find_theta0(n)
theta0 = array([radians(9.3), radians(4.7), radians(-2.2), radians(-4), radians(-3.7)])


theta_array, t = integrate(theta0, n, tsim, tstep)

embed()