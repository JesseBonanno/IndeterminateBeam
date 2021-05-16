# defined using a force (technically a moment, however force is used to maintain consistenct for all load classes) and a coordinate. An anti-clockwise moment is positive by convention of this package.
load_1 = PointTorque(force=1000, coord=1)
load_2 = PointTorque(force=-1000, coord=2)

# Plotting the loads
beam = Beam(3)
beam.add_loads(
    load_1,
    load_2
)

fig = beam.plot_beam_diagram()
fig.show()