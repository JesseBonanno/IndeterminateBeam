# Readme example as a demonstration for changing units
# used and presented in following example. Note that
# the example is conceptually identical only with 
# different units.

# update units usings the update_units() function.
# use the command below for more information.
# help(beam.update_units)

# note: initialising beam with the anticipation that units will be updated
beam = Beam(7000, E = 200 * 10 **6, I = 9.05 * 10 **6)

beam.update_units(key='length', unit='mm')
beam.update_units('force', 'kN')
beam.update_units('distributed', 'kN/m')
beam.update_units('moment', 'kN.m')
beam.update_units('E', 'kPa')
beam.update_units('I', 'mm4')
beam.update_units('deflection', 'mm')

a = Support(5000,(1,1,0))               # Defines a pin support at location x = 5 m (x = 5000 mm)
b = Support(0,(0,1,0))                  # Defines a roller support at location x = 0 m
c = Support(7000,(1,1,1))               # Defines a fixed support at location x = 7 m (x = 7000 mm)
beam.add_supports(a,b,c)    

load_1 = PointLoadV(1,2000)             # Defines a point load of 1000 N (1 kN) acting up, at location x = 2 m
load_2 = DistributedLoadV(2,(1000,4000))      # Defines a 2000 N/m (2 kN/m) UDL from location x = 1 m to x = 4 m 
load_3 = PointTorque(2, 3500)           # Defines a 2*10**3 N.m (2 kN.m) point torque at location x = 3.5 m
beam.add_loads(load_1,load_2,load_3)    # Assign the support objects to a beam object created earlier

beam.analyse()
fig_1 = beam.plot_beam_external()
fig_1.show()

fig_2 = beam.plot_beam_internal()
fig_2.show()