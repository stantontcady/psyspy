from logging import debug, info, warning
from math import ceil

from numpy import empty

from numerical_methods import RungeKutta45, ForwardEuler
from perturbations import Perturbation

from IPython import embed


class SimulationRoutine(object):
    
    def __init__(self,
                 power_network,
                 simulation_time,
                 controller=None,
                 perturbations=None,
                 time_step=0.001,
                 power_flow_tolerance=0.0001):
        
        self.network = power_network

        self.network.set_solver_tolerance(power_flow_tolerance)
        self.simulation_time = simulation_time
        self.time_step = time_step
        self.num_simulation_steps = int(float(simulation_time)/float(time_step)) + 1
        self.time_vector = empty(self.num_simulation_steps)
        
        self.numerical_method = RungeKutta45(time_step)
        # self.numerical_method = ForwardEuler(time_step)
        
        if controller is not None and isinstance(controller, Controller) is False:
            raise TypeError('controller must be an instance of the Controller class or a subclass thereof')
        else:
            self.controller = controller
        
        self.perturbations = [] 
        if perturbations is not None:
            if type(perturbations) is not list:
                perturbations = [perturbations]

            for perturbation in perturbations:
                if isinstance(perturbation, Perturbation) is False:
                    raise TypeError('perturbations must be an instance of the Perturbation class or a subclass thereof')
                if perturbation.end_time is not None:
                    if perturbation.end_time >= simulation_time or perturbation.end_time is None:
                        debug('Perturbation %i does not revert to normal conditions before end of simulation' % 
                              (perturbation.get_id()))
                        continue
                if perturbation.enabled is True:
                    self.add_perturbation(perturbation)


    def add_perturbation(self, perturbation):
        if perturbation.start_time > (self.simulation_time - self.time_step):
            warning('Cannot add perturbation %i, the start time is after end of simulation or in last time step.' % 
                    (perturbation.get_id()))
            return False
        
        start_time_time_step_ratio = float(perturbation.start_time)/float(self.time_step)

        if int(start_time_time_step_ratio) - start_time_time_step_ratio != 0.0:
            debug('Perturbation %i does not occur at a time instant included in the simulation, ' + \
                  'it will be activated immediately after the nearest time step, i.e., %f seconds late.' % 
                  (system_change.get_change_id(), ceil(start_time_time_step_ratio)*self.time_step - model_change.start_time))
        self.perturbations.append(perturbation)
        return True


    def check_perturbation_active(self, perturbation):
        admittance_matrix_recompute_required = False
        
        t = self.current_time
        dt = self.time_step
        
        if t >= perturbation.start_time and t < (perturbation.start_time + dt):
            if perturbation.active is False:
                perturbation.activate()
                admittance_matrix_recompute_required = perturbation.admittance_matrix_recompute_required()
        elif perturbation.end_time is not None and t >= perturbation.end_time and t < (perturbation.end_time + dt):
            if perturbation.active is True:
                perturbation.deactivate()
                admittance_matrix_recompute_required = perturbation.admittance_matrix_recompute_required()

        return admittance_matrix_recompute_required
            
    
    def check_all_perturbations_active(self):
        admittance_matrix_recompute_required = False
        
        for perturbation in self.perturbations:
            if self.check_perturbation_active(perturbation) is True:
                admittance_matrix_recompute_required = True
        
        return admittance_matrix_recompute_required


    def check_controller_active(self):
        if self.controller is None:
            pass
        else:
            pass
            
            
    def run_simulation(self):
        self.current_time = 0
        n = self.network
        
        n.prepare_for_dynamic_simulation_initial_value_calculation()
        
        _ = n.compute_initial_values_for_dynamic_simulation()
        
        n.initialize_dynamic_model_states()
        n.prepare_for_dynamic_simulation()

        for k in range(0, self.num_simulation_steps):
            self.time_vector[k] = self.current_time
            admittance_matrix_recompute_required = self.check_all_perturbations_active()
            self.check_controller_active()
            
            n.prepare_for_dynamic_state_update()

            n.update_dynamic_states(numerical_integration_method=self.numerical_method.get_updated_states)
            
            n.update_algebraic_states(admittance_matrix_recompute_required=admittance_matrix_recompute_required)

            self.current_time += self.time_step
