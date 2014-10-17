import unittest

from numpy import array, asarray, matrix, genfromtxt
from numpy.testing import assert_array_equal, assert_array_almost_equal
from scipy.sparse import lil_matrix

from model_components import Bus, ConstantPowerLoad, PowerLine, PowerNetwork, PVBus, SynchronousDGR


def create_wecc_9_bus_network():
    la = ConstantPowerLoad(P=1.25, Q=0.5) # Station A
    lb = ConstantPowerLoad(P=0.9, Q=0.3) # Station B
    lc = ConstantPowerLoad(P=1, Q=0.35) # Station C

    b1 = PVBus(P=0.716, V=1.04, theta0=0)
    b2 = PVBus(P=1.63, V=1.025)
    b3 = PVBus(P=0.85, V=1.025)
    b4 = Bus(shunt_y=(0, 0.5*0.176 + 0.5*0.158))
    b5 = Bus(nodes=la, shunt_y=(0, 0.5*0.176 + 0.5*0.306))
    b6 = Bus(nodes=lb, shunt_y=(0, 0.5*0.158 + 0.5*0.358))
    b7 = Bus(shunt_y=(0, 0.5*0.306 + 0.5*0.149))
    b8 = Bus(nodes=lc, shunt_y=(0, 0.5*0.149 + 0.5*0.209))
    b9 = Bus(shunt_y=(0, 0.5*0.358 + 0.5*0.209))

    n = PowerNetwork(buses=[b1, b2, b3, b4, b5, b6, b7, b8, b9])

    line1 = n.connect_buses(b1, b4, z=(0, 0.0576))
    line4 = n.connect_buses(b4, b5, z=(0.01, 0.085))
    line6 = n.connect_buses(b5, b7, z=(0.032, 0.161))
    line5 = n.connect_buses(b4, b6, z=(0.017, 0.092))
    line7 = n.connect_buses(b6, b9, z=(0.039, 0.17))
    line8 = n.connect_buses(b7, b8, z=(0.0085, 0.072))
    line3 = n.connect_buses(b3, b9, z=(0, 0.0586))
    line9 = n.connect_buses(b8, b9, z=(0.0119, 0.1008))
    line2 = n.connect_buses(b2, b7, z=(0, 0.0625))


    n.set_slack_bus(b1)
    return n

class TestPowerNetwork(unittest.TestCase):
    
    def test_generate_admittance_matrix(self):
        network = create_wecc_9_bus_network()
        expected_G = genfromtxt('resources/tests/wecc9_conductance.csv', delimiter=',')
        
        expected_B = genfromtxt('resources/tests/wecc9_susceptance.csv', delimiter=',')
             
        actual_G, actual_B, _ = network.generate_admittance_matrix()
        actual_G = asarray(actual_G.todense())
        actual_B = asarray(actual_B.todense())
        
        assert_array_almost_equal(actual_G, expected_G, 8)
        
    def test_generate_jacobian_matrix(self):
        expected_J = genfromtxt('resources/tests/wecc9_jacobian.csv', delimiter=',')

        network = create_wecc_9_bus_network()
        actual_J = network.generate_jacobian_matrix()
        actual_J = asarray(actual_J.todense())
        
        assert_array_almost_equal(actual_J, expected_J, 8)
    
if __name__ == '__main__':
    unittest.main()