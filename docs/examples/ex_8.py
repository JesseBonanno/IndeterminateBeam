##AXIAL LOADED INDETERMINATE BEAM (Ex 4.13 Hibbeler)
## A rod with constant EA has a force of 60kN applied at x = 0.1 m, and the beam has fixed supports at x=0, and x =0.4 m. Determine the reaction forces.

beam = Beam(0.4)

a = Support()
b = Support(0.4)

load_1 = PointLoadH(-60000, 0.1)

beam.add_supports(a,b)
beam.add_loads(load_1)

beam.analyse()
beam.plot_normal_force()
