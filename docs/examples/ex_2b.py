# Run section 2a (prior to running this example)   

# query for the data at a specfic point (note units are not provided)
print("bending moments at 3 m: " + str(beam.get_bending_moment(3)))
print("shear forces at 1,2,3,4,5m points: " + str(beam.get_shear_force(1,2,3,4,5)))
print("normal force absolute max: " + str(beam.get_normal_force(return_absmax=True)))
print("deflection max: " + str(beam.get_deflection(return_max = True)))   

##add a query point to a plot (adds values on plot)
beam.add_query_points(1,3,5)
beam.remove_query_points(5)

## plot the results for the beam
fig = beam.plot_beam_internal()
fig.show()