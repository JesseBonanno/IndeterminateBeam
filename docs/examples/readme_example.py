# arbritrary example defined in README.md
from indeterminatebeam import Beam, Support, PointLoadV, PointTorque, UDLV, DistributedLoadV
beam = Beam(7)                          # Initialize a Beam object of length 9m with E and I as defaults
beam_2 = Beam(9,E=2000, I =100000)      # Initializa a Beam specifying some beam parameters

a = Support(5,(1,1,0))                  # Defines a pin support at location x = 5m  
b = Support(0,(0,1,0))                  # Defines a roller support at location x = 0m
c = Support(7,(1,1,1))                  # Defines a fixed support at location x = 7m
beam.add_supports(a,b,c)    

load_1 = PointLoadV(1,2)                # Defines a point load of 1kn acting up, at location x = 2m
load_2 = UDLV(2,(1,4))                  # Defines a 2kN UDL from location x = 1m to x = 4m 
load_3 = PointTorque(2, 3.5)            # Defines a 2kN.m point torque at location x = 3.5m
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