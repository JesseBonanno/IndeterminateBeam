## Statically Indeterminate beam (Ex 12.21 Hibbeler)
## Determine the reactions at the roller support B of the beam described below: 
## 3m long, fixed at A (x = 0m), roller support at B (x=3m), vertical point load at midpan of 8kN, UDL of 6kN/m, EI constant.

from indeterminatebeam import Beam, Support, PointLoadV, DistributedLoadV

beam = Beam(3)

a = Support(0,(1,1,1))  
b = Support(3,(0,1,0))

load_1 = PointLoadV(-8,1.5)
load_2 = DistributedLoadV(-6, (0,3))

beam.add_supports(a,b)
beam.add_loads(load_1,load_2)

beam.analyse()

print(f"The beam has an absolute maximum shear force of: {beam.get_shear_force(return_absmax=True)} kN")
print(f"The beam has an absolute maximum bending moment of: {beam.get_bending_moment(return_absmax=True)} kN.m")
print(f"The beam has a vertical reaction at B of: {beam.get_reaction(3,'y')} kN")

beam.plot_beam_internal()