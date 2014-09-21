from bus import Bus
from synchronous_dgr import synchronous_generator
from IPython import embed

g1 = synchronous_generator()
g2 = synchronous_generator()
g3 = synchronous_generator()


b1 = Bus(nodes=[g1, g2])
b2 = Bus(nodes=[g3])

embed()