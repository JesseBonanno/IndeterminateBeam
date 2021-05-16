# Spring Supported beam (Ex 12.16 Hibbeler)
# Determine the vertical displacement at x = 1 m for the beam detailed below:
# 3 m long, spring of ky = 45 kN/m at A (x = 0 m) and B (x = 3 m), vertical point load at x = 1 m of 3000 N, E = 200 GPa, I = 4.6875*10**-6 m4.

# when initializing beam we should specify E and I. Units should be expressed in MPa (N/mm2) for E, and mm4 for I
beam = Beam(3, E=(200)*10**3, I=(4.6875*10**-6)*10**12)

# creating supports, note that an x support must be specified even when there are no x forces. This will not affect the accuracy or reliability of results.
# Also note that ky units are kN/m in the problem but must be in N/m for the program to work correctly.
a = Support(0, (1,1,0), ky = 45000)   
b = Support(3, (0,1,0), ky = 45000)

load_1 = PointLoadV(-3000, 1)

beam.add_supports(a,b)
beam.add_loads(load_1)

beam.analyse()

beam.get_deflection(1)

fig1 = beam.plot_beam_external()  
fig1.show()

fig2 = beam.plot_beam_internal()  
fig2.show()

##results in 38.46 mm deflection ~= 38.4mm specified in textbook (difference only due to their rounding)
##can easily check reliability of answer by looking at deflection at the spring supports. Should equal F/k.
## ie at support A (x = 0 m), the reaction force is 2kN by equilibrium, so our deflection is F/K = 2kn / 45*10-3 kN/mm = 44.4 mm (can be seen in plot)