# Statically Determinate beam (Ex 12.14 Hibbeler)
# Determine the displacement at x = 8m for the following structure
# 8 m long fixed at A (x = 0m)
# A trapezoidal load of - 4000 N/m at x = 0 m descending to 0 N/m at x = 6 m.

beam = Beam(8, E=1, I = 1)     ##EI Defined to be 1 get the deflection as a function of EI

a = Support(0, (1,1,1))             ##explicitly stated although this is equivalent to Support() as the defaults are for a cantilever on the left of the beam.

load_1 = TrapezoidalLoadV((-4000,0),(0,6))

beam.add_supports(a)
beam.add_loads(load_1)

beam.analyse()
print(f"Deflection is {beam.get_deflection(8)} N.m3 / EI (N.mm2)")

fig = beam.plot_beam_internal()
fig.show()
# Note: all plots are correct, deflection graph shape is correct but for actual deflection values will need real EI properties.

##save the results as a pdf (optional)
# Can save figure using `fig.write_image("./results.pdf")` (can change extension to be
# png, jpg, svg or other formats as reired). Requires pip install -U kaleido
