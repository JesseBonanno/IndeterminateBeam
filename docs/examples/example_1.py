# Statically Indeterminate beam (Ex 12.21 Hibbeler)
# Determine the reactions at the roller support B of the beam described below: 
# 3 m long, fixed at A (x = 0 m), roller support at B (x=3 m), 
# vertical point load at midpan of 8000 N, UDL of 6000 N/m, EI constant.

from indeterminatebeam import Beam, Support, PointLoadV, UDLV

beam = Beam(3)

a = Support(0,(1,1,1))  
b = Support(3,(0,1,0))

load_1 = PointLoadV(-8000,1.5)
load_2 = UDLV(-6000, (0,3))

beam.add_supports(a,b)
beam.add_loads(load_1,load_2)

beam.analyse()

print(f"The beam has an absolute maximum shear force of: {beam.get_shear_force(return_absmax=True)} N")
print(f"The beam has an absolute maximum bending moment of: {beam.get_bending_moment(return_absmax=True)} N.mm")
print(f"The beam has a vertical reaction at B of: {beam.get_reaction(3,'y')} N")

fig1 = beam.plot_beam_external()  
fig1.show()

fig2 = beam.plot_beam_internal()  
fig2.show()

# fig1.write_image("./example_1_external.png")
# fig2.write_image("./example_1_internal.png")