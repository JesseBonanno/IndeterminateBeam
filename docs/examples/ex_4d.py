# defined by force (tuple with start and end force), 
# span (tuple with start and end point) and angle of force
load_1 = TrapezoidalLoad(force=(1000,2000), span=(1,2), angle = 0)
load_2 = TrapezoidalLoad(force=(-1000,-2000), span=(3,4), angle = 45)
load_3 = TrapezoidalLoad(force=(-1000,2000), span=(5,6), angle = 90)

# Plotting the loads
beam = Beam(7)
beam.add_loads(
    load_1,
    load_2,
    load_3
)

fig = beam.plot_beam_diagram()
fig.show()