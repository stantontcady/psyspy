from numpy import empty


def set_initial_conditions(obj, state, initial_value=None):
    """
    Helper function set initial conditions for buses, and models.
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


def impedance_admittance_wrangler(z=(), y=()):
    if len(z) == 2:
        r = z[0]
        x = z[1]
        impedance_mag_squared = (r**2 + x**2)
        computed_y = (r/impedance_mag_squared, -x/impedance_mag_squared)
    
    if len(z) == 2 and len(y) == 2:
        if round(computed_y[0], 5) != round(y[0], 5):
            print 'Resistance and conductance provided without different values, using conductance.'    
        
        if round(computed_y[1], 5) != round(y[1], 5):
            print 'Reactance and susceptance provided without different values, using susceptance.'
        
        # note that we use admittance in all cases, and only tell the user if they differ sufficiently
        return y

    elif len(z) == 2 and len(y) != 2:
        if len(y) != 0:
            print 'Admittance provided does not have two elements, using impedance.'
        return computed_y
    elif len(y) == 2:
        return y

    if len(z) != 0 and len(y) != 0:
        print 'Could not save admittance of line, defaulting to zero.'
    return (0, 0)