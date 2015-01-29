from math import cos, radians, sin
from microgrid_model import NewtonRhapson, RungeKutta45

from matplotlib.pylab import plot, figure, show, ylim, xlim
from numpy import arange, array, concatenate, empty, zeros, set_printoptions

from IPython import embed


def incremental_state_method(current_states):
    # if current_states is None:
    #     global theta
    #     current_theta = theta
    #     # this shold never be executed
    #     print "started ffrom the bottom now we here"
    # else:
    #     current_theta = get_current_theta(omit_first_element=False)

    result = empty(n)
    for i in range(0, n):
        j = connected_indices[i][0]
        k = connected_indices[i][1]
        result[i] = incremental_state_method_bus(current_states, i, j, k)
    return result


def incremental_state_method_bus(current_theta, i, j, k):
    '''
    theta is an array of thetas
    i is the bus for which the network flow is being computed
    j and k are the buses to which bus i is connected
    '''
    global U, D, B
    return (U[i] - network_flow(B[i, j], B[i, k], current_theta, i, j, k))/D[i]


def network_flow(Bij, Bik, current_theta, i, j, k):
    '''
    Bij and Bik is the susceptance matrix entries
    current_theta is an array of thetas
    i is the bus for which the network flow is being computed
    j and k are the buses to which bus i is connected
    '''
    # sign does not match because defnition of B has different sign
    return -1*(trig_helper(Bij, current_theta[i], current_theta[j], sin) + 
               trig_helper(Bik, current_theta[i], current_theta[k], sin))


def trig_helper(Bij, theta_i, theta_j, trig_func):
    return Bij*trig_func(theta_i - theta_j)
    
    
def get_updated_states(theta, solver):
    return solver.get_updated_states(theta, incremental_state_method)


def integrate(theta0, n, tsim, tstep):
    num_steps = int(tsim/tstep)
    theta_array = empty((num_steps, n))
    t_vector = empty(num_steps)
    # theta is a global var
    save_new_theta(theta0)
    t = 0.
    tperturb_start = 0.1
    tperturb_end = 0.15
    solver = RungeKutta45(step_size=tstep)
    theta_array[0, :] = theta0
    for k in range(1, num_steps):
        theta_array[k, :] = get_updated_states(theta_array[k-1, :], solver)
        t_vector[k] = t
        t += tstep
        if t >= tperturb_start and t < (tperturb_start + tstep):
            U[5] = -1.1
        #if t >= tperturb_end and t < (tperturb_end + tstep):
        #    U[5] = -0.9
    return theta_array, t_vector

        
def find_theta0(n):
    # initial guess is all zeros
    save_new_theta(zeros(n-1))
    # need to find the thetas that satisfy the network constraints
    # that is, given V_i = 1pu for all i, we want to find the voltage angles that satisfy the network constraints for the given power outputs and draws of the generators and loads, respectively
    solver = NewtonRhapson(tolerance=0.0001)
    theta0, _ = solver.find_roots(get_current_states_method=get_current_theta,
                                  save_updated_states_method=save_new_theta,
                                  get_jacobian_method=generate_jacobian_matrix,
                                  get_function_vector_method=get_function_vector)

    return concatenate((zeros(1), theta0))


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
    global n, connected_indices, U
    current_theta = get_current_theta(omit_first_element=False)
    function_vector = _power_flow_balance(n, current_theta, U)
    return function_vector[1:]
    
def _power_flow_balance(n, theta, U):
    result = zeros(n)
    for i in range(0, n):
        j = connected_indices[i][0]
        k = connected_indices[i][1]
        result[i] = network_flow(B[i, j], B[i, k], theta, i, j, k) - U[i]
    
    return result
    
        

def generate_jacobian_matrix():
    # global vars
    global theta, n, B, connected_indices
    J = zeros((n-1, n-1))
    current_theta = get_current_theta(omit_first_element=False)
    for i in range(1, n):
        j = connected_indices[i][0]
        k = connected_indices[i][1]

        J[i-1, i-1] = -1*(trig_helper(B[i, j], current_theta[i], current_theta[j], cos) +
                          trig_helper(B[i, k], current_theta[i], current_theta[k], cos))
        
        if j != 0:
            J[i-1, j-1] = trig_helper(B[i, j], current_theta[i], current_theta[j], cos)
        if k != 0:
            J[i-1, k-1] = trig_helper(B[i, k], current_theta[i], current_theta[k], cos)
    
    return J
    
def plot_thetas(tsim, t, theta_array):
    xlim(0, tsim)
    plot(t, theta_array)
    show()


set_printoptions(linewidth=175)
n = 6
tsim = 1
tstep = 0.001

# theta is used as a global var, initialize it to nothing
theta = empty(n)
# generator setpoints and load power draws
# power balance is 0.046 pu -- should this be accounted for since there's no loss?
U = array([0.716, 1.63, 0.85, -1.0, -1.25, -0.9])
# generator and load first order time constants
D = array([0.0125, 0.00679, 0.00479, 0.00125, 0.000679, 0.000479])
# D = array([0.0125, 0.0125, 0.0125, 0.0125, 0.0125, 0.0125])
D *= 10
connected_indices = array([[4,5],[4,3],[5,3],[1,2],[1,0],[2,0]])

# susceptance matrix (optimal ordering shouldnt matter here as all buses have same number of incident lines (2))
B = array(
    [[ 13.5301147,   0.        ,   0.        ,   0.        ,  -7.01262272,  -6.68449198],
    [  0.        ,  11.68171717,   0.        ,  -7.43494424,  -4.47427293,   0.        ],
    [  0.        ,   0.        ,  10.36447891,  -6.27352572,   0.        ,  -4.37445319],
    [  0.        ,  -7.43494424,  -6.27352572,  13.52946996,   0.        ,   0.        ],
    [ -7.01262272,  -4.47427293,   0.        ,   0.        ,  11.24589565,   0.        ],
    [ -6.68449198,   0.        ,  -4.37445319,   0.        ,   0.        ,  10.80094517]]
)

theta0 = find_theta0(n)

j = connected_indices[0][0]
k = connected_indices[0][1]
U[0] = network_flow(B[0, j], B[0, k], theta0, 0, j, k)

theta_array, t = integrate(theta0, n, tsim, tstep)


embed()
