from itertools import count
from operator import itemgetter
from os.path import join as path_join
from math import sin, cos

from joblib import Parallel, delayed
from networkx import Graph
from numpy import append, array, zeros, frompyfunc, set_printoptions, inf, hstack, empty
from numpy.linalg import norm, cond
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
try:
    from prettytable import PrettyTable
except ImportError:
    print_table_enabled = False

from ..exceptions import PowerNetworkError
from buses import Bus
from power_line import PowerLine
from power_network_helper_functions import fp_fq_helper, connected_bus_helper, jacobian_hij_helper, jacobian_nij_helper, \
                                           jacobian_kij_helper, jacobian_lij_helper, jacobian_diagonal_helper, \
                                           compute_apparent_power_injected_from_network, compute_jacobian_row_by_bus
from ..simulation_resources import NewtonRhapson
from IPython import embed

class PowerNetwork(object):
    
    def __init__(self, buses=[], power_lines=[], solver_tolerance=0.00001):
        self.graph_model = Graph()
        self.buses = []
        for bus in buses:
            self.add_bus(bus)

        for power_line in power_lines:
            if isinstance(power_line, PowerLine) is False:
                raise TypeError('power lines must be a list of instances of PowerLine type or a subclass thereof')

        self.power_lines = []
        self.power_lines.extend(power_lines)

        set_printoptions(linewidth=175)
        self.solver = NewtonRhapson(tolerance=solver_tolerance)

        
    def __repr__(self):
        output = ''
        for bus in self.buses:
            output += bus.repr_helper(simple=True, indent_level_increment=2)
        for power_line in self.power_lines:
            output += power_line.repr_helper(simple=True, indent_level_increment=2)
        return output


    def __iter__(self):
        return iter(self.buses)


    def __len__(self):
        return len(self.buses)


    def __contains__(self, obj):
        if isinstance(obj, Bus):
            try:
                return obj in self.buses
            except AttributeError:
                pass
        elif isinstance(obj, PowerLine):
            try:
                return obj in self.power_lines
            except AttributeError:
                pass
        
        return False


    def get_buses(self):
        """
        A trivial function to return the bus list. Added to match similar functions for getting generator and load buses.
        """
        return self


    def get_generator_buses(self):
        """
        Returns a list of buses that have generator models.
        """
        return [bus for bus in self if bus.has_generator_model() is True]


    def get_load_buses(self):
        """
        Returns a list of buses that have load models.
        """
        return [bus for bus in self if bus.has_load_model() is True]
        

    def get_other_buses(self):
        """
        Returns a list of buses that have neither a generator nor a load model.
        """
        return list(set(self.get_buses()) - set(self.get_generators()) - set(self.get_loads()))


    def set_solver_tolerance(self, new_tolerance):
        return self.solver.set_tolerance(new_tolerance)


    def get_number_of_buses(self):
        return len(self.buses)


    def get_number_of_power_lines(self):
        return len(self.power_lines)


    def add_bus(self, bus, is_slack_bus=False):
        if isinstance(bus, Bus) is False:
            raise TypeError('buses must be a list of instances of Bus type or a subclass thereof')
        else:
            if self.bus_in_network(bus) is False:
                bus.set_get_apparent_power_injected_from_network_method(self.compute_apparent_power_injected_from_network)
                bus.set_get_connected_bus_admittance_from_network_method(self._get_connected_bus_admittances_by_bus_id)
                bus.set_get_connected_bus_polar_voltage_from_network_method(self._get_connected_bus_polar_voltage_by_bus_id)
                self.buses.append(bus)
                # need to regenerate this mapping each time a new bus is added
                self.generate_buses_index_bus_id_mapping()
                if is_slack_bus is not False:
                    current_slack_bus = self.get_slack_bus()
                    if current_slack_bus is not None:
                        debug("changing slack bus from bus with id %i" % current_slack_bus)
                    self.set_slack_bus(bus)
                    
            return bus.get_id()


    def add_power_line(self, power_line):
        self.power_lines.append(power_line)


    def connect_buses(self, bus_a, bus_b, z=(), y=()):
        _ = self.add_bus(bus_a)
        _ = self.add_bus(bus_b)
        
        power_line = PowerLine(bus_a, bus_b, z, y)
        self.add_power_line(power_line)
        return power_line


    def generate_buses_index_bus_id_mapping(self):
        mapping = []
        for bus in self.buses:
            mapping.append(bus.get_id())
        self.buses_index_bus_id_mapping = mapping
        return mapping


    def get_buses_index_bus_id_mapping(self):
        try:
            mapping = self.buses_index_bus_id_mapping
        except AttributeError:
            mapping = self.generate_buses_index_bus_id_mapping()
        return mapping

    
    def get_bus_by_id(self, bus_id):
        buses_index_bus_id_mapping = self.get_buses_index_bus_id_mapping()
        try:
            index_of_bus = buses_index_bus_id_mapping.index(bus_id)
            return self.buses[index_of_bus]
        except ValueError:
            return None


    def get_bus_by_name(self, bus_name):
        for bus in self:
            if bus.name is not None and bus.name == bus_name:
                return bus
            
        return None

    
    def get_bus_type_by_id(self, bus_id):
        bus = self.get_bus_by_id(bus_id)
        if bus is None:
            return None

        return bus.get_node_type()


    def bus_in_network(self, bus):
        if self.get_bus_by_id(bus.get_id()) is None:
            return False
        else:
            return True


    def get_bus_ids_ordered_by_incidence_count(self):
        bus_info = {}
        for power_line in self.power_lines:
            for bus in [power_line.bus_a, power_line.bus_b]:
                try:
                    bus_info['%i' % bus.get_id()] = (bus.get_id(), bus_info['%i' % bus.get_id()][1] + 1)
                except KeyError:
                    bus_info['%i' % bus.get_id()] = (bus.get_id(), 1)
        
        return [bus_tuple[0] for bus_tuple in sorted([value for _, value in bus_info.iteritems()], key=itemgetter(1, 0))]

        
    def get_power_line_by_id(self, power_line_id):
        for power_line in self.power_lines:
            if power_line.get_id() == power_line_id:
                return power_line
    
        return None

        
    def power_line_in_network(self, power_line):
        if self.get_power_line_by_id(power_line.get_id()) is None:
            return False
        else:
            return True

            
    def get_connected_bus_id(self, bus, power_line):
        return self.get_connected_bus_id_by_bus_id(bus.get_id(), power_line)
            
    
    def get_connected_bus_id_by_bus_id(self, bus_id, power_line):
        if power_line.bus_a.get_id() == bus_id:
            return power_line.bus_b.get_id()
        elif power_line.bus_b.get_id() == bus_id:
            return power_line.bus_a.get_id()
        else:
            return None


    def get_connected_bus_id_by_ids(self, bus_id, power_line_id):
        return get_connected_bus_id(self.get_bus_by_id(bus_id), self.get_power_line_by_id(power_line_id))
            

    def get_all_connected_bus_ids_by_id(self, bus_id):
        _, connected_bus_ids = self.get_incident_power_line_ids_and_connected_bus_ids_by_id(bus_id)
        return connected_bus_ids

    
    def get_incident_power_line_ids_by_id(self, bus_id):
        power_line_ids, _ = self.get_incident_power_line_ids_and_connected_bus_ids_by_id(bus_id)
        return power_line_ids

        
    def get_incident_power_line_ids_and_connected_bus_ids_by_id(self, bus_id):
        power_line_ids = []
        connected_bus_ids = []
        for power_line in self.power_lines:
            connected_bus_id = self.get_connected_bus_id_by_bus_id(bus_id, power_line)
            if connected_bus_id is not None:
                connected_bus_ids.append(connected_bus_id)
                power_line_ids.append(power_line.get_id())
        return power_line_ids, connected_bus_ids


    def _get_connected_bus_admittances_by_bus_id(self, bus_id, include_bus_ids=False):
        connected_bus_ids = self.get_all_connected_bus_ids_by_id(bus_id)
        interconnection_admittance = []
        for connected_bus_id in connected_bus_ids:
            Yij = self.get_admittance_value_from_bus_ids(bus_id, connected_bus_id)
            interconnection_admittance.append(Yij)
            
        if include_bus_ids is True:
            return interconnection_admittance, connected_bus_ids
        else:
            return interconnection_admittance


    def _get_connected_bus_polar_voltage_by_bus_id(self, bus_id, include_bus_ids=False):
        connected_bus_ids = self.get_all_connected_bus_ids_by_id(bus_id)
        polar_voltages = []
        for connected_bus_id in connected_bus_ids:
            Vpolar = self.get_bus_by_id(connected_bus_id).get_current_voltage_polar()
            polar_voltages.append(Vpolar)
            
        if include_bus_ids is True:
            return polar_voltages, connected_bus_ids
        else:
            return polar_voltages


    def generate_admittance_matrix_index_bus_id_mapping(self, optimal_ordering=True):
        admittance_matrix_index_bus_id_mapping = {}
        if optimal_ordering is True:
            admittance_matrix_index_bus_id_mapping['optimal_ordering'] = True
            # Rock that Tinney Scheme #2, hard.
            admittance_matrix_index_bus_id_mapping['mapping'] = self.get_bus_ids_ordered_by_incidence_count()
        else:
            admittance_matrix_index_bus_id_mapping['optimal_ordering'] = False
            admittance_matrix_index_bus_id_mapping['mapping'] = []
            for bus in self.buses:
                admittance_matrix_index_bus_id_mapping['mapping'].append(bus.get_id())
        
        return admittance_matrix_index_bus_id_mapping
        

    def save_admittance_matrix_index_bus_id_mapping(self,
                                                    input_admittance_matrix_index_bus_id_mapping=None,
                                                    optimal_ordering=True):

        if input_admittance_matrix_index_bus_id_mapping is None:
            admittance_matrix_index_bus_id_mapping = self.generate_admittance_matrix_index_bus_id_mapping(optimal_ordering)
        else:
            admittance_matrix_index_bus_id_mapping = {}
            admittance_matrix_index_bus_id_mapping['optimal_ordering'] = None
            admittance_matrix_index_bus_id_mapping['mapping'] = input_admittance_matrix_index_bus_id_mapping

        self.admittance_matrix_index_bus_id_mapping = admittance_matrix_index_bus_id_mapping
        return admittance_matrix_index_bus_id_mapping    


    def get_admittance_matrix_index_bus_id_mapping(self, suppress_exception=False):
        try:
            admittance_matrix_index_bus_id_mapping = self.admittance_matrix_index_bus_id_mapping
        except AttributeError:
            if suppress_exception is True:
                return None
            else:
                raise PowerNetworkError('missing admittance matrix mapping for this power network')
        
        return admittance_matrix_index_bus_id_mapping['mapping']

        
    def is_admittance_matrix_index_bus_id_mapping_optimal(self):
        try:
            admittance_matrix_index_bus_id_mapping = self.admittance_matrix_index_bus_id_mapping
            return admittance_matrix_index_bus_id_mapping['optimal_ordering']
        except AttributeError:
            return None


    def generate_admittance_matrix(self, optimal_ordering=True):
        n = len(self.buses)
        G = zeros([n,n], dtype=float)
        B = zeros([n,n], dtype=float)
        
        # if ordering type is changing from the ordering used in the saved mapping we need to regenerate the mapping
        if optimal_ordering != self.is_admittance_matrix_index_bus_id_mapping_optimal():
            _ = self.save_admittance_matrix_index_bus_id_mapping(optimal_ordering=optimal_ordering)

        admittance_matrix_index_bus_id_mapping = self.get_admittance_matrix_index_bus_id_mapping()

        for i, bus_id_i in enumerate(admittance_matrix_index_bus_id_mapping):
            bus_i = self.get_bus_by_id(bus_id_i)
            for incident_power_line_id in self.get_incident_power_line_ids_by_id(bus_id_i):
                incident_power_line = self.get_power_line_by_id(incident_power_line_id)
                bus_id_j = self.get_connected_bus_id(bus_i, incident_power_line)
                j = self._get_admittance_matrix_index_from_bus_id(bus_id_j)
                if j is None:
                    raise PowerNetworkError('cannot generate admittance matrix, bus id %i cannot be found' % (bus_id_j))
                (gij, bij) = incident_power_line.y
                G[i, i] += gij
                B[i, i] -= bij
                G[i, j] = -gij
                B[i, j] = bij
            (gi, bi) = bus_i.shunt_y
            G[i, i] += gi
            B[i, i] -= bi    
        
        if n > 1:
            G = lil_matrix(G)
            B = lil_matrix(B)
        return G, B
        
    
    def save_admittance_matrix(self, G=None, B=None, optimal_ordering=True):
        if G is None or B is None:
            Ggen, Bgen = self.generate_admittance_matrix(optimal_ordering=optimal_ordering)
            if G is None:
                G = Ggen
            if B is None:
                B = Bgen

        self.G = G
        self.B = B
        return self.G, self.B


    def get_admittance_matrix(self, generate_on_exception=False):
        try:
            G = self.G
        except AttributeError:
            G = None
        try:
            B = self.B
        except AttributeError:
            B = None
        
        if G is None or B is None:
            if generate_on_exception is True:
                G, B = self.save_admittance_matrix(G=G, B=B)
            else:
                raise PowerNetworkError('missing conductance or susceptance matrix for this power network')

        return G, B


    def print_admittance_matrix(self):
        if 'print_table_enabled' in globals() and print_table_enabled is False:
            print 'Cannot print admittance matrix, please install PrettyTable to enable this feature.'
        else:
            table_header = ["bus"]
            for bus in self:
                table_header.append(bus.get_id())
            g_table = PrettyTable(table_header)
            g_table.padding_width = 1
            b_table = PrettyTable(table_header)
            b_table.padding_width = 1
            for bus_i in self:
                bus_i_id = bus_i.get_id()
                conductances = [bus_i_id]
                susceptances = [bus_i_id]
                for bus_j in self:
                    Gij, Bij = self.get_admittance_value_from_bus_ids(bus_i_id, bus_j.get_id())
                    conductances.append(round(Gij, 4))
                    susceptances.append(round(Bij, 4))
                g_table.add_row(conductances)
                b_table.add_row(susceptances)
            
            print "Conductances"
            print g_table
            print "Susceptances"
            print b_table


    def is_slack_bus(self, bus):
        return self.is_slack_bus_by_id(bus.get_id())
        
    
    def is_slack_bus_by_id(self, bus_id):
        slack_bus_id = self.get_slack_bus_id()
        if bus_id == slack_bus_id:
            return True
        
        return False


    def select_slack_bus(self):
        # this will be None if the slack bus is not yet set
        slack_bus_id = self.get_slack_bus_id()
        
        if slack_bus_id is None:
            for bus in self.buses:
                if bus.has_generator_model() is True and slack_bus_id is None:
                    return self.set_slack_bus(bus)

        return slack_bus_id


    def get_slack_bus_id(self):
        try:
            slack_bus_id = self.slack_bus_id
            if slack_bus_id is not None:
                return slack_bus_id
        except AttributeError:
            pass

        return None
        
    
    def get_slack_bus(self):
        slack_bus_id = self.get_slack_bus_id()
        if slack_bus_id is not None:
            return self.get_bus_by_id(slack_bus_id)
        return None


    def set_slack_bus(self, bus):
        bus.make_slack_bus()
        self.slack_bus_id = bus.get_id()
        return self.slack_bus_id
        
    
    def unset_slack_bus(self):
        bus = self.get_slack_bus()
        if bus is not None:
            bus.unmake_slack_bus()
            self.slack_bus_id = None


    def is_voltage_angle_reference_bus(self, bus):
        return self.is_voltage_angle_reference_bus_by_id(bus.get_id())


    def is_voltage_angle_reference_bus_by_id(self, bus_id):
        reference_bus_id = self.get_voltage_angle_reference_bus_id()
        if bus_id == reference_bus_id:
            return True

        return False


    def set_voltage_angle_reference_bus(self, bus):
        return self.set_voltage_angle_reference_bus_by_id(bus.get_id())

        
    def set_voltage_angle_reference_bus_by_id(self, bus_id):
        self.reference_bus_id = bus_id
        return self.reference_bus_id


    def get_voltage_angle_reference_bus_id(self):
        try:
            reference_bus_id = self.reference_bus_id
            return reference_bus_id
        except AttributeError:
            return None


    def get_voltage_angle_reference_bus(self):
        reference_bus_id = self.get_voltage_angle_reference_bus_id()
        if reference_bus_id is not None:
            return self.get_bus_by_id(reference_bus_id)
        else:
            return None
            
    def get_angular_speed_of_voltage_angle_reference_bus(self):
        reference_bus = self.get_voltage_angle_reference_bus()
        if reference_bus is None:
            return None
        else:
            reference_bus.get_current_angular_speed()


    def shift_bus_voltage_angles(self, angle_to_shift):
        for bus in self.buses:
            bus.shift_voltage_angles(angle_to_shift)


    def _get_admittance_matrix_index_from_bus_id(self, bus_id_to_find):
        admittance_matrix_index_bus_id_mapping = self.get_admittance_matrix_index_bus_id_mapping()

        try:
            index_of_bus_id = admittance_matrix_index_bus_id_mapping.index(bus_id_to_find)
        except ValueError:
            index_of_bus_id = None
        
        return index_of_bus_id
        
        
    def get_admittance_value_from_bus_ids(self, bus_id_i, bus_id_j):
        i = self._get_admittance_matrix_index_from_bus_id(bus_id_i)
        if bus_id_i != bus_id_j:
            j = self._get_admittance_matrix_index_from_bus_id(bus_id_j)
        else:
            j = i
        if i is None or j is None:
            return None

        G, B = self.get_admittance_matrix()

        return G[i, j], B[i, j]
        
        
    def _get_current_voltage_vector(self):
        # don't need the output, just need to ensure a slack bus has been selected
        _ = self.get_slack_bus_id()
        voltage_vector = array([])
        for bus_id in self.get_admittance_matrix_index_bus_id_mapping():
            bus = self.get_bus_by_id(bus_id)
            if self.is_slack_bus_by_id(bus_id) is True:
                continue
            V, theta = bus.get_current_voltage_polar()
            # if self.is_voltage_angle_reference_bus_by_id(bus_id) is False:
            voltage_vector = append(voltage_vector, [theta])
            if bus.is_pv_bus() is False:
                voltage_vector = append(voltage_vector, [V])

        return voltage_vector
        
    
    def _save_new_voltages_from_vector(self, new_voltage_vector, replace=True):
        i = 0
        for bus_id in self.get_admittance_matrix_index_bus_id_mapping():
            bus = self.get_bus_by_id(bus_id)
            if self.is_slack_bus(bus) is True:
                continue

            if bus.is_pv_bus() is True:
                # if this is a pv bus we only want to update the voltage angle
                bus.update_voltage_angle(new_voltage_vector[i], replace=replace)
            else:
                # all other buses update both the voltage magnitude and angle
                bus.update_voltage_polar((new_voltage_vector[i+1], new_voltage_vector[i]), replace=replace)
                i += 1

            i += 1
            
    
    def reset_voltages_to_flat_profile(self):
        for bus in self.buses:
            if(bus.is_pv_bus() is False):
                bus.reset_voltage_to_unity_magnitude_zero_angle()
            else:
                if self.is_slack_bus(bus) is False:
                    bus.reset_voltage_to_zero_angle()


    def _generate_function_vector(self):
        function_vector = array([])
        admittance_matrix_index_bus_id_mapping = self.get_admittance_matrix_index_bus_id_mapping()

        (voltage_is_static_list, _, connected_bus_ids_list, interconnection_admittance_list,
         self_admittance_list, _) = self._get_static_vars_list()

        voltage_list, _ = self._get_varying_vars_list(admittance_matrix_index_bus_id_mapping)

        for index, bus_id in enumerate(admittance_matrix_index_bus_id_mapping):
            
            voltage_magnitude_is_static, voltage_angle_is_static = voltage_is_static_list[index]
            
            # does not enter the function vector if the voltage magnitude and angle are static
            if voltage_magnitude_is_static is True and voltage_angle_is_static is True:
                continue
                
            Vpolar_i = voltage_list[index]
            Yii = self_admittance_list[index]
            
            P_injected, Q_injected = self.get_bus_by_id(bus_id).get_apparent_power_injection()
            
            fp, fq = fp_fq_helper(P_injected, Q_injected, Vpolar_i, Yii,
                                  admittance_matrix_index_bus_id_mapping,
                                  voltage_list, connected_bus_ids_list[index],
                                  interconnection_admittance_list[index])

            if voltage_angle_is_static is False:
                function_vector = append(function_vector, fp)
            
            if voltage_magnitude_is_static is False:
                function_vector = append(function_vector, fq)
        # print function_vector
        return function_vector


    def _generate_jacobian_matrix(self):
        admittance_matrix_index_bus_id_mapping = self.get_admittance_matrix_index_bus_id_mapping()
        slack_bus_id = self.get_slack_bus_id()

        (voltage_is_static_list, has_dynamic_model_list, connected_bus_ids_list, interconnection_admittance_list,
         self_admittance_list, jacobian_indices) = self._get_static_vars_list()

        voltage_list, dgr_derivatives = self._get_varying_vars_list(admittance_matrix_index_bus_id_mapping)

        # num_pv_buses = sum([1 if x is True else 0 for x in is_pv_bus_list])
        num_buses = len(admittance_matrix_index_bus_id_mapping)
        num_buses -= sum([1 if x[0] is True and x[1] is True else 0 for x in voltage_is_static_list])
        num_pv_buses = sum([1 if x[0] is True and x[1] is False else 0 for x in voltage_is_static_list])

        n = num_buses*2 - num_pv_buses

        J = zeros((n, n))
        Parallel()(delayed(compute_jacobian_row_by_bus)
                   (J, index, voltage_is_static_list, has_dynamic_model_list, connected_bus_ids_list,
                    jacobian_indices, admittance_matrix_index_bus_id_mapping,
                    interconnection_admittance_list, self_admittance_list, voltage_list,
                    dgr_derivatives) for index, _ in enumerate(admittance_matrix_index_bus_id_mapping))

        # no need to save as sparse matrix if there's only one element, and it breaks spsolve
        if n > 1:
            J = lil_matrix(J)
        return J


    def _get_varying_vars_list(self, index_bus_id_mapping=None):
        if index_bus_id_mapping is None:
            index_bus_id_mapping = self.get_admittance_matrix_index_bus_id_mapping()
        return frompyfunc(self._varying_var_helper, 1, 2)(index_bus_id_mapping)


    def _varying_var_helper(self, bus_id):
        bus = self.get_bus_by_id(bus_id)
        Vpolar = bus.get_current_voltage_polar()
        
        if bus.has_dynamic_model() is True and bus.is_pv_bus() is False:
            dgr_derivatives = bus.get_apparent_power_derivatives()
        else:
            dgr_derivatives = ()

        return Vpolar, dgr_derivatives

        
    def save_static_vars_list(self, index_bus_id_mapping=None):

        (voltage_is_static_list, has_dynamic_model_list, connected_bus_ids_list,
         interconnection_admittance_list, self_admittance_list,
         jacobian_indices) = self._generate_static_vars_list(index_bus_id_mapping)
         
        self.voltage_is_static_list = voltage_is_static_list
        self.has_dynamic_model_list = has_dynamic_model_list
        self.connected_bus_ids_list = connected_bus_ids_list
        self.interconnection_admittance_list = interconnection_admittance_list
        self.self_admittance_list = self_admittance_list
        self.jacobian_indices = jacobian_indices        


    def _get_static_vars_list(self, force_recompute=False, index_bus_id_mapping=None):
        recompute = False
        if force_recompute is True:
            recompute = True
        else:
            try:
                voltage_is_static_list = self.voltage_is_static_list
                has_dynamic_model_list = self.has_dynamic_model_list
                connected_bus_ids_list = self.connected_bus_ids_list
                interconnection_admittance_list = self.interconnection_admittance_list
                self_admittance_list = self.self_admittance_list
                jacobian_indices = self.jacobian_indices
            except AttributeError:
                recompute = True
        
        if recompute is True:
            return self._generate_static_vars_list(index_bus_id_mapping)
        else:
            return (voltage_is_static_list, has_dynamic_model_list, connected_bus_ids_list,
                    interconnection_admittance_list, self_admittance_list, jacobian_indices)


    def _generate_static_vars_list(self, index_bus_id_mapping=None):
        if index_bus_id_mapping is None:
            index_bus_id_mapping = self.get_admittance_matrix_index_bus_id_mapping()
        
        (voltage_is_static_list, has_dynamic_model_list, connected_bus_ids_list, interconnection_admittance_list, 
         self_admittance_list) = frompyfunc(self._static_var_helper, 1, 5)(index_bus_id_mapping)
        
        jacobian_indices = []
        current_index = 0
        for index, bus_id in enumerate(index_bus_id_mapping):
            if voltage_is_static_list[index][0] is True and voltage_is_static_list[index][1] is True:
                jacobian_indices.append(None)
            else:
                jacobian_indices.append(current_index)
                if voltage_is_static_list[index][0] is True:
                    current_index += 1
                else:
                    current_index += 2   

        return (voltage_is_static_list, has_dynamic_model_list, connected_bus_ids_list,
                interconnection_admittance_list, self_admittance_list, jacobian_indices)


    def _static_var_helper(self, bus_id):
        bus = self.get_bus_by_id(bus_id)

        self_admittance = self.get_admittance_value_from_bus_ids(bus_id, bus_id)

        interconnection_admittance, connected_bus_ids = self._get_connected_bus_admittances_by_bus_id(bus_id, True)

        return (bus.is_voltage_polar_static(), bus.has_dynamic_model(),
                connected_bus_ids, interconnection_admittance, self_admittance)


    def solve_power_flow(self, optimal_ordering=True, append=True, force_static_var_recompute=False):
        # need to check if ordering has changed since admittance matrix was last generated
        if optimal_ordering != self.is_admittance_matrix_index_bus_id_mapping_optimal():
            self.save_admittance_matrix(optimal_ordering=optimal_ordering)
            
        if force_static_var_recompute is True:
            self.save_static_vars_list()

        if append is True:
            # create a new column in each of the nodes' states to append the solution from power flow
            x = self._get_current_voltage_vector()
            self._save_new_voltages_from_vector(x, replace=False)

            
        x_root, _ = self.solver.find_roots(get_current_states_method=self._get_current_voltage_vector,
                                           save_updated_states_method=self._save_new_voltages_from_vector,
                                           get_jacobian_method=self._generate_jacobian_matrix, 
                                           get_function_vector_method=self._generate_function_vector)

        self._compute_and_save_line_power_flows(append=append)
        return x_root
        
        
    def _compute_and_save_line_power_flows(self, append=True):
        for power_line in self.power_lines:
            P, Q = self._compute_line_power_flow(power_line)
            if append is True:
                power_line.append_complex_power(P, Q)
            elif append is False:
                power_line.replace_complex_power(P, Q)
            else:
                raise PowerNetworkError('cannot compute power flows, append kwarg must be True or False')

            
    def _compute_line_power_flow(self, power_line):
        bus_i, bus_j = power_line.get_incident_buses()
        bus_i_id = bus_i.get_id()
        bus_j_id = bus_j.get_id()
        Gij, Bij = self.get_admittance_value_from_bus_ids(bus_i_id, bus_j_id)
        Vi, thetai = bus_i.get_current_voltage_polar() 
        Vj, thetaj = bus_j.get_current_voltage_polar()
        Pij = -Gij*Vi**2 + Vi*Vj*(Gij*cos(thetai - thetaj) - Bij*sin(thetai - thetaj))
        Qij = -Bij*Vi**2 + Vi*Vj*(Gij*sin(thetai - thetaj) + Bij*cos(thetai - thetaj))
        return Pij, Qij

    
    def compute_apparent_power_injected_from_network(self, bus):
        admittance_matrix_index_bus_id_mapping = self.get_admittance_matrix_index_bus_id_mapping()

        _, _, connected_bus_ids_list, interconnection_admittance_list, self_admittance, _ = self._get_static_vars_list()

        voltage_list, _ = self._get_varying_vars_list(admittance_matrix_index_bus_id_mapping)

        bus_id = bus.get_id()
        index = admittance_matrix_index_bus_id_mapping.index(bus_id)
                
        Vpolar_i = voltage_list[index]
        Yii = self_admittance[index]
        
        return compute_apparent_power_injected_from_network(Vpolar_i, Yii,
                                                            admittance_matrix_index_bus_id_mapping,
                                                            voltage_list, connected_bus_ids_list[index],
                                                            interconnection_admittance_list[index])


    def get_buses_with_dynamic_models(self):
        try:
            buses_with_dynamic_models = self.buses_with_dynamic_models
        except AttributeError:
            bus_ids_with_dynamic_models = [bus.get_id() for bus in self.buses if bus.has_dynamic_model()]
            self.buses_with_dynamic_models = [self.get_bus_by_id(bus_id) for bus_id in bus_ids_with_dynamic_models]
            
        return self.buses_with_dynamic_models


    def prepare_for_dynamic_simulation_initial_value_calculation(self):
        [bus.prepare_for_dynamic_simulation_initial_value_calculation() for bus in self.get_buses_with_dynamic_models()]
        self.select_slack_bus()


    def compute_initial_values_for_dynamic_simulation(self):
        return self.solve_power_flow(append=False, force_static_var_recompute=True)


    def initialize_dynamic_model_states(self):
        for bus in self.get_buses_with_dynamic_models():
            bus.initialize_dynamic_states()


    def prepare_for_dynamic_simulation(self, reference_bus_id=None):
        # need a reference bus for dynamic simulation, use the slack bus if none provided
        if reference_bus_id is None:
            reference_bus = self.get_slack_bus()
        else:
            self.get_bus_by_id(reference_bus_id)
            
        self.unset_slack_bus()
        self.set_voltage_angle_reference_bus(reference_bus)
        # retrieve referernce bus this way to ensure previous steps worked
        reference_bus = self.get_voltage_angle_reference_bus()
        if reference_bus.has_dynamic_model() is False:
            raise PowerNetworkError('selected reference bus must have a dynamic model')
        reference_angle = reference_bus.model.get_internal_voltage_angle()
        
        self.shift_bus_voltage_angles(reference_angle)
        
        [bus.prepare_for_dynamic_simulation() for bus in self.get_buses_with_dynamic_models()]
        
        # need to update static variables to account for some changed bus properties (e.g., static voltage magnitude)
        self.save_static_vars_list()

    
    def prepare_for_dynamic_state_update(self):
        # TO DO: handle reference speed for structure preserving model
        for bus in self.get_buses_with_dynamic_models():
            bus.prepare_for_dynamic_state_update()


    def get_current_dynamic_states(self):
        dynamic_states = empty(0)
        self.dynamic_state_bus_index_mapping = []
        for bus in self.get_buses_with_dynamic_models():
            i = bus.get_id()
            dynamic_states_i = bus.get_current_dynamic_state_array()
            self.dynamic_state_bus_index_mapping.append((i, dynamic_states_i.shape[0]))
            dynamic_states = hstack((dynamic_states, dynamic_states_i))

        return dynamic_states


    def _parse_current_dynamic_state_array(self, state_array, bus_id, num_states):
        try:
            dynamic_state_bus_index_mapping = self.dynamic_state_bus_index_mapping
        except AttributeError:
            raise AttributeError('FILL IN')
        
        i = dynamic_state_bus_index_mapping.index((bus_id, num_states))
        
        k = 0
        for j in range(0, i):
            k += dynamic_state_bus_index_mapping[j][1]
        
        return state_array[k:(k+num_states)]


    def get_dynamic_state_time_derivative_array(self, current_states=None):
        dynamic_state_derivatives = empty(0)
        try:
            dynamic_state_bus_index_mapping = self.dynamic_state_bus_index_mapping
        except AttributeError:
            raise AttributeError('FILL IN')
        
        if current_states is None:
            current_states = self.get_current_dynamic_states()
            
        for bus_id, num_states in dynamic_state_bus_index_mapping:
            current_states_i = self._parse_current_dynamic_state_array(current_states, bus_id, num_states)
            dynamic_state_derivatives_i = self.get_bus_by_id(bus_id).get_dynamic_state_time_derivative_array(current_states=current_states_i)
            dynamic_state_derivatives = hstack((dynamic_state_derivatives, dynamic_state_derivatives_i))
        
        return dynamic_state_derivatives


    def update_dynamic_states(self, numerical_integration_method):
        current_states = self.get_current_dynamic_states()
        updated_states = numerical_integration_method(current_states, self.get_dynamic_state_time_derivative_array)
        for bus_id, num_states in self.dynamic_state_bus_index_mapping:
            updated_states_i = self._parse_current_dynamic_state_array(updated_states, bus_id, num_states)
            self.get_bus_by_id(bus_id).save_new_dynamic_state_array(updated_states_i)


    def update_algebraic_states(self, admittance_matrix_recompute_required=False):
        if admittance_matrix_recompute_required is True:
            _, _ = self.save_admittance_matrix()
        # _ = n.solve_power_flow(force_static_var_recompute=force_static_var_recompute, append=append)
