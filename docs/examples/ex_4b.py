# defined by force, coord and angle (0)
load_1 = PointLoad(force=1000, coord=1, angle=0)
load_2 = PointLoad(force=1000, coord=2, angle=45)
load_3 = PointLoad(force=1000, coord=3, angle=90)

# Plotting the loads
beam = Beam(4)
beam.add_loads(
    load_1,
    load_2,
    load_3
)

fig = beam.plot_beam_diagram()
fig.show()