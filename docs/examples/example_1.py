##example 4.17 https://engineering.purdue.edu/~ce474/Docs/Beam_Examples02.pdf
from indeterminatebeam import Beam, Support, DistributedLoadH, DistributedLoadV, PointLoadH, PointLoadV, PointTorque, PointLoad

beam = Beam(6)

a = Support()               ##by default a support is defined as a fixed support at location 0
c = Support(6,(0,1,0))

beam.add_supports(a,c)
beam.add_loads(PointLoadV(-15,3))

beam.analyse()

print(beam.check_determinancy())
print(beam.get_shear_force(return_absmax=True))
print(beam.get_bending_moment(return_absmax=True))

fig = beam.plot()
fig.savefig("./results.png")