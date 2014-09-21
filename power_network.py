from itertools import count

from bus import Bus
from power_line import PowerLine
from synchronous_dgr import SynchronousDGR

class PowerNetwork(object):
    
    def __init__(self, buses=[], power_lines=[]):
        self.buses = []
        self.buses.extend(buses)
        self.power_lines = []
        self.power_lines.extend(power_lines)
        
    def add_bus(self, bus):
        self.buses.append(bus)
    
    def add_power_line(self, power_line):
        self.power_lines.append(power_line)
        
    def connect_buses(self, bus_a, bus_b, r=None, x=None, g=None, b=None):
        if self.bus_in_network(bus_a) is False:
            self.add_bus(bus_a)
        if self.bus_in_network(bus_b) is False:
            self.add_bus(bus_b)
        
        power_line = PowerLine(bus_a, bus_b, r, x, g, b)
        self.add_power_line(power_line)
    
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
            
    def generate_admittance_matrix(self):
        pass