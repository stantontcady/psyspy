from logging import debug, info, warning
from math import ceil

from numpy import empty

from numerical_methods import RungeKutta45, ForwardEuler

from IPython import embed


class SimulationRoutine(object):
    
    def __init__(self, power_network, simulation_time, model_changes=None, time_step=0.001, power_flow_tolerance=0.0001):
        
        self.network = power_network

        self.network.set_solver_tolerance(power_flow_tolerance)
        self.simulation_time = simulation_time
        self.time_step = time_step
        self.num_simulation_steps = int(float(simulation_time)/float(time_step)) + 1
        self.time_vector = empty(self.num_simulation_steps)
        
        self.numerical_method = RungeKutta45(time_step)
        # self.numerical_method = ForwardEuler(time_step)
        
        self.model_changes = [] 
        if model_changes is not None:
            if type(model_changes) is not list:
                model_changes = [model_changes]

            for model_change in model_changes:
                if model_change.end_time is not None:
                    if model_change.end_time >= simulation_time or model_change.end_time is None:
                        debug('Model change %i does not revert to normal conditions before end of simulation' % (model_change.get_change_id()))
                        continue
                self.add_model_change(model_change)

    def add_model_change(self, model_change):
        if model_change.start_time > (self.simulation_time - self.time_step):
            warning('Cannot add model change %i, the start time is after end of simulation or in last time step.' % (model_change.get_change_id()))
            return False
        
        start_time_time_step_ratio = float(model_change.start_time)/float(self.time_step)

        if int(start_time_time_step_ratio) - start_time_time_step_ratio != 0.0:
            debug('Model change %i does not occur at a time instant included in the simulation, it will be activated immediately after the nearest time step, i.e., %f seconds late.' % (system_change.get_change_id(), ceil(start_time_time_step_ratio)*self.time_step - model_change.start_time))
        self.model_changes.append(model_change)
        return True


    def check_model_change_active(self, model_change):
        admittance_matrix_recompute_required = False
        
        if ((self.current_time >= model_change.start_time) and 
           ((self.current_time <= model_change.end_time) or model_change.end_time is None)):
            if model_change.active is False:
                model_change.activate()
                admittance_matrix_recompute_required = model_change.admittance_matrix_recompute_required()
        else:
            if model_change.active is True:
                model_change.deactivate()
                admittance_matrix_recompute_required = model_change.admittance_matrix_recompute_required()

        return admittance_matrix_recompute_required
            
    
    def check_all_model_changes_active(self):
        admittance_matrix_recompute_required = False
        
        for model_change in self.model_changes:
            if self.check_model_change_active(model_change) is True:
                admittance_matrix_recompute_required = True
        
        return admittance_matrix_recompute_required
            
            
    def run_simulation(self):
        self.current_time = 0
        n = self.network
        
        _ = n.compute_initial_values_for_dynamic_simulation()
        
        n.initialize_dynamic_model_states()
        n.prepare_for_dynamic_simulation()

        reference_bus = n.get_voltage_angle_reference_bus()

        for k in range(0, self.num_simulation_steps):
            self.time_vector[k] = self.current_time
            admittance_matrix_recompute_required = self.check_all_model_changes_active()
            force_static_var_recompute = False

            if admittance_matrix_recompute_required is True:
            #     # this function forces a recomputation of the admittance matrix which may be necessary to account for change
                _, _ = n.save_admittance_matrix()
                force_static_var_recompute = True
            self.current_time += self.time_step
            
            # n.prepare_for_dynamic_state_update(force_static_var_recompute=force_static_var_recompute)

            reference_velocity = reference_bus.get_current_dynamic_angular_velocity()

            # n.save_injected_apparent_power_to_bus_models()
            
            # n.update_dynamic_states(numerical_integration_method=self.numerical_integration_method.get_updated_states)
            
            for bus in n.get_buses_with_dynamic_models():
                if n.is_voltage_angle_reference_bus(bus) is not True:
                    bus.set_reference_dynamic_angular_velocity(reference_velocity)
                
                # bus.save_bus_voltage_polar_to_model()
                
                bus.update_dynamic_states(numerical_integration_method=self.numerical_method.get_updated_states)

            # solve power flow without slack bus, make sure to leave append=True (this is the default option), tolerance=self.power_flow_tolerance
            if k == 0:
                append = False
            else:
                append = True

            _ = n.solve_power_flow(force_static_var_recompute=force_static_var_recompute, append=append)
