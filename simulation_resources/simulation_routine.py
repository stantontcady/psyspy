from math import ceil

from numpy import empty

from numerical_methods import RungeKutta45

from IPython import embed


class SimulationRoutine(object):
    
    def __init__(self, power_network, simulation_time, system_changes=None, time_step=0.0001, power_flow_tolerance=0.00001):
        
        self.network = power_network
        self.simulation_time = simulation_time
        self.time_step = time_step
        self.num_simulation_steps = int(float(simulation_time)/float(time_step)) + 1
        self.power_flow_tolerance = power_flow_tolerance
        self.time_vector = empty(self.num_simulation_steps)
        
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
        dynamic_dgr_buses = self.network.get_dynamic_dgr_buses()
        # need to make each bus with a dynamic generator attached act like a PV bus to solve the initial power flow
        for dynamic_dgr_bus in dynamic_dgr_buses:
            # this is easily parallelizable
            dynamic_dgr_bus.make_temporary_pv_bus()
        _ = self.network.solve_power_flow(tolerance=self.power_flow_tolerance, append=False)
        
        # get / set reference bus / generator
        # initialize states for generator of reference bus
        # get reference generator delta
        # to determine if (a) or (b) should be done first, test against steady state power balance
        # a) initialize states for non reference generators (pass reference delta)
        # b) shift initial thetas of all but reference bus
        
        
        # these can be parallelized
        for dynamic_dgr_bus in dynamic_dgr_buses:
            dynamic_dgr_bus.stop_temporary_pv_bus()
            Pnetwork = self.network.compute_real_power_injected_from_network(dynamic_dgr_bus)
            Qnetwork = self.network.compute_reactive_power_injected_from_network(dynamic_dgr_bus)
            dynamic_dgr_bus.dgr.initialize_states(Pnetwork, Qnetwork)
            
            
        # no longer need a slack bus during dynamic simulation
        slack_and_reference_bus_id = self.network.get_slack_bus_id()
        self.network.unset_slack_bus()
        self.network.set_voltage_angle_reference_bus_by_id(slack_and_reference_bus_id)
        
        reference_bus = self.network.get_voltage_angle_reference_bus()
        reference_dgr_states = reference_bus.dgr.get_current_states(as_dictionary=True)
        reference_angle = reference_dgr_states['d']
        self.network.shift_bus_voltage_angles(reference_angle)
        for dynamic_dgr_bus in dynamic_dgr_buses:
            # this is easily parallelizable
            dynamic_dgr_bus.dgr.shift_initial_torque_angle(reference_angle)
            dynamic_dgr_bus.dgr.set_reference_angle(reference_angle)
        

        for k in range(0, self.num_simulation_steps):

            self.time_vector[k] = self.current_time
            if self.check_all_system_changes_active() is True:
            #     # this function forces a recomputation of the admittance matrix which may be necessary to account for change
            #     # TO DO: add field to system change objects to identify if this step is needed for the type of change activated / deactivated
                _, _ = self.network.save_admittance_matrix()
            self.current_time += self.time_step
            
            reference_dgr_states = reference_bus.dgr.get_current_states(as_dictionary=True)
            reference_speed = reference_dgr_states['w']

            # these can be parallelized
            for dynamic_dgr_bus in dynamic_dgr_buses:
                if self.network.is_voltage_angle_reference_bus(dynamic_dgr_bus) is False:
                    dynamic_dgr_bus.dgr.set_reference_angular_velocity(reference_speed)
                    updated_states = self.get_nodal_state_update(dynamic_dgr_bus.dgr)
                    dynamic_dgr_bus.dgr.update_states(updated_states)
                    
            # update reference bus last since the other buses need it's angular speed
            updated_states = self.get_nodal_state_update(reference_bus.dgr)
            reference_bus.dgr.update_states(updated_states)
            
            # embed()

            # solve power flow without slack bus, make sure to leave append=True (this is the default option), tolerance=self.power_flow_tolerance
            _ = self.network.solve_power_flow(tolerance=self.power_flow_tolerance)
                
    
    def get_nodal_state_update(self, node):
        return self.numerical_method.get_nodal_state_update(node)
