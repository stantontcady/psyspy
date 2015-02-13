import unittest

from numpy import array, asarray, matrix, genfromtxt
from numpy.testing import assert_array_equal, assert_array_almost_equal
from scipy.sparse import lil_matrix

from microgrid_model import Bus, PowerLine, PowerNetwork, PQBus, PVBus
# from ..microgrid_model import NodeError, PowerLineError, PowerNetworkError


def create_wecc_9_bus_network(set_slack_bus=True):

    b1 = PVBus(P=0.716, V=1.04, theta0=0)
    b2 = PVBus(P=1.63, V=1.025)
    b3 = PVBus(P=0.85, V=1.025)
    b4 = Bus(shunt_y=(0, 0.5*0.176 + 0.5*0.158))
    b5 = PQBus(P=1.25, Q=0.5, shunt_y=(0, 0.5*0.176 + 0.5*0.306))
    b6 = PQBus(P=0.9, Q=0.3, shunt_y=(0, 0.5*0.158 + 0.5*0.358))
    b7 = Bus(shunt_y=(0, 0.5*0.306 + 0.5*0.149))
    b8 = PQBus(P=1, Q=0.35, shunt_y=(0, 0.5*0.149 + 0.5*0.209))
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

    if set_slack_bus is True:
        n.set_slack_bus(b1)
    return n
    
def create_wecc_9_bus_network_with_pq_buses():

    b1 = PVBus(P=0.716, V=1.04, theta0=0)
    b2 = PVBus(P=1.63, V=1.025)
    b3 = PVBus(P=0.85, V=1.025)
    b4 = Bus(shunt_y=(0, 0.5*0.176 + 0.5*0.158))
    b5 = PQBus(P=1.25, Q=0.5, shunt_y=(0, 0.5*0.176 + 0.5*0.306))
    b6 = PQBus(P=0.9, Q=0.3, shunt_y=(0, 0.5*0.158 + 0.5*0.358))
    b7 = Bus(shunt_y=(0, 0.5*0.306 + 0.5*0.149))
    b8 = PQBus(P=1, Q=0.35, shunt_y=(0, 0.5*0.149 + 0.5*0.209))
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
    
    def test_node_functions(self):
        def series_of_tests(object_to_test):
            def assert_voltage_equal(expected_voltage, actual_voltage=None):
                if actual_voltage is None:
                    actual_voltage_magnitude, actual_voltage_angle = object_to_test.get_current_voltage_polar()
                
                expected_voltage_magnitude, expected_voltage_angle = expected_voltage
                
                self.assertEqual(expected_voltage_magnitude, actual_voltage_magnitude)
                self.assertEqual(expected_voltage_angle, actual_voltage_angle)

            # initial conditions should be V=1, theta=0
            expected_test_voltage = (1, 0)
            assert_voltage_equal(expected_test_voltage)
            
            expected_test_voltage = (1.2, 0.1)
            _, _ = object_to_test.update_voltage_polar((1.2, 0.1), replace=True)
            assert_voltage_equal(expected_test_voltage)
            
            expected_test_voltage = (1.1, 0.053)
            _, _ = object_to_test.update_voltage_polar((1.1, 0.053))
            assert_voltage_equal(expected_test_voltage)
        
        # node = Node()
        # also want to test that Bus inherits these methods properly
        bus = Bus()
        
        # series_of_tests(node)
        series_of_tests(bus)
        
        
    def test_bus_functions(self):
        bus = Bus()
        
        # initial conditions should be V=1, theta=0
        actual_voltage_magnitude, actual_voltage_angle = bus.get_current_voltage_polar()
        expected_voltage_magnitude = 1
        expected_voltage_angle = 0
        self.assertEqual(expected_voltage_magnitude, actual_voltage_magnitude)
        self.assertEqual(expected_voltage_angle, actual_voltage_angle)
        
        
        expected_voltage_magnitude = array([1, 1.15])
        expected_voltage_angle = array([0, 0.02])
        _, _ = bus.update_voltage_polar((1.15, 0.02), replace=False)
        assert_array_equal(expected_voltage_magnitude, bus.V)
        assert_array_equal(expected_voltage_angle, bus.theta)
        
        expected_voltage_magnitude = array([1, 1.15, 1.12])
        _ = bus.update_voltage_magnitude(1.12, replace=False)
        assert_array_equal(expected_voltage_magnitude, bus.V)
        
        expected_voltage_angle = array([0, 0.02, 0.034])
        _ = bus.update_voltage_angle(0.034, replace=False)
        assert_array_equal(expected_voltage_angle, bus.theta)
        
        expected_voltage_magnitude = array([1, 1.15, 1.14])
        _ = bus.update_voltage_magnitude(1.14, replace=True)
        assert_array_equal(expected_voltage_magnitude, bus.V)
        
        expected_voltage_angle = array([0, 0.02, 0.023])
        _ = bus.update_voltage_angle(0.023, replace=True)
        assert_array_equal(expected_voltage_angle, bus.theta)
        
        bus.reset_voltage_to_unity_magnitude_zero_angle()
        expected_voltage_magnitude = array([1])
        expected_voltage_angle = array([0])
        assert_array_equal(expected_voltage_magnitude, bus.V)
        assert_array_equal(expected_voltage_angle, bus.theta)

    
    def test_generate_admittance_matrix(self):
        expected_G = genfromtxt('tests/resources/wecc9_conductance_matrix.csv', delimiter=',')
        expected_B = genfromtxt('tests/resources/wecc9_susceptance_matrix.csv', delimiter=',')
        expected_G_optimal = genfromtxt('tests/resources/wecc9_conductance_matrix_optimal_ordering.csv', delimiter=',')
        expected_B_optimal = genfromtxt('tests/resources/wecc9_susceptance_matrix_optimal_ordering.csv', delimiter=',')

        network = create_wecc_9_bus_network()

        actual_G, actual_B = network.generate_admittance_matrix(optimal_ordering=False)

        actual_G = asarray(actual_G.todense())
        actual_B = asarray(actual_B.todense())
        
        assert_array_almost_equal(actual_G, expected_G, 8)
        assert_array_almost_equal(actual_B, expected_B, 8)

        actual_G_optimal, actual_B_optimal = network.generate_admittance_matrix(optimal_ordering=True)

        actual_G_optimal = asarray(actual_G_optimal.todense())
        actual_B_optimal = asarray(actual_B_optimal.todense())

        assert_array_almost_equal(actual_G_optimal, expected_G_optimal, 8)
        assert_array_almost_equal(actual_B_optimal, expected_B_optimal, 8)

        
    def test_generate_jacobian_matrix(self):
        expected_J = genfromtxt('tests/resources/wecc9_jacobian_matrix.csv', delimiter=',')
        expected_J_optimal = genfromtxt('tests/resources/wecc9_jacobian_matrix_optimal_ordering.csv', delimiter=',')

        network = create_wecc_9_bus_network()

        _, _ = network.save_admittance_matrix(optimal_ordering=False)

        actual_J = network._generate_jacobian_matrix()
        actual_J = asarray(actual_J.todense())

        assert_array_almost_equal(actual_J, expected_J, 8)

        _, _ = network.save_admittance_matrix()

        actual_J_optimal = network._generate_jacobian_matrix()
        actual_J_optimal = asarray(actual_J_optimal.todense())


        assert_array_almost_equal(actual_J_optimal, expected_J_optimal, 8)


    def test_solve_power_flow(self):
        def do_test(network_to_test):
            actual_final_states = network_to_test.solve_power_flow(optimal_ordering=False)
            assert_array_almost_equal(actual_final_states, expected_final_states, 8)
            
            network_to_test.reset_voltages_to_flat_profile()
            
            actual_final_states_optimal_ordering = network_to_test.solve_power_flow(optimal_ordering=True)

            assert_array_almost_equal(actual_final_states_optimal_ordering, expected_final_states_optimal_ordering, 8)
            
        network0 = create_wecc_9_bus_network()
        network1 = create_wecc_9_bus_network_with_pq_buses()

        expected_final_states = genfromtxt('tests/resources/wecc9_final_states.csv', delimiter=',')
        expected_final_states_optimal_ordering = genfromtxt('tests/resources/wecc9_final_states_optimal_ordering.csv',
                                                            delimiter=',')
        
        do_test(network0)
        do_test(network1)


    # def test_exceptions(self):
    #     network = create_wecc_9_bus_network(set_slack_bus=False)
    #
    #     self.assertRaises(PowerNetworkError, network.get_slack_bus_id)
    #     self.assertRaises(PowerNetworkError, network._compute_and_save_line_power_flows, None)
    #     self.assertRaises(PowerNetworkError, network.get_admittance_matrix_index_bus_id_mapping)
    #     self.assertRaises(PowerNetworkError, network.get_admittance_matrix)
    #
    #     line = PowerLine()
    #     self.assertRaises(PowerLineError, line.get_incident_buses)
    #
    #     self.assertRaises(NodeError, Bus, [])
        
    
if __name__ == '__main__':
    unittest.main()
