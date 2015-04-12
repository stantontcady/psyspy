from logging import debug

from matplotlib.pylab import cm
from numpy import empty, linspace


def set_initial_conditions(obj, state, initial_value=None):
    """
    Helper function set initial conditions for any object.
    """
    if initial_value is None:
        initial_value = 0
    
    initial_state = empty(1, dtype=float)
    initial_state[0] = initial_value

    setattr(obj, '%s' % state, initial_state)


def set_parameter_value(obj, parameter, value):
    if value is None:
        value = 0
    
    setattr(obj, '%s' % parameter, value)


def check_method_exists_and_callable(obj, method_name):
    if hasattr(obj, method_name) is True:
        method = getattr(obj, method_name)
        if hasattr(method, '__call__') is True:
            return method
        else:
            return False
    else:
        return None


def impedance_admittance_wrangler(z=(), y=()):
    if len(z) == 2:
        r = z[0]
        x = z[1]
        impedance_mag_squared = (r**2 + x**2)
        computed_y = (r/impedance_mag_squared, -x/impedance_mag_squared)
    
    if len(z) == 2 and len(y) == 2:
        if round(computed_y[0], 5) != round(y[0], 5):
            debug('Resistance and conductance provided without different values, using conductance.')
        
        if round(computed_y[1], 5) != round(y[1], 5):
            debug('Reactance and susceptance provided without different values, using susceptance.')
        
        # note that we use admittance in all cases, and only tell the user if they differ sufficiently
        return y

    elif len(z) == 2 and len(y) != 2:
        if len(y) != 0:
            debug('Admittance provided does not have two elements, using impedance.')
        return computed_y
    elif len(y) == 2:
        return y

    if len(z) != 0 and len(y) != 0:
        debug('Could not get admittance, defaulting to zero.')
    return (0, 0)


def generate_n_colors(n, cmap):
    if cmap.name == "Greys":
        # limit bottom range of grey color map or it'll just be white and not visible
        min_num = 0.25
    else:
        min_num = 0.0
    colorspace = linspace(min_num, 1.0, n)
    for i in range(0, n):
        rgba = [int(255*ele) for ele in cmap(colorspace[i])]
        rgb = rgba[0:3]
        yield "#{0:02x}{1:02x}{2:02x}".format(*rgb), colorspace[i]
