# TIMOSHENKO BEAM
beam = Beam(10, E=24800, G=3600, I=11600, A=74)

beam.update_units("E", "MPa")
beam.update_units("G", "MPa")
beam.update_units("I", "cm4")
beam.update_units("A", "cm2")
beam.update_units("force", "kN")
beam.update_units("distributed", "kN/m")
beam.update_units("deflection", "mm")

a = Support(0, (1, 1, 0))  # Defines a pin support at location x = 0 m
b = Support(2, (1, 1, 0))  # Defines a pin support at location x = 2 m
c = Support(7, (1, 1, 0))  # Defines a pin support at location x = 7 m
d = Support(10, (1, 1, 0))  # Defines a pin support at location x = 10 m

beam.add_supports(a, b, c, d)

load_1 = DistributedLoadV(-10, (0, 2))
load_2 = DistributedLoadV(-10, (7, 10))
load_3 = PointLoadV(-25, 4.5)
# Defines a point load of 1000 N acting up, at location x = 2 m
beam.add_loads(
    load_1, load_2, load_3
)  # Assign the support objects to a beam object created earlier

beam.analyse()

## plot the diagram of the problem
fig_0 = beam.plot_beam_diagram()
fig_0.show()

fig_1 = beam.plot_reaction_force()
fig_1.show()

fig_2 = beam.plot_beam_internal()
fig_2.show()

# EULER BEAM
beam = Beam(10, E=24800, I=11600, A=74)

beam.update_units("E", "MPa")
beam.update_units("I", "cm4")
beam.update_units("A", "cm2")
beam.update_units("force", "kN")
beam.update_units("distributed", "kN/m")
beam.update_units("deflection", "mm")

# assign supports and loads from earlier
beam.add_supports(a, b, c, d)
beam.add_loads(load_1, load_2, load_3)

beam.analyse()

## plot the results for the beam
fig_3 = beam.plot_reaction_force()
fig_3.show()

fig_4 = beam.plot_beam_internal()
fig_4.show()
