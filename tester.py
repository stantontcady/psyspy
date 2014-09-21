from bus import Bus
from power_line import PowerLine
from power_network import PowerNetwork
from synchronous_dgr import SynchronousDGR
from IPython import embed

g1 = SynchronousDGR()
g2 = SynchronousDGR()
g3 = SynchronousDGR()


b1 = Bus(nodes=[g1, g2])
b2 = Bus(nodes=[g3])
b3 = Bus()

n = PowerNetwork(buses=[b1,b2])
n.connect_buses(b1, b2, r=0.1, b=0.25)

n.add_bus(b3)
l1 = PowerLine(b1, b3, r=0.05, b=0.1)
n.add_power_line(l1)


embed()