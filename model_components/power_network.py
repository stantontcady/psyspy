from itertools import count
from operator import itemgetter
from math import sin, cos

from numpy import append, array, zeros, frompyfunc, hstack, set_printoptions, inf
from numpy.linalg import norm
from scipy.sparse import lil_matrix, csr_matrix, diags
from scipy.sparse.linalg import spsolve

from power_line import PowerLine


class PowerNetwork(object):
    
    def __init__(self, buses=[], power_lines=[]):
        self.buses = []
        self.buses.extend(buses)
        self.power_lines = []
        self.power_lines.extend(power_lines)
        set_printoptions(linewidth=175)

        
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
                    bus_info['%i' % bus.get_id()] += 1
                except KeyError:
                    bus_info['%i' % bus.get_id()] = 1

        return [int(bus_tuple[0]) for bus_tuple in sorted(bus_info.items(), key=itemgetter(1))]

        
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
    

    def generate_admittance_matrix(self):
        n = len(self.buses)
        G = zeros([n,n], dtype=float)
        B = zeros([n,n], dtype=float)
        bus_ids = []
        for bus in self.buses:
            bus_ids.append(bus.get_id())
        
        # bus_ids = self.get_bus_ids_ordered_by_incidence_count()
        
        def get_index_from_bus_id(bus_id_to_find):
            try:
                index_of_bus_id = bus_ids.index(bus_id_to_find)
            except ValueError:
                index_of_bus_id = None
            return index_of_bus_id

        for i, bus_id_i in enumerate(bus_ids):
            bus_i = self.get_bus_by_id(bus_id_i)
            for incident_power_line_id in self.get_incident_power_line_ids_by_id(bus_id_i):
                incident_power_line = self.get_power_line_by_id(incident_power_line_id)
                bus_id_j = self.get_connected_bus_id(bus_i, incident_power_line)
                j = get_index_from_bus_id(bus_id_j)
                if j is None:
                    raise ValueError('cannot generate admittance matrix, bus id %i cannot be found' % (bus_id_j))
                (gij, bij) = incident_power_line.y
                G[i, i] += gij
                B[i, i] -= bij
                G[i, j] = -gij
                B[i, j] = bij
            (gi, bi) = bus_i.shunt_y
            G[i, i] += gi
            B[i, i] -= bi    
                
        
        return lil_matrix(G), lil_matrix(B), bus_ids


    def save_admittance_matrix(self, G=None, B=None):
        if G is None or B is None:
            Ggen, Bgen, admittance_matrix_index_bus_id_mapping = self.generate_admittance_matrix()
            if G is None:
                G = Ggen
            if B is None:
                B = Bgen

        self.G = G
        self.B = B
        self.admittance_matrix_index_bus_id_mapping = admittance_matrix_index_bus_id_mapping
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
            Ggen, Bgen = self.save_admittance_matrix()
        
        if G is None:
            G = Ggen
        if B is None:
            B = Bgen
            
        return G, B
        
    
    def get_admittance_matrix_bus_id_index_mapping(self):
        try:
            mapping = self.admittance_matrix_index_bus_id_mapping
        except AttributeError:
            _, _ = self.get_admittance_matrix()
        mapping = self.admittance_matrix_index_bus_id_mapping
        
        return mapping
        
        
    def is_slack_bus(self, bus):
        return self.is_slack_bus_by_id(bus.get_id())
        
    
    def is_slack_bus_by_id(self, bus_id):
        try:
            if bus_id == self.slack_bus_id:
                return True
        except AttributeError:
            raise AttributeError('no slack bus selected for this power network')
            
        return False

    
    def select_slack_bus(self):          
        slack_bus_id = None
        for bus in self.buses:
            bus_id = bus.get_id()
            if bus.has_generator_attached() is True and slack_bus_id is None:
                slack_bus_id = bus_id
                break

            self.slack_bus_id = slack_bus_id
        return slack_bus_id
        
    
    def get_slack_bus_id(self):
        try:
            slack_bus_id = self.slack_bus_id
            return slack_bus_id
        except AttributeError:
            return self.select_slack_bus()
    

    def set_slack_bus(self, bus):
        self.slack_bus_id = bus.get_id()
        return self.slack_bus_id
        
        
    def get_admittance_matrix_index_from_bus_id(self, bus_id_to_find):
        admittance_matrix_index_bus_id_mapping = self.get_admittance_matrix_bus_id_index_mapping()

        try:
            index_of_bus_id = admittance_matrix_index_bus_id_mapping.index(bus_id_to_find)
        except ValueError:
            index_of_bus_id = None
        
        return index_of_bus_id
        
        
    def get_admittance_value_from_bus_ids(self, bus_id_i, bus_id_j):
        i = self.get_admittance_matrix_index_from_bus_id(bus_id_i)
        if bus_id_i != bus_id_j:
            j = self.get_admittance_matrix_index_from_bus_id(bus_id_j)
        else:
            j = i
        if i is None or j is None:
            return None

        G, B = self.get_admittance_matrix()

        return G[i, j], B[i, j]
        
        
    def get_current_voltage_vector(self):
        # don't need the output, just need to ensure a slack bus has been selected
        _ = self.get_slack_bus_id()
        voltage_vector = array([])
        for bus_id in self.get_admittance_matrix_bus_id_index_mapping():
            bus = self.get_bus_by_id(bus_id)
            if self.is_slack_bus_by_id(bus_id) is True:
                continue
            V, theta = bus.get_current_node_voltage()
            voltage_vector = append(voltage_vector, [theta])
            if bus.has_generator_attached() is False:
                voltage_vector = append(voltage_vector, [V])

        return voltage_vector
        
    
    def update_voltage_vector(self, new_voltage_vector):
        i = 0
        for bus_id in self.get_admittance_matrix_bus_id_index_mapping():
            bus = self.get_bus_by_id(bus_id)
            if self.is_slack_bus(bus) is True:
                continue
            if bus.has_generator_attached() is False:
                _, _ = bus.replace_node_voltage(new_voltage_vector[i+1], new_voltage_vector[i])
                i += 1
            else:
                bus.replace_node_voltage_angle(new_voltage_vector[i])
            
            i += 1

            
    def generate_function_vector(self):
        function_vector = array([])
        admittance_matrix_index_bus_id_mapping = self.get_admittance_matrix_bus_id_index_mapping()
        for bus_id in admittance_matrix_index_bus_id_mapping:
            bus = self.get_bus_by_id(bus_id)
            if self.is_slack_bus(bus) is True:
                continue
            fp, fq = self._fp_fq_helper(bus)
            function_vector = append(function_vector, fp)
            if bus.has_generator_attached() is False:
                function_vector = append(function_vector, fq)
        
        return function_vector
        
            
    def _fp_fq_helper(self, bus):
        bus_id_i = bus.get_id()
        Vi, thetai = bus.get_current_node_voltage()
        Gii, Bii = self.get_admittance_value_from_bus_ids(bus_id_i, bus_id_i)
        Pnet, Qnet = bus.get_specified_real_reactive_power()

        
        fp = Gii*Vi

        if bus.has_generator_attached() is False:
            fq = Bii*Vi
        else:
            fq = 0

        for bus_id_k in self.get_all_connected_bus_ids_by_id(bus_id_i):
            bus_k = self.get_bus_by_id(bus_id_k)
            Vk, thetak = bus_k.get_current_node_voltage()
            Gik, Bik = self.get_admittance_value_from_bus_ids(bus_id_i, bus_id_k)
            fp += Vk*(Gik*cos(thetai - thetak) - Bik*sin(thetai - thetak))
            if bus.has_generator_attached() is False:
                fq += Vk*(Gik*sin(thetai - thetak) + Bik*cos(thetai - thetak))
        fp = fp*Vi - Pnet
        if bus.has_generator_attached() is False:
            fq = fq*Vi - Qnet
        
        # if bus_id_i in [7, 10, 12]:
            # embed()
        
        return fp, fq
                
    
    def generate_jacobian_matrix(self):
        # run this to ensure that admittance matrix is generated, but don't actually need it in a local var
        _, _ = self.get_admittance_matrix()
        
        admittance_matrix_index_bus_id_mapping = self.admittance_matrix_index_bus_id_mapping
        slack_bus_id = self.get_slack_bus_id()
        
        J, list_of_bus_id_lists = frompyfunc(self._jacobian_diagonal_helper, 1, 2)(admittance_matrix_index_bus_id_mapping)
        J = diags(hstack(J), 0, format='lil')
        # J = diag(hstack(J))
        
        jacobian_matrix_index_bus_id_mapping = [int(bus_id) for bus_id in hstack(list_of_bus_id_lists).tolist() if bus_id is not None]
        
        n = len(jacobian_matrix_index_bus_id_mapping)

        i = 0
        while i < n:
            bus_id_i = jacobian_matrix_index_bus_id_mapping[i]
            bus_i = self.get_bus_by_id(bus_id_i)
            connected_bus_ids = self.get_all_connected_bus_ids_by_id(bus_id_i)
            Vi_polar = bus_i.get_current_node_voltage()
            bus_i_has_generator = bus_i.has_generator_attached()
            j = 0
            while j < n:
                if i == j:
                    if bus_i_has_generator is False:
                        J[i+1, j] = self._jacobian_kii_helper(bus_id_i, Vi_polar, connected_bus_ids)
                        J[i, j+1] = self._jacobian_nii_helper(bus_id_i, Vi_polar, connected_bus_ids, Kii=J[i+1, j])
                        j += 1
                else:
                    bus_id_j = jacobian_matrix_index_bus_id_mapping[j]
                    if bus_id_j in connected_bus_ids and self.is_slack_bus_by_id(bus_id_j) is False:
                        Gij, Bij = self.get_admittance_value_from_bus_ids(bus_id_i, bus_id_j)
                        bus_j = self.get_bus_by_id(bus_id_j)
                        Vj_polar = bus_j.get_current_node_voltage()

                        J[i, j] = self._jacobian_hij_helper(Vi_polar, Vj_polar, Gij, Bij)


                        if bus_i_has_generator is False:
                            J[i+1, j] = self._jacobian_kij_helper(Vi_polar, Vj_polar, Gij, Bij)

                        if bus_j.has_generator_attached() is False:
                            if bus_i_has_generator is False:
                                J[i+1, j+1] = self._jacobian_lij_helper(Vi_polar, Vj_polar, Gij, Bij, J[i, j])
                                Kij = J[i+1, j]
                            else:
                                Kij = None
                            J[i, j+1] = self._jacobian_nij_helper(Vi_polar, Vj_polar, Gij, Bij, Kij)
                            j += 1
                j += 1
                    
            if bus_i_has_generator is False:
                i += 1
            i += 1
        
        return J

    
    def _jacobian_diagonal_helper(self, bus_id):
        bus = self.get_bus_by_id(bus_id)
        if self.is_slack_bus(bus) is True:
            return [], []

        Vi_polar = bus.get_current_node_voltage()
        connected_bus_ids = self.get_all_connected_bus_ids_by_id(bus_id)

        Hii = self._jacobian_hii_helper(bus_id, Vi_polar, connected_bus_ids)
        
        diag_elements = [Hii]
        jacobian_indices = [bus_id]

        if bus.has_generator_attached() is False:
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
        if False: # if Lii is not None:
            _, Bii = self.get_admittance_value_from_bus_ids(bus_id_i, bus_id_i)
            Qneti = self._get_qneti(Bii, Vi, Lii=Lii)
            return Bii*Vi**2 - Qneti
        else:
            Hii = 0
            for bus_id_k in connected_bus_ids:
                bus_k = self.get_bus_by_id(bus_id_k)
                Vk, thetak = bus_k.get_current_node_voltage()
                Gik, Bik = self.get_admittance_value_from_bus_ids(bus_id_i, bus_id_k)
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
        Gii, _ = self.get_admittance_value_from_bus_ids(bus_id_i, bus_id_i)
        if False: # if Kii is not None:
            Pneti = self._get_pneti(Gii, Vi, Kii=Kii)
            return Gii*Vi + Pneti/Vi
        else:
            Nii = 2*Gii*Vi
            for bus_id_k in connected_bus_ids:
                bus_k = self.get_bus_by_id(bus_id_k)
                Vk, thetak = bus_k.get_current_node_voltage()
                Gik, Bik = self.get_admittance_value_from_bus_ids(bus_id_i, bus_id_k)
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
        if False: #if Nii is not None:
            Gii, _ = self.get_admittance_value_from_bus_ids(bus_id_i, bus_id_i)
            Pneti = self._get_pneti(Gii, Vi, Nii=Nii)
            return -1*Gii*Vi**2 + Pneti
        else:
            Kii = 0
            for bus_id_k in connected_bus_ids:
                bus_k = self.get_bus_by_id(bus_id_k)
                Vk, thetak = bus_k.get_current_node_voltage()
                Gik, Bik = self.get_admittance_value_from_bus_ids(bus_id_i, bus_id_k)
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
        _, Bii = self.get_admittance_value_from_bus_ids(bus_id_i, bus_id_i)
        Vi, thetai = Vi_polar
        if False: #if Hii is not None:
            Qneti = self._get_qneti(Bii, Vi, Hii=Hii)
            return Bii*Vi + Qneti/Vi
        else:
            Lii = 2*Bii*Vi

            for bus_id_k in connected_bus_ids:
                bus_k = self.get_bus_by_id(bus_id_k)
                Vk, thetak = bus_k.get_current_node_voltage()
                Gik, Bik = self.get_admittance_value_from_bus_ids(bus_id_i, bus_id_k)
                Lii += Vk*(Gik*sin(thetai - thetak) + Bik*cos(thetai - thetak))
            return Lii

    
    # @staticmethod
    def _get_pneti(self, Gii, Vi, Nii=None, Kii=None):
        if Nii is not None:
            return Vi*(Nii-Gii*Vi)
        elif Kii is not None:
            return Gii*Vi**2 + Kii
        return None

    
    # @staticmethod
    def _get_qneti(self, Bii, Vi, Hii=None, Lii=None):
        if Hii is not None:
            return Bii*Vi**2 - Hii
        elif Lii is not None:
            return Vi*(Lii - Bii*Vi)
        return None
        

    def nr(self, tolerance=0.0001):
        fx = self.generate_function_vector()
        while True:
            J = csr_matrix(self.generate_jacobian_matrix())
            x = self.get_current_voltage_vector()
            x_next = x - spsolve(J, fx)
            self.update_voltage_vector(x_next)
            fx = self.generate_function_vector()
            error = norm(fx, inf)
            if error < tolerance:
                break
        return x_next
