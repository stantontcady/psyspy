

class SimulationRoutine(object):
    
    def __init__(self, power_network, simulation_time, system_changes=None, time_step=0.0001, power_flow_tolerance=0.00001):
        
        self.simulation_time = simulation_time
        
        if system_changes is not None:
            if type(system_changes) is not list:
                system_changes = [system_changes]
            for system_change in system_changes:
                self.add_system_change(system_change)
                
        self.time_step = time_step
        
        self.power_flow_tolerance = power_flow_tolerance

                
    def add_system_change(self, system_change):
        self.system_changes.append(system_change)
