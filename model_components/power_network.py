from itertools import count
from operator import itemgetter
from math import sin, cos

from numpy import append, array, zeros, frompyfunc, hstack, diagflat, set_printoptions
from scipy.sparse import lil_matrix

from power_line import PowerLine

from IPython import embed

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

    
    def get_bus_by_id(self, bus_id):
        for bus in self.buses:
            if bus.get_id() == bus_id:
                return bus
    
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
                (gj, bj) = incident_power_line.y
                G[i, i] += gj
                B[i, i] += bj
                G[i, j] = -gj
                B[i, j] = -bj
            (gi, bi) = bus_i.shunt_y
            G[i, i] += gi
            B[i, i] += bi    
                
        
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
        
        
    def is_slack_bus(self, bus):
        try:
            if bus.get_id() == self.slack_bus_id:
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
        
        
    def get_admittance_matrix_index_from_bus_id(self, bus_id_to_find):
        try:
            admittance_matrix_index_bus_id_mapping = self.admittance_matrix_index_bus_id_mapping
        except AttributeError:
            _, _, admittance_matrix_index_bus_id_mapping = self.generate_admittance_matrix()

        try:
            index_of_bus_id = admittance_matrix_index_bus_id_mapping.index(bus_id_to_find)
        except ValueError:
            index_of_bus_id = None
        
        return index_of_bus_id
        
        
    def get_admittance_value_from_bus_ids(self, bus_id_i, bus_id_j):
        i = self.get_admittance_matrix_index_from_bus_id(bus_id_i)
        j = self.get_admittance_matrix_index_from_bus_id(bus_id_j)
        if i is None or j is None:
            return None

        G, B = self.get_admittance_matrix()
        
        return G[i, j], B[i, j]
        
        
    def get_current_voltage_vector(self):
        self.select_slack_bus()
        self.save_admittance_matrix_bus_id_index_mapping()
        state_vector = array([])
        for bus_id in self.bus_admittance_matrix_id_index_mapping:
            bus = self.get_bus_by_id(bus_id)
            if self.is_slack_bus(bus) is True:
                continue
            V, theta = bus.get_current_node_voltage()
            state_vector = append(state_vector, [theta])
            if bus.has_generator_attached() is True:
                state_vector = append(state_vector, [V])

        return state_vector
                
    
    def generate_jacobian_matrix(self):
        # run this to ensure that admittance matrix is generated, but don't actually need it in a local var
        _, _ = self.save_admittance_matrix()
        
        admittance_matrix_index_bus_id_mapping = self.admittance_matrix_index_bus_id_mapping
        slack_bus_id = self.select_slack_bus()
        
        J, list_of_bus_id_lists = frompyfunc(self._jacobian_diagonal_helper, 1, 2)(admittance_matrix_index_bus_id_mapping)
        
        J = diagflat(hstack(J))
        # J is square, okay to take either element of shape
        n = J.shape[0]
        jacobian_matrix_index_bus_id_mapping = [int(bus_id) for bus_id in hstack(list_of_bus_id_lists).tolist() if bus_id is not None]

        i = 0
        while i < n:
            bus_id_i = jacobian_matrix_index_bus_id_mapping[i]
            connected_bus_ids = self.get_all_connected_bus_ids_by_id(bus_id_i)
            bus_i = self.get_bus_by_id(bus_id_i)
            Vi_polar = bus_i.get_current_node_voltage()
            bus_i_has_generator = bus_i.has_generator_attached()
            j = 0
            while j < n:
                if i == j:
                    if bus_i_has_generator is False:
                        J[i+1, j] = self._jacobian_kii_helper(bus_id_i)
                        J[i, j+1] = self._jacobian_nii_helper(bus_id_i)
                        j += 1
                else:
                    bus_id_j = jacobian_matrix_index_bus_id_mapping[j]
                    if bus_id_j in connected_bus_ids:
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
            diag_elements.append(self._jacobian_lii_helper(bus_id, Vi_polar, Hii))
            jacobian_indices.append(bus_id)
            
        return diag_elements, jacobian_indices
        
            
    def _jacobian_hij_helper(self, Vi_polar, Vj_polar, Gij, Bij, Lij=None):
        Vj, thetaj = Vj_polar
        if Lij is not None:
            return Lij*Vj
        else:
            Vi, thetai = Vi_polar
            return Vi*Vj*(Gij*sin(thetai - thetaj) + Bij*cos(thetai - thetaj))

        
    def _jacobian_hii_helper(self, i, Vi_polar, connected_bus_ids):
        # Hii = 0
        # Vi, thetai = Vi_polar
        # for k in connected_bus_ids:
        #     bus_k = self.get_bus_by_id(k)
        #     Vk, thetak = bus_k.get_current_node_voltage()
        #     Gik, Bik = self.get_admittance_value_from_bus_ids(i, bus_k.get_id())
        #     Hii += Vk*Gik*sin(thetai - thetak) + Bik*cos(thetai - thetak)
        
        # return -1*Vi*Hii
        return 0
        # return 'H%i%i' % (i-1, i-1)


    def _jacobian_nij_helper(self, Vi_polar, Vj_polar, Gij, Bij, Kij=None):
        Vj, thetaj = Vj_polar
        if Kij is not None:
            return -1*Kij/Vj
        else:
            Vi, thetai = Vi_polar
            return Vi*(Gij*cos(thetai - thetaj) - Bij*sin(thetai - thetaj))
        
        
    def _jacobian_nii_helper(self, i): # , Vi_polar, connected_bus_ids
        # return 'N%i%i' % (i-1, i-1)
        return 0
        

    def _jacobian_kij_helper(self, Vi_polar, Vj_polar, Gij, Bij, Nij=None):
        Vj, thetaj = Vj_polar
        if Nij is not None:
            return -1*Nij*Vj
        else:
            Vi, thetai = Vi_polar
            return -1*Vi*Vj*(Gij*cos(thetai - thetaj) - Bij*sin(thetai - thetaj))
        
    
    def _jacobian_kii_helper(self, i): # , Vi_polar, connected_bus_ids
        return 0
        # return 'K%i%i' % (i-1, i-1)
        # Kii = 0
        # Vi, thetai = Vi_polar
        # for k in connected_bus_ids:
        #     bus_k = self.get_bus_by_id(k)
        #     Vk, thetak = bus_k.get_current_node_voltage()
        #     # Hii += Vk*G[]*sin(thetai - thetak) + B[]*cos(thetai - thetak)
        # return -1*Vi*Hii
        
    
    def _jacobian_lij_helper(self, Vi_polar, Vj_polar, Gij, Bij, Hij=None):
        Vj, thetaj = Vj_polar
        if Hij is not None:
            return Hij/Vj
        else:
            Vi, thetai = Vi_polar
            return Vi*(Gij*sin(thetai - thetaj) + bij*cos(thetai - thetaj))
        
    
    def _jacobian_lii_helper(self, i, Vi_polar, Hii):
        return 0
        # _, Bii = self.get_admittance_value_from_bus_ids(i, i)
        # Vi, _ = Vi_polar
        #
        # Qneti = Bii*Vi**2 - Hii
        
        # return Bii*Vi + Qneti/Vi
        # return 'L%i%i' % (i-1, i-1)
        
        
        # Lii = 2*Bii*Vi
        #
        # for k in connected_bus_ids:
        #     bus_k = self.get_bus_by_id(k)
        #     Vk, thetak = bus_k.get_current_node_voltage()
        #     Gik, Bik = self.get_admittance_value_from_bus_ids(i, bus_k.get_id())
        #     Lii += Vk*Gik*sin(thetai - thetak) + Bik*cos(thetai - thetak)
        # return -1*Vi*Hii
    