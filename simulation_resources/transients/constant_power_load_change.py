from itertools import count

from .load_change import TemporaryLoadChange


class TemporaryConstantPowerLoadChange(TemporaryLoadChange):
    _temporary_constant_power_load_change_ids = count(0)
    
    def __init__(self, start_time, end_time, affected_node, new_P=None, new_Q=None):
        
        # check for constant power load change specific errors before calling super class init
        if new_P is None and new_Q is None:
            raise StandardError('A new real or reactive power must be specified for constant power load change')
            
        # the load change class expects an object of type node, not bus, but it may be possible to extract the node from the bus if there's only one node attached to the bus
        if (affected_node.get_node_type() == 'bus') and (len(affected_node.child_nodes) == 1):
            # if node passed in is actually a bus but it only has one child node, change affected target
            affected_node = affected_node.child_nodes[0]
            
        if affected_node.get_node_type() != 'constant_power_load':
            raise TypeError('Node type must be constant power load')
            
        TemporaryLoadChange.__init__(self, start_time, end_time, affected_node)
            
        old_P, old_Q = self.affected_node.get_real_and_reactive_power()
        
        if old_P == new_P and old_Q == new_Q:
            print 'New real and reactive powers are identical to current values for this node, this change will be disabled'
            self.enabled = False
            
        self.new_P = new_P
        self.new_Q = new_Q
        
        self.old_P = old_P
        self.old_Q = old_Q
        
        self._temporary_constant_power_load_change_id = self._temporary_constant_power_load_change_ids.next() + 1
        
        self._change_type = 'temporary_constant_power_load_change'
        

    def toggle_change(self):
        if self.enabled is True:
            if self.active is False:
                self.activate()
                self.active = True
            else:
                self.deactivate()
                self.active = False


    def activate(self):
         if self.enabled is True:
            if self.new_P is not None:
                _ = self.affected_node.change_real_power(self.new_P)
            if self.new_Q is not None:
                _ = self.affected_node.change_reactive_power(self.new_Q)
            self.active = True
            print 'Activated'
    
    
    def deactivate(self):
        if self.enabled is True:
            if self.old_P is not None:
                _ = self.affected_node.change_real_power(self.old_P)
            if self.old_Q is not None:
                _ = self.affected_node.change_reactive_power(self.old_Q)
            self.active = False
            print 'Deactivated'
