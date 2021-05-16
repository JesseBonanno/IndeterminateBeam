# defined with Sympy expression of the distributed load function 
# expressed using variable x which represents the beam x-coordinate. 
# Requires quotation marks around expression. As with the UDL and 
# Trapezoidal load classes other parameters to express are the span 
# (tuple with start and end point) and angle of force.
# NOTE: where UDL or Trapezoidal load classes can be specified (linear functions)
# they should be used for quicker analysis times.

load_1 = DistributedLoad(expr= "2", span=(1,2), angle = 0)
load_2 = DistributedLoad(expr= "2*(x-6)**2 -5", span=(3,4), angle = 45)
load_3 = DistributedLoad(expr= "cos(5*x)", span=(5,6), angle = 90)

# Plotting the loads
beam = Beam(7)
beam.add_loads(
    load_1,
    load_2,
    load_3
)

fig = beam.plot_beam_diagram()
fig.show()