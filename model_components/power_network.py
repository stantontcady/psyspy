from itertools import count
from operator import itemgetter
from math import sin, cos

from numpy import append, array, zeros, frompyfunc, hstack, set_printoptions, inf
from numpy.linalg import norm, cond
from scipy.sparse import lil_matrix, csr_matrix, diags
from scipy.sparse.linalg import spsolve

from power_line import PowerLine
from simulation_resources import NewtonRhapson

from IPython import embed


class PowerNetwork(object):
    
    def __init__(self, buses=[], power_lines=[]):
        self.buses = []
        self.buses.extend(buses)
        self.power_lines = []
        self.power_lines.extend(power_lines)
        set_printoptions(linewidth=175)
        self.solver = NewtonRhapson(tolerance=0.00001)

        
    def __repr__(self):
        output = ''
        for bus in self.buses:
            output += bus.repr_helper(simple=True, indent_level_increment=2)
        for power_line in self.power_lines:
            output += power_line.repr_helper(simple=True, indent_level_increment=2)
        return output

        
    def add_bus(self, bus):
        if self.bus_in_network(bus) is False:
            self.buses.append(bus)

    
    def add_power_line(self, power_line):
        self.power_lines.append(power_line)

        
    def connect_buses(self, bus_a, bus_b, z=(), y=()):
        self.add_bus(bus_a)
        self.add_bus(bus_b)
        
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


    def get_admittance_matrix_index_bus_id_mapping(self):
        try:
            admittance_matrix_index_bus_id_mapping = self.admittance_matrix_index_bus_id_mapping
        except AttributeError:
            raise AttributeError('missing admittance matrix mapping for this power network')
        
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
                    raise AttributeError('cannot generate admittance matrix, bus id %i cannot be found' % (bus_id_j))
                (gij, bij) = incident_power_line.y
                G[i, i] += gij
                B[i, i] -= bij
                G[i, j] = -gij
                B[i, j] = bij
            (gi, bi) = bus_i.shunt_y
            G[i, i] += gi
            B[i, i] -= bi    
                
        
        return lil_matrix(G), lil_matrix(B)
        
    
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


    def get_admittance_matrix(self):
        try:
            G = self.G
        except AttributeError:
            G = None
        try:
            B = self.B
        except AttributeError:
            B = None
        
        if G is None or B is None:
            raise AttributeError('missing conductance or susceptance matrix for this power network')
            
        return G, B
        
        
    def is_slack_bus(self, bus):
        return self.is_slack_bus_by_id(bus.get_id())
        
    
    def is_slack_bus_by_id(self, bus_id):
        slack_bus_id = self.get_slack_bus_id()
        if bus_id == slack_bus_id:
            return True
        
        return False


    def select_slack_bus(self):          
        slack_bus_id = None
        for bus in self.buses:
            bus_id = bus.get_id()
            if bus.is_pv_bus() is True and slack_bus_id is None:
                slack_bus_id = bus_id
                break

            self.slack_bus_id = slack_bus_id
        return slack_bus_id


    def get_slack_bus_id(self):
        try:
            slack_bus_id = self.slack_bus_id
            return slack_bus_id
        except AttributeError:
            raise AttributeError('no slack bus selected for this power network')


    def set_slack_bus(self, bus):
        self.slack_bus_id = bus.get_id()
        return self.slack_bus_id


    def unset_slack_bus(self):
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
            # raise AttributeError('no voltage angle reference bus selected for this power network')


    def get_voltage_angle_reference_bus(self):
        reference_bus_id = self.get_voltage_angle_reference_bus_id()
        if reference_bus_id is not None:
            return self.get_bus_by_id(reference_bus_id)
        else:
            return None
            
            
    def shift_bus_voltage_angles(self, angle_to_shift):
        for bus in self.buses:
            current_angle = bus.get_current_voltage_angle()
            bus.update_voltage_angle((current_angle-angle_to_shift), replace=True)

    def _get_admittance_matrix_index_from_bus_id(self, bus_id_to_find):
        admittance_matrix_index_bus_id_mapping = self.get_admittance_matrix_index_bus_id_mapping()

        try:
            index_of_bus_id = admittance_matrix_index_bus_id_mapping.index(bus_id_to_find)
        except ValueError:
            index_of_bus_id = None
        
        return index_of_bus_id
        
        
    def _get_admittance_value_from_bus_ids(self, bus_id_i, bus_id_j):
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
            V, theta = bus.get_current_voltage()
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
                bus.update_voltage(new_voltage_vector[i+1], new_voltage_vector[i], replace=replace)
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
        for bus_id in admittance_matrix_index_bus_id_mapping:
            bus = self.get_bus_by_id(bus_id)
            if self.is_slack_bus(bus) is True:
                continue
            fp, fq = self._fp_fq_helper(bus)
            # if self.is_voltage_angle_reference_bus_by_id(bus_id) is False:
            function_vector = append(function_vector, fp)
            
            if bus.is_pv_bus() is False:
                function_vector = append(function_vector, fq)
        
        return function_vector


    def _fp_fq_helper(self, bus_i):
        bus_id_i = bus_i.get_id()
        Vi_polar = bus_i.get_current_voltage()
        Gii, Bii = self._get_admittance_value_from_bus_ids(bus_id_i, bus_id_i)
        P_net, Q_net = bus_i.get_specified_real_reactive_power()
        connected_bus_ids = self.get_all_connected_bus_ids_by_id(bus_id_i)
        
        P_network = self.compute_real_power_injected_from_network(None, bus_id_i, Vi_polar, Gii, connected_bus_ids)
        fp = P_network - P_net
        Q_network = self.compute_reactive_power_injected_from_network(None, bus_id_i, Vi_polar, Bii, connected_bus_ids)
        fq = Q_network - Q_net
            
        return fp, fq


    def _generate_jacobian_matrix(self):
        admittance_matrix_index_bus_id_mapping = self.get_admittance_matrix_index_bus_id_mapping()
        slack_bus_id = self.get_slack_bus_id()
        
        J, list_of_bus_id_lists = frompyfunc(self._jacobian_diagonal_helper, 1, 2)(admittance_matrix_index_bus_id_mapping)
        J = diags(hstack(J), 0, format='lil')
        
        jacobian_matrix_index_bus_id_mapping = [int(bus_id) for bus_id in hstack(list_of_bus_id_lists).tolist() if bus_id is not None]
        
        n = len(jacobian_matrix_index_bus_id_mapping)

        i = 0
        while i < n:
            bus_id_i = jacobian_matrix_index_bus_id_mapping[i]
            bus_i = self.get_bus_by_id(bus_id_i)
            connected_bus_ids = self.get_all_connected_bus_ids_by_id(bus_id_i)
            Vi_polar = bus_i.get_current_voltage()
            bus_i_is_pv_bus = bus_i.is_pv_bus()
            if bus_i.has_dynamic_dgr_attached() is True and bus_i_is_pv_bus is False:
                Vi, thetai = Vi_polar
                Hii_dgr, Nii_dgr, Kii_dgr, Lii_dgr = bus_i.dgr.get_real_reactive_power_derivatives(Vi, thetai)
            j = 0
            while j < n:
                if i == j:
                    if bus_i_is_pv_bus is False:
                        J[i+1, j] = self._jacobian_kii_helper(bus_id_i, Vi_polar, connected_bus_ids)
                        J[i, j+1] = self._jacobian_nii_helper(bus_id_i, Vi_polar, connected_bus_ids, Kii=J[i+1, j])
                        if bus_i.has_dynamic_dgr_attached() is True:
                            J[i, j] += Hii_dgr
                            J[i, j+1] += Nii_dgr
                            J[i+1, j] += Kii_dgr
                            J[i+1, j+1] += Lii_dgr
                        j += 1
                else:
                    bus_id_j = jacobian_matrix_index_bus_id_mapping[j]
                    if bus_id_j in connected_bus_ids and self.is_slack_bus_by_id(bus_id_j) is False:
                        Gij, Bij = self._get_admittance_value_from_bus_ids(bus_id_i, bus_id_j)
                        bus_j = self.get_bus_by_id(bus_id_j)
                        Vj_polar = bus_j.get_current_voltage()

                        J[i, j] = self._jacobian_hij_helper(Vi_polar, Vj_polar, Gij, Bij)


                        if bus_i_is_pv_bus is False:
                            J[i+1, j] = self._jacobian_kij_helper(Vi_polar, Vj_polar, Gij, Bij)

                        if bus_j.is_pv_bus() is False:
                            if bus_i_is_pv_bus is False:
                                J[i+1, j+1] = self._jacobian_lij_helper(Vi_polar, Vj_polar, Gij, Bij, J[i, j])
                                Kij = J[i+1, j]
                            else:
                                Kij = None
                            J[i, j+1] = self._jacobian_nij_helper(Vi_polar, Vj_polar, Gij, Bij, Kij)
                            j += 1
                j += 1
                    
            if bus_i_is_pv_bus is False:
                i += 1
            i += 1
        
        return J

    
    def _jacobian_diagonal_helper(self, bus_id):
        bus = self.get_bus_by_id(bus_id)
        if self.is_slack_bus(bus) is True:
            return [], []

        Vi_polar = bus.get_current_voltage()
        connected_bus_ids = self.get_all_connected_bus_ids_by_id(bus_id)

        Hii = self._jacobian_hii_helper(bus_id, Vi_polar, connected_bus_ids)
        
        diag_elements = [Hii]
        jacobian_indices = [bus_id]

        if bus.is_pv_bus() is False:
            diag_elements.append(self._jacobian_lii_helper(bus_id, Vi_polar, connected_bus_ids, Hii))
            jacobian_indices.append(bus_id)
            
        return diag_elements, jacobian_indices


    def _jacobian_hij_helper(self, Vi_polar, Vj_polar, Gij, Bij, Lij=None):
        Vj, thetaj = Vj_polar
        if Lij is not None:
            return Lij*Vj
        else:
            Vi, thetai = Vi_polar
            return Vi*Vj*(Gij*sin(thetai - thetaj) + Bij*cos(thetai - thetaj))

        
    def _jacobian_hii_helper(self, bus_id_i, Vi_polar, connected_bus_ids, Lii=None):
        Vi, thetai = Vi_polar
        if Lii is not None:
            _, Bii = self._get_admittance_value_from_bus_ids(bus_id_i, bus_id_i)
            Qneti = self._get_qneti(Bii, Vi, Lii=Lii)
            return Bii*Vi**2 - Qneti
        else:
            Hii = 0
            for bus_id_k in connected_bus_ids:
                bus_k = self.get_bus_by_id(bus_id_k)
                Vk, thetak = bus_k.get_current_voltage()
                Gik, Bik = self._get_admittance_value_from_bus_ids(bus_id_i, bus_id_k)
                Hii += Vk*(Gik*sin(thetai - thetak) + Bik*cos(thetai - thetak))

            return -1*Vi*Hii


    def _jacobian_nij_helper(self, Vi_polar, Vj_polar, Gij, Bij, Kij=None):
        Vj, thetaj = Vj_polar
        if Kij is not None:
            return -1*Kij/Vj
        else:
            Vi, thetai = Vi_polar
            return Vi*(Gij*cos(thetai - thetaj) - Bij*sin(thetai - thetaj))
        
        
    def _jacobian_nii_helper(self, bus_id_i, Vi_polar, connected_bus_ids, Kii=None):
        Vi, thetai = Vi_polar
        Gii, _ = self._get_admittance_value_from_bus_ids(bus_id_i, bus_id_i)
        if Kii is not None:
            Pneti = self._get_pneti(Gii, Vi, Kii=Kii)
            return Gii*Vi + Pneti/Vi
        else:
            Nii = 2*Gii*Vi
            for bus_id_k in connected_bus_ids:
                bus_k = self.get_bus_by_id(bus_id_k)
                Vk, thetak = bus_k.get_current_voltage()
                Gik, Bik = self._get_admittance_value_from_bus_ids(bus_id_i, bus_id_k)
                Nii += Vk*(Gik*cos(thetai - thetak) - Bik*sin(thetai - thetak))
            return Nii
        

    def _jacobian_kij_helper(self, Vi_polar, Vj_polar, Gij, Bij, Nij=None):
        Vj, thetaj = Vj_polar
        if Nij is not None:
            return -1*Nij*Vj
        else:
            Vi, thetai = Vi_polar
            return -1*Vi*Vj*(Gij*cos(thetai - thetaj) - Bij*sin(thetai - thetaj))
        
    
    def _jacobian_kii_helper(self, bus_id_i, Vi_polar, connected_bus_ids, Nii=None):
        Vi, thetai = Vi_polar
        if Nii is not None:
            Gii, _ = self._get_admittance_value_from_bus_ids(bus_id_i, bus_id_i)
            Pneti = self._get_pneti(Gii, Vi, Nii=Nii)
            return -1*Gii*Vi**2 + Pneti
        else:
            Kii = 0
            for bus_id_k in connected_bus_ids:
                bus_k = self.get_bus_by_id(bus_id_k)
                Vk, thetak = bus_k.get_current_voltage()
                Gik, Bik = self._get_admittance_value_from_bus_ids(bus_id_i, bus_id_k)
                Kii += Vk*(Gik*cos(thetai - thetak) - Bik*sin(thetai - thetak))
            return Vi*Kii
        
    
    def _jacobian_lij_helper(self, Vi_polar, Vj_polar, Gij, Bij, Hij=None):
        Vj, thetaj = Vj_polar
        if Hij is not None:
            return Hij/Vj
        else:
            Vi, thetai = Vi_polar
            return Vi*(Gij*sin(thetai - thetaj) + Bij*cos(thetai - thetaj))
        
    
    def _jacobian_lii_helper(self, bus_id_i, Vi_polar, connected_bus_ids, Hii=None):
        _, Bii = self._get_admittance_value_from_bus_ids(bus_id_i, bus_id_i)
        Vi, thetai = Vi_polar
        if Hii is not None:
            Qneti = self._get_qneti(Bii, Vi, Hii=Hii)
            return Bii*Vi + Qneti/Vi
        else:
            Lii = 2*Bii*Vi

            for bus_id_k in connected_bus_ids:
                bus_k = self.get_bus_by_id(bus_id_k)
                Vk, thetak = bus_k.get_current_voltage()
                Gik, Bik = self._get_admittance_value_from_bus_ids(bus_id_i, bus_id_k)
                Lii += Vk*(Gik*sin(thetai - thetak) + Bik*cos(thetai - thetak))
            return Lii

    
    @staticmethod
    def _get_pneti(Gii, Vi, Nii=None, Kii=None):
        if Nii is not None:
            return Vi*(Nii-Gii*Vi)
        elif Kii is not None:
            return Gii*Vi**2 + Kii
        return None

    
    @staticmethod
    def _get_qneti(Bii, Vi, Hii=None, Lii=None):
        if Hii is not None:
            return Bii*Vi**2 - Hii
        elif Lii is not None:
            return Vi*(Lii - Bii*Vi)
        return None
        

    def solve_power_flow(self, tolerance=0.00001, optimal_ordering=True, append=True):
        # need to check if ordering has changed since admittance matrix was last generated
        if optimal_ordering != self.is_admittance_matrix_index_bus_id_mapping_optimal():
            self.save_admittance_matrix(optimal_ordering=optimal_ordering)
        if append is True:
            # create a new column in each of the nodes' states to append the solution from power flow
            x = self._get_current_voltage_vector()
            self._save_new_voltages_from_vector(x, replace=False)
            
        x_root, k = self.solver.find_roots(get_current_states_method=self._get_current_voltage_vector,
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
                raise ValueError('append kwarg must be True or False')

            
    def _compute_line_power_flow(self, power_line):
        bus_i, bus_j = power_line.get_incident_buses()
        bus_i_id = bus_i.get_id()
        bus_j_id = bus_j.get_id()
        Gij, Bij = self._get_admittance_value_from_bus_ids(bus_i_id, bus_j_id)
        Vi, thetai = bus_i.get_current_voltage() 
        Vj, thetaj = bus_j.get_current_voltage()
        Pij = -Gij*Vi**2 + Vi*Vj*(Gij*cos(thetai - thetaj) - Bij*sin(thetai - thetaj))
        Qij = -Bij*Vi**2 + Vi*Vj*(Gij*sin(thetai - thetaj) + Bij*cos(thetai - thetaj))
        return Pij, Qij


    def compute_reactive_power_injected_from_network(self,
                                                     bus_i=None,
                                                     bus_id_i=None,
                                                     Vi_polar=None,
                                                     Bii=None,
                                                     connected_bus_ids=None):
        if bus_i is None and (bus_id_i is None or Vi_polar is None or Bii is None or connected_bus_ids is None):
            raise AttributeError('must provide bus object or all of: bus id, \
                                  bus polar voltage, self susceptance, and a list of conencted bus ids')
        
        if bus_id_i is None:
            bus_id_i = bus_i.get_id()
        if Vi_polar is None:
            Vi_polar = bus_i.get_current_voltage()
        if Bii is None:
            _, Bii = self._get_admittance_value_from_bus_ids(bus_id_i, bus_id_i)
        if connected_bus_ids is None:
            connected_bus_ids = self.get_all_connected_bus_ids_by_id(bus_id_i)
        Vi, thetai = Vi_polar
        Q = Bii*Vi
        
        for bus_id_k in connected_bus_ids:
            bus_k = self.get_bus_by_id(bus_id_k)
            Vk, thetak = bus_k.get_current_voltage()
            Gik, Bik = self._get_admittance_value_from_bus_ids(bus_id_i, bus_id_k)
            Q += Vk*(Gik*sin(thetai - thetak) + Bik*cos(thetai - thetak))
        
        Q *= Vi
        return Q


    def compute_real_power_injected_from_network(self,
                                                 bus_i=None,
                                                 bus_id_i=None,
                                                 Vi_polar=None,
                                                 Gii=None,
                                                 connected_bus_ids=None):
        if bus_i is None and (bus_id_i is None or Vi_polar is None or Gii is None or connected_bus_ids is None):
            raise AttributeError('must provide bus object or all of: bus id, \
                                  bus polar voltage, self conductance, and a list of conencted bus ids')
        
        if bus_id_i is None:
            bus_id_i = bus_i.get_id()
        if Vi_polar is None:
            Vi_polar = bus_i.get_current_voltage()
        if Gii is None:
            Gii, _ = self._get_admittance_value_from_bus_ids(bus_id_i, bus_id_i)
        if connected_bus_ids is None:
            connected_bus_ids = self.get_all_connected_bus_ids_by_id(bus_id_i)
        Vi, thetai = Vi_polar
        P = Gii*Vi
        
        for bus_id_k in connected_bus_ids:
            bus_k = self.get_bus_by_id(bus_id_k)
            Vk, thetak = bus_k.get_current_voltage()
            Gik, Bik = self._get_admittance_value_from_bus_ids(bus_id_i, bus_id_k)
            P += Vk*(Gik*cos(thetai - thetak) - Bik*sin(thetai - thetak))
        
        P *= Vi
        return P


    def identify_dynamic_dgr_buses(self):
        self.dynamic_dgr_bus_ids = []
        for bus in self.buses:
            if bus.has_dynamic_dgr_attached() is True:
                self.dynamic_dgr_bus_ids.append(bus.get_id())
                
        return self.dynamic_dgr_bus_ids
                

    def get_dynamic_dgr_buses(self):
        try:
            dynamic_dgr_bus_ids = self.dynamic_dgr_bus_ids
        except AttributeError:
            dynamic_dgr_bus_ids = self.identify_dynamic_dgr_buses()
        
        return [self.get_bus_by_id(bus_id) for bus_id in dynamic_dgr_bus_ids]
