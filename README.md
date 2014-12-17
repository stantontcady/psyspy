#PowerPy#

PowerPy is a full-fledged dynamic power system simulator written completely in Python; it is capable of simulating both static and dynamic operation of an *n*-bus power system.  While it was written with the intention of simulating microgrids, i.e., systems with a relatively small number of buses, it was flexibly designed and should therefore be suitable for systems of any size.

For dynamic simulations, PowerPy represents the system using a dynamic algebraic equation model where the default generator model is the structure-preserving model with constant complex voltage behind reactance.  For a detailed explanation of the model and simulation methodology, please see this document.

##Modeling a Power Network##
PowerPy was designed to allow for intuitive, yet powerful representations of power networks.  A multi-level object-oriented approach is used to represent a power system and its components.  Each component is discussed below, with the lowest-level object discussed first.

###Node###
The most basic component in a PowerPy power network is the node.  It has many low-level methods that are shared among higher-level objects.  Additionally, it has two properties: *V* and *theta* which correspond to the voltage magnitude and angle at the node.  While the *Node* object is the most basic component, it is discussed here strictly to illustrate the hierarchy among the model components in PowerPy and should not be used as a standalone object.

An example node instantiation with the default arguments is shown below; note that if the initial voltage magnitude and angle are omitted, they will be defaulted to *V0*=1 per unit and *theta0*=0 radians (these defaults are also true for all objects that are derived from the *Node* class).

```python
n = Node(V0=None, theta0=None)
```

###Bus###
While *Node* is the most basic object in PowerPy, *Bus* is the most basic object that is used during a simulation.  When creating an instance of the *Bus* class, one can specify a connected dynamic generator (dgr), connected load(s), an initial voltage magnitude and angle, and a shunt impedance or admittance.  All of these arguments are optional as illustrated by the code below.

```python
b0 = Bus(dgr=None, loads=None, V0=None, theta0=None, shunt_z=(), shunt_y=())
```

A few things to note about creating an instance of the Bus class:

* The dynamic generator (dgr) must be of type *DGR* or of a type derived from the DGR superclass. The *DGR* type is discussed in-depth later.
* The loads argument can be a single load or a list of loads.  In either case, it must be an object of type *Load* or a list of *Load* objects (objects for which the *Load* class is a superclass are also acceptable). The *Load* type is discussed later.
* If an initial voltage magnitude and angle are provided and they do not match the initial values stored in the attached dgr and/or load(s) objects, the latter values will be overwritten.  If no initial voltage is supplied when instantiating a *Bus* object, the initial magnitude and angle of the attached dgr or load(s) will be inherited with the dgr taking precedence over the loads, and the values from the first load in the list taking precedence over all others.
* If both a shunt admittance and impedance are provided, the admittance value takes precedence (internally, only the admittance is stored, so the impedance is converted before storing).
* The complex numbers representing the shunt admittance and impedance (*shunt_y* and *shunt_z*, respectively) should be specified as an ordered tuple where the first element is the real component, and the second element is the imaginary component.  An example is as follows.

```python
# the following specifies a shunt admittance for bus b1 where y=a+jb
b1 = Bus(shunt_y=(a, b))
```

####PVBus####
Building upon the *Bus* class, PowerPy has a *PVBus* class intended strictly to be used for static load flow calculations.  As the name implies, instances of the *PVBus* class represent constant power, constant voltage magnitude buses, i.e., generation buses, for the purposes of power flow computations.  An instance of the *PVBus* class can be instantiated with the specified power output and voltage magnitude, as well as the initial voltage angle and shunt impedance and/or admittance.  An example with the default arguments is given below (note that if *P* and *V* are not supplied, they will be defaulted to 0 and 1 per unit, respectively).

```python
b2 = PVBus(P=None, V=None, theta0=None, shunt_z=(), shunt_y=())
```

####PQBus####
Similar to the *PVBus* class, PowerPy has a *PQBus* class that extends the basic *Bus* class and is intended strictly to be used for static load flow calculations.  As the name implies, instances of the *PQBus* class represent constant real and reactive power load (or generation) buses for the purposes of power flow computations.  An instance of the *PQBus* class can be instantiated with the specified real and reactive power draw (or generation, if negative), as well as the initial voltage angle and shunt impedance and/or admittance.  It should be noted that the *PQBus* class is simply a convenient wrapper around the standard *Bus* class with an instance of the *ConstantPowerLoad* class (see below for details) created and attached to the bus upon instantiation.  That is, the following two examples are equivalent with respect to the power flow analysis.

```python
b3 = PQBus(P=None, Q=None, V0=None, theta0=None, shunt_z=(), shunt_y=())

l0 = ConstantPowerLoad(P=None, Q=None, V0=None, theta0=None)
b4 = Bus(loads=l0, V0=None, theta0=None, shunt_z=(), shunt_y=())
```

Note that if *P* and *Q* are omitted, they will both be defaulted to 0.

###Load###
A *Load* superclass is defined that effectively inherits all the properties and methods of the *Node* class without any additions. It's purpose is to provide a basis for other, more specific load models which are described below.

####ConstantPowerLoad####
An instance of the *ConstantPowerLoad* class models a load that draws a constant real and reactive power, irrespective of the states of the power network.  In classic load flow analysis, an instance of the *ConstantPowerLoad* class is equivalent to a PQ bus.  Like the *Node* class from which it is derived, an instance of the *ConstantPowerLoad* class can be initialized with a voltage magnitude and angle, *V0* and *theta0*.  Additionally, a constant real and reactive power can be specified (in per unit) upon instantiation; these values can also be changed using the *change_real_and_reactive_power* method.  An example instantiation and change of P and Q values is illustrated below.

```python
l1 = ConstantPowerLoad(P=None, Q=None, V0=None, theta0=None)

l1.change_real_and_reactive_power(new_P=1.0, new_Q=0.4)
```

###DGR###

####SynchronousDGR####

##Static Simulation##
PowerPy is capable of performing static 
