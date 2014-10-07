from numpy import inf
from numpy.linalg import norm
from scipy.sparse.linalg import spsolve


def nr(power_network, tolerance=0.001):
    while error > tolerance:
        A = power_network.generate_jacobian_matrix()
        b = power_network.generate_function_matrix()
        h = spsolve(A, b)
        x = power_network.get_current_voltage_vector()
        x_next = -h + x
        power_network.update_voltage_vector(x_next)
        error = norm(x_next, inf)
    return x_next