from math import ceil

from numerical_methods import RungeKutta45

class SimulationRoutine(object):
    
    def __init__(self, power_network, simulation_time, system_changes=None, time_step=0.0001, power_flow_tolerance=0.00001):
        
        self.network = power_network
        self.simulation_time = simulation_time
        self.time_step = time_step
        self.num_simulation_steps = int(float(simulation_time)/float(time_step)+1)
        self.power_flow_tolerance = power_flow_tolerance
        
        self.numerical_method = RungeKutta45(time_step)
        
        
        self.system_changes = []        
        if system_changes is not None:
            if type(system_changes) is not list:
                system_changes = [system_changes]

            for system_change in system_changes:
                self.add_system_change(system_change)

                
    def add_system_change(self, system_change):
        if system_change.start_time > (self.simulation_time - self.time_step):
            print 'Cannot add system change, the start time is after end of simulation or in last time step.'
            return False
        
        start_time_time_step_ratio = float(system_change.start_time)/float(self.time_step)

        if int(start_time_time_step_ratio) - start_time_time_step_ratio != 0.0:
            print 'System change %i does not occur at a time instant included in the simulation, it will be activated immediately after the nearest time step, i.e., %f seconds late.' % (system_change.get_change_id(), ceil(start_time_time_step_ratio)*self.time_step - system_change.start_time)
        self.system_changes.append(system_change)
        return True


    def check_system_change_active(self, system_change):
        if (self.current_time >= system_change.start_time) and (self.current_time <= system_change.end_time):
            if system_change.active is False:
                system_change.activate()
                return True
        else:
            if system_change.active is True:
                system_change.deactivate()
                return True
        return False
            
    
    def check_all_system_changes_active(self):
        system_change_toggled = False
        for system_change in self.system_changes:
            if self.check_system_change_active(system_change) is True:
                system_change_toggled = True
        
        return system_change_toggled
            
            
    def run_simulation(self):
        self.current_time = 0
        # solve power flow with slack bus
        # self.network.initialize_dynamic_states()
        dynamic_generator_nodes = self.network.get_dynamic_generator_nodes()
        for k in range(0, self.num_simulation_steps):
            if self.check_all_system_changes_active() is True:
                # this function forces a recomputation of the admittance matrix which may be necessary to account for change
                # TO DO: add field to system change objects to identify if this step is needed for the type of change activated / deactivated
                self.network.save_admittance_matrix()
            self.current_time += self.time_step
            
            for dynamic_generator_node in dynamic_generator_nodes:
                updated_states = self.get_nodal_state_update(dynamic_generator_node)
                dynamic_generator_node.update_states(updated_states)
                
    
    def get_nodal_state_update(self, node):
        return self.numerical_method.get_nodal_state_update(node)
