# for all loads except the point torque an angle is specified for the
# direction of the load. If the load to be specified is to be completely
# vertical or completely horizontal a V (vertical) or a H (horizontal)
# can be added at the end of the class name, and the angle does then
# not need to be spefied.

# The following two loads are equivalent horizontal loads
load_1 = PointLoad(force=1000, coord=1, angle = 0)
load_2 = PointLoadH(force=1000, coord=2)

# The following two loads are equivalent vertical loads
load_3 = PointLoad(force=1000, coord=3, angle = 90)
load_4 = PointLoadV(force=1000, coord=4)

# The following two loads are also equivalent (a negative sign
# esentially changes the load direction by 180 degrees).
load_5 = PointLoad(force=1000, coord=5, angle = 0)
load_6 = PointLoad(force=-1000, coord=6, angle = 180)


# Plotting the loads
beam = Beam(7)
beam.add_loads(
    load_1,
    load_2,
    load_3,
    load_4,
    load_5,
    load_6
)

fig = beam.plot_beam_diagram()
fig.show()