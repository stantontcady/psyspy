from itertools import count
from operator import itemgetter

from numpy import zeros
from scipy.sparse import lil_matrix

from power_line import PowerLine

from IPython import embed

class PowerNetwork(object):
    
    def __init__(self, buses=[], power_lines=[]):
        self.buses = []
        self.buses.extend(buses)
        self.power_lines = []
        self.power_lines.extend(power_lines)
        
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
        print bus_info

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
        if power_line.bus_a.get_id() == bus.get_id():
            return power_line.bus_b.get_id()
        elif power_line.bus_b.get_id() == bus.get_id():
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
            connected_bus_id = self.get_connected_bus_id(self.get_bus_by_id(bus_id), power_line)
            if connected_bus_id is not None:
                connected_bus_ids.append(connected_bus_id)
                power_line_ids.append(power_line.get_id())
        return power_line_ids, connected_bus_ids
    

    def generate_admittance_matrix(self):
        n = len(self.buses)
        G = zeros([n,n], dtype=float)
        B = zeros([n,n], dtype=float)
        for bus in self.buses:
            i = bus.get_id() - 1
            for incident_power_line_id in self.get_incident_power_line_ids_by_id(bus.get_id()):
                incident_power_line = self.get_power_line_by_id(incident_power_line_id)
                j = self.get_connected_bus_id(bus, incident_power_line) - 1
                (gj, bj) = incident_power_line.y
                G[i, i] += gj
                B[i, i] += bj
                G[i, j] = -gj
                B[i, j] = -bj
            (gi, bi) = bus.shunt_y
            G[i, i] += gi
            B[i, i] += bi
            i += 1
        
        return lil_matrix(G), lil_matrix(B)
        