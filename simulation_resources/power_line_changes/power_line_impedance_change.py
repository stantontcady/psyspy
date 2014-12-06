from itertools import count

from .power_line_change import PowerLineChange
from model_components import impedance_admittance_wrangler


class PowerLineImpedanceChange(PowerLineChange):
    _power_line_impedance_change_ids = count(0)
    
    def __init__(self, affected_line, start_time, end_time, new_z=(), new_y=()):
        
        # check for constant power line impedance change-specific errors before calling super class init
        if new_z == () and new_y == ():
            raise StandardError('A new reacatance or admittance must be specified for power line impedance change')
        
        PowerLineChange.__init__(self, affected_line, start_time, end_time)
        
        try:
            old_y = self.affected_line.y
        except ValueError:
            raise TypeError('Node type must be constant power load')
            
        new_y = impedance_admittance_wrangler(new_z, new_y)
        
        if old_y == new_y:
            print 'New admittances are identical to current values for this power line, this change will be disabled'
            self.enabled = False
            
        self.new_y = new_y
        
        self.old_y = old_y
        
        self._power_line_impedance_change_id = self._power_line_impedance_change_ids.next() + 1
        
        self._change_type = 'power_line_impedance_change'
        
        self.admittance_matrix_change = True


    def activate(self):
         if self.enabled is True:
             self.affected_line.y = self.new_y
             self.active = True
             print 'Activated'
    
    
    def deactivate(self):
        if self.enabled is True:
            self.affected_line.y = self.old_y
            self.active = False
            print 'Deactivated'
