# arbritrary example defined in README.md
from indeterminatebeam import Beam, Support, PointLoadV, PointTorque, UDLV, DistributedLoadV
beam = Beam(7000)                          # Initialize a Beam object of length 9000 mm with E and I as defaults
beam_2 = Beam(9000,E=2000, I =100000)      # Initializa a Beam specifying some beam parameters

a = Support(5000,(1,1,0))                  # Defines a pin support at location x = 5000 mm  
b = Support(0,(0,1,0))                  # Defines a roller support at location x = 0 mm
c = Support(7000,(1,1,1))                  # Defines a fixed support at location x = 7000 mm
beam.add_supports(a,b,c)    

load_1 = PointLoadV(1000,2000)                # Defines a point load of 1000 N acting up, at location x = 2000 mm
load_2 = DistributedLoadV(2,(1000,4000))      # Defines a 2 N/mm UDL from location x = 1000 mm to x = 4000 mm 
load_3 = PointTorque(2*10**6, 3500)            # Defines a 2*10**6 N.mm point torque at location x = 3500 mm
beam.add_loads(load_1,load_2,load_3)    # Assign the support objects to a beam object created earlier

beam.analyse()

fig_1 = beam.plot_beam_external()
fig_1.show()

fig_2 = beam.plot_beam_internal()
fig_2.show()

# save the results (optional)
# Can save figure using ``fig.write_image("./results.pdf")`` (can change extension to be
# png, jpg, svg or other formats as reired). Requires pip install -U kaleido

# fig_1.write_image("./readme_example_diagram.png")
# fig_2.write_image("./readme_example_internal.png")