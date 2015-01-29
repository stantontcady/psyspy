from math import cos, radians, sin
from microgrid_model import NewtonRhapson, RungeKutta45

from matplotlib.pylab import plot, figure, show, ylim, xlim, xlabel, ylabel
from numpy import arange, array, concatenate, dot, empty, zeros, set_printoptions, isclose, sum as asum, divide, multiply, apply_along_axis
from numpy import identity, array_equal, arange, zeros, diag, ones, append, amax, amin, argmax, argmin, nonzero, unique, eye, around, dstack, vstack
from numpy.linalg import matrix_power, eigvals

from IPython import embed


def incremental_state_method(current_states):
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


def generate_rc_weight_matrix(A):
    n = A.shape[0]
    # create empty weight matrix
    P = zeros((n,n))
    # compute weights from adjacency matrix
    for i in range(0,n):
        # out degree is column sum plus 1 (assuming self loops)
        Di = 1 + asum(A[:,i])
        # compute inverse of out degree
        iDi = 1/float(Di)
        # diagonal of weight matrix is out degree
        P[i,i] = iDi
        # put the out degree anywhere there is a 1 in the adjency matrix
        for j in range(0,n):
            if A[j,i] == 1:
                P[j,i] = iDi
    return P


def stop_check_max_min(m, d, n, tol, k, diam):
    # m: max, d: min, n: number of nodes, tol: tolerance, k: iteration, diam: graph diameter
    if (amax(m) - amin(d)) < tol and k % diam == 0:
        return True
    else:
        return False


def approximate_ratio_consensus_stop_max_min(A, y0, z0, e=0.00001):
    # print eigvals(A)
    # upper bound on diameter of graph (number of unique eigenvalues of adjacency matrix)
    diam = unique(eigvals(A)).shape[0]
    # number of nodes (only need element 0 of shape -- A is square)
    n = A.shape[0]
    # indexing variable to toggle between k and k+1 (will be toggled by XORing with 1, i.e., s = s ^ 1)
    s = 0
    
    #### allocate and initialize matrices for states
    ### primary states y and z
    ## y is primary numerator state
    # matrix to store y[k] and y[k+1] vectors
    y = empty((n,2))
    # set y[0] to given initial conditions
    y[:,s] = y0
    # matrix to store y[k] over entire simuliaton
    Y = empty((n,1))
    # save y[0] to matrix storing all y[k]
    Y[:,0] = y0
    ## end y
    ## z is primary denominator state
    # matrix to store z[k] and z[k+1] vectors
    z = empty((n,2))
    # set z[0] to given initial conditions
    z[:,s] = z0
    # matrix to store z[k] over entire simulation
    Z = empty((n,1))
    # save z[0] to matrix storing all z[k]
    Z[:,0] = z0
    ## end z
    ## x is the ratio of the primary states, i.e., x[i] = y[i]/z[i]
    # matrix to store x[k] vector (no need to store (k+1)th x's)
    x = empty((n,1))
    # matrix to store x[k] over entire simulation
    X = empty((n,1))
    ## end x
    ### end primary states
    ### max computation
    ## m stores the maximum
    # vector to store max consnesus computation at k and k+1
    m = zeros((n,2))
    # matrix to store max over entire simulation
    M = empty((n,1))
    ### end max
    ### min computation
    ## m stores the maximum
    # vector to store min consnesus computation at k and k+1
    d = zeros((n,2))
    # matrix to store min over entire simulation
    D = empty((n,1))
    ### end min
    #### end state matrix allocation and initialization
    
    for i in range(0,n):
        # initialize ratio state arrays
        X[i] = y[i,s]/z[i,s]
    
    P = generate_rc_weight_matrix(A)

    k = 0
    while True:
        if k % diam == 0:
            for i in range(0,n):
                # reset max consensus to be ratio of current primary states
                m[i,s] = y[i,s]/z[i,s]
                # reset min consensus to be ratio of current primary states
                d[i,s] = y[i,s]/z[i,s]
        for i in range(0,n):
            # local part of RC on primary states
            y[i,s^1] = P[i,i]*y[i,s]
            z[i,s^1] = P[i,i]*z[i,s]
      
            # udpate max and min consensus
            # get indices of nonzero elements in ith row of weight matrix (in-neighbors of i)
            nz_in = nonzero(P[i,:])[0]
            m_tmp = m[:,s]
            m[i,s^1] = amax(m_tmp[nz_in])
            d_tmp = d[:,s]
            d[i,s^1] = amin(d_tmp[nz_in])
            # do for each neighbor (iterate over columns)
            # update remote part of RC for all states
            for j in range(0,n):
                # i and j are neighbors if A_ij is nonzero
                if A[i,j] != 0:
                    # only get value from node j if ratio of ancillary states of node j is larger than 1
                    # do remote part of RC on all states
                    y[i,s^1] += y[j,s]*P[i,j]
                    z[i,s^1] += z[j,s]*P[i,j]
    
        # if stop_check_max(v[:,s],w[:,s],n,e,k):
        if stop_check_max_min(m[:,s],d[:,s],n,e,k,diam):
            for i in range(0,n):
                x[i] = round(y[i,s]/z[i,s],10)
            return [Y,Z,X,k,M,D]
        else:
            k += 1
            for i in range(0,n):
                x[i] = y[i,s]/z[i,s]
            Y = append(Y,array([y[:,s]]).T,axis=1)
            Z = append(Z,array([z[:,s]]).T,axis=1)
            X = append(X,around(x,decimals=6),axis=1)
            M = append(M,around(array([m[:,s]]).T,decimals=6),axis=1)
            D = append(D,around(array([d[:,s]]).T,decimals=6),axis=1)
            # print "max: %f - node: %i, min: %f - node: %i" % (amax(d)-1,argmax(d),amin(d)-1,argmin(d))
        s = s ^ 1


def rc(num_steps, P, y0, z0):
    y = array(y0, copy=True)
    z = array(z0, copy=True)
    for krc in range(0, num_steps):
        y = dot(P, y)
        z = dot(P, z)
    return divide(y, z)


def integrate(theta0, n, tsim, tstep):
    num_steps = int(tsim/tstep)
    theta_array = empty((num_steps, n))
    t_vector = empty(num_steps)
    save_new_theta(theta0)
    t = 0.
    tperturb0 = 0.125
    tperturb1 = 5
    tperturb2 = 10
    # tround = 0.1
    solver = RungeKutta45(step_size=tstep)
    theta_array[0, :] = theta0
    global U, alpha
    # reasonable value of 10 ms per iteration
    rc_iteration_time = 0.005
    Uarray = empty((num_steps, 6))
    r = 1
    # num_rc_steps = 50
    # P = array([
    #     [1/2., 1/3., 0, 0, 0, 0],
    #     [1/2., 1/3., 1/3., 0, 0, 0],
    #     [0, 1/3., 1/3., 1/3., 0, 0],
    #     [0, 0, 1/3., 1/3., 1/3., 0],
    #     [0, 0, 0, 1/3., 1/3., 1/2.],
    #     [0, 0, 0, 0, 1/3., 1/2.]
    # ])
    A = array([[0, 1, 0, 0, 0, 0],
               [1, 0, 1, 0, 0, 0],
               [0, 1, 0, 1, 0, 0],
               [0, 0, 1, 0, 1, 0],
               [0, 0, 0, 1, 0, 1],
               [0, 0, 0, 0, 1, 0]])
    z0 = D
    # store the time that is acceptable for rc to run again (given # of iterations and time per iteration)
    rc_acceptable_time = 0
    for k in range(1, num_steps):
        if t >= rc_acceptable_time and t < (rc_acceptable_time + tstep):
            [Yr, Zr, Xr, krcr, Mr, mr] = approximate_ratio_consensus_stop_max_min(A, U, z0, e=1e-4)
            z0 = Zr[:,-1]
            dUr = multiply(alpha, Xr[0:3, -1])
            U[0:3] += dUr
            rc_acceptable_time = t + krcr*rc_iteration_time
            
            try:
                Y = dstack((Y, Yr))
                Z = dstack((Z, Zr))
                X = dstack((X, Xr))
                M = dstack((M, Mr))
                m = dstack((m, mr))
                krc = vstack((krc, krcr))
            except UnboundLocalError:
                Y = Yr
                Z = Zr
                X = Xr
                M = Mr
                m = mr
                krc = krcr
            r += 1

        theta_array[k, :] = get_updated_states(theta_array[k-1, :], solver)
        t_vector[k] = t
        t += tstep
        if t >= tperturb0 and t < (tperturb0 + tstep):
            U[5] = -1.1
            
        if t >= tperturb1 and t < (tperturb1 + tstep):
            U[4] = -1.5
            
        if t >= tperturb2 and t < (tperturb2 + tstep):
            U[5] = -0.6
            
        Uarray[k, :] = U

    return theta_array, t_vector, Uarray, Y, Z, X, krc, M, m

        
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
tsim = 16
tstep = 0.0005

# theta is used as a global var, initialize it to nothing
theta = empty(n)
# generator setpoints and load power draws
# power balance is 0.046 pu -- should this be accounted for since there's no loss?
U = array([0.716, 1.63, 0.85, -1.0, -1.25, -0.9])
# generator and load first order time constants
D = array([0.0125, 0.00679, 0.00479, 0.00125, 0.000679, 0.000479])
# D = array([0.0125, 0.0125, 0.0125, 0.0125, 0.0125, 0.0125])
D *= 10
alpha = -0.6*D[0:3]
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

theta_array, t, Uarray, _, _, X, krc, _, _ = integrate(theta0, n, tsim, tstep)

gen_load_sum = apply_along_axis(lambda x: (abs(asum(x[0:3])), abs(asum(x[3:]))), axis=1, arr=Uarray)

# print krcz
# figure(1)
# plot(arange(start=1,stop=krc), Y[0,1:krc].T)
# figure(2)
# plot(arange(start=1,stop=krc), Z[:,1:krc].T)
# figure(3)
# plot(arange(start=1,stop=krc), X[:,1:krc].T)
# figure(4)
# plot(arange(start=1,stop=krc), M[:,1:krc].T)
# figure(5)
# plot(arange(start=1,stop=krc), m[:,1:krc].T)

# Uarray[k, :] = U[0:3]
# gen_array[k, :] = asum(U[0:3])
# load_array[k, :] = -1*asum(U[3:])
# figure(6)
# plot(t_vector, Uarray)
figure(1)
plot(t, theta_array)
xlabel('time, t [s]')

figure(2)
plot(t, gen_load_sum, t, Uarray)
xlabel('time, t [s]')

figure(3)
for i in range(0, X.shape[2]):
    xlim(1, krc[i]-1)
    xlabel('iteration, k')
    ylabel('rc ratio')
    plot(arange(start=1,stop=krc[i]), X[:,1:krc[i],i].T)
    
show()

embed()
