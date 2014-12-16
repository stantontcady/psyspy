#PowerPy#

PowerPy is a full-fledged dynamic power system simulator written completely in Python; it is capable of simulating both static and dynamic operation of an *n*-bus power system.  While it was written with the intention of simulating microgrids, i.e., systems with a relatively small number of buses, it was flexibly designed and should therefore be suitable for systems of any size.

PowerPy can perform both static, i.e., power flow, and dynamic simulations.  The dynamic simulator represents the system using a dynamic algebraic equation model where the default generator model is the structure-preserving model with constant complex voltage behind reactance.  For a detailed explanation of the model and simulation methodology, please see this document.

##Modeling a Power Network##
PowerPy was designed to allow for intuitive, yet powerful representations of power networks.  A multi-level object-oriented approach is used to represent a power system and its components.  Each component is discussed below, where the lowest-level object is discussed first.

###Node###
The most basic component in a PowerPy power network is the node.  It has many low-level methods that are shared among higher-level objects.  Additionally, it has two properties: *V* and *theta* which correspond to the voltage magnitude and angle at the node.  While the *Node* object is the most basic object, it is discussed here to illustrate the hierarchy among the model components in PowerPy and should not be used as a standalone object.

###Bus###
While *Node* is the most basic object in PowerPy, *Bus* is the most basic object that is used during a simulation.  When creating an instance of the *Bus* class, one can include a dynamic generator (dgr), a load or list of loads, an initial voltage magnitude and angle, and a shunt impedance or admittance.  All of these arguments are optional as illustrated by the code below.

```python
b = Bus(dgr=None, loads=None, V0=None, theta0=None, shunt_z=(), shunt_y=())
```

A few things to note about creating an instance of the Bus class:

* The dynamic generator (dgr) must be of type *DGR* or of a type derived from the DGR superclass. The *DGR* type is discussed in-depth later.
* The loads argument can be a single load or a list of loads.  In either case, it must be an object of type *Load* or a list of *Load* objects (objects for which the *Load* class is a superclass are also okay). The *Load* type is discussed later.
* If an initial voltage magnitude and angle are provided and they do not match the initial values stored in the dgr and/or load(s) objects will be overwritten.  If no initial voltage is supplied the initial magnitude and angle of the dgr or load(s) in will be inherited with the dgr taking precedence over the loads, and the values from the first load in the list taking precedence over all others.
* If both a shunt admittance and impedance are provided, the admittance value takes precedence (internally only the admittance is stored, so the impedance is converted before storing).

##Static Simulation##
PowerPy is capable of performing static 
