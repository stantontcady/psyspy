import unittest

from numpy import array, asarray, matrix
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
        expected_G = array(
            [[ 0., 0., 0., 0., 0., 0., 0., 0., 0.],
             [ 0., 0., 0., 0., 0., 0., 0., 0., 0.],
             [ 0., 0., 0., 0., 0., 0., 0., 0., 0.],
             [ 0., 0., 0., 3.30737896, -1.36518771, -1.94219125, 0., 0., 0.],
             [ 0., 0., 0.,-1.36518771, 2.55279209, 0., -1.18760438, 0., 0.],
             [ 0., 0., 0.,-1.94219125, 0., 3.22420039, 0., 0., -1.28200914],
             [ 0., 0., 0., 0., -1.18760438, 0., 2.80472685, -1.61712247, 0.],
             [ 0., 0., 0., 0., 0., 0., -1.61712247, 2.77220995, -1.15508748],
             [ 0., 0., 0., 0., 0., -1.28200914, 0., -1.15508748, 2.43709662]])
        
        expected_B = array(
            [[ 17.36111111, 0., 0., -17.36111111, 0., 0., 0., 0., 0.],
             [ 0., 16., 0., 0., 0., 0., -16., 0., 0.],
             [ 0., 0., 17.06484642, 0., 0., 0., 0., 0., -17.06484642],
             [-17.36111111, 0., 0., 39.30888873, -11.60409556, -10.51068205, 0., 0., 0.],
             [ 0., 0., 0., -11.60409556, 17.3382301, 0., -5.97513453, 0., 0.],
             [ 0., 0., 0., -10.51068205, 0., 15.84092701, 0., 0., -5.58824496],
             [ 0., -16., 0., 0., -5.97513453, 0., 35.44561313, -13.6979786, 0.],
             [ 0., 0., 0., 0., 0., 0., -13.6979786, 23.30324902, -9.78427043],
             [ 0., 0., -17.06484642, 0., 0., -5.58824496, 0., -9.78427043, 32.15386181]])
             
        actual_G, actual_B, _ = network.generate_admittance_matrix()
        actual_G = asarray(actual_G.todense())
        actual_B = asarray(actual_B.todense())
        
        assert_array_almost_equal(actual_G, expected_G, 8)
    
if __name__ == '__main__':
    unittest.main()