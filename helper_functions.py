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