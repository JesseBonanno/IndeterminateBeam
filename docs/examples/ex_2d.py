# Arbritrary example defined in README.md
from indeterminatebeam import Beam, Support, PointLoadV, PointTorque, UDLV, DistributedLoadV
beam = Beam(7)                          # Initialize a Beam object of length 7 m with E and I as defaults
beam_2 = Beam(9,E=2000, I =100000)      # Initialize a Beam specifying some beam parameters

a = Support(5,(1,1,0))                  # Defines a pin support at location x = 5 m  
b = Support(0,(0,1,0))                  # Defines a roller support at location x = 0 m
c = Support(7,(1,1,1))                  # Defines a fixed support at location x = 7 m
beam.add_supports(a,b,c)    

load_1 = PointLoadV(1000,2)                # Defines a point load of 1000 N acting up, at location x = 2 m
load_2 = DistributedLoadV(2000,(1,4))      # Defines a 2000 N/m UDL from location x = 1 m to x = 4 m 
load_3 = PointTorque(2*10**3, 3.5)            # Defines a 2*10**3 N.m point torque at location x = 3.5 m
beam.add_loads(load_1,load_2,load_3)    # Assign the support objects to a beam object created earlier

beam.analyse()

# print results as a table with 10 points
beam.print_results_table(num_points=10, max_dp=3)

# optionally export as a csv
# beam.export_results_csv(filename="filename.csv", num_points=100, max_dp=10)
