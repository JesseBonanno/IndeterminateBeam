# The parameters for a support class are as below, taken from the docstring
# for the Support class __init__ method.

# Parameters:
#         -----------
#         coord: float
#             x coordinate of support on a beam in m (default 0)
#         fixed: tuple of 3 booleans
#             Degrees of freedom that are fixed on a beam for movement in
#             x, y and bending, 1 represents fixed and 0 represents free
#             (default (1,1,1))
#         kx :
#             stiffness of x support (N/m), if set will overide the
#             value placed in the fixed tuple. (default = None)
#         ky : (positive number)
#             stiffness of y support (N/m), if set will overide the
#             value placed in the fixed tuple. (default = None)


# Lets define every possible degree of freedom combination for
# supports below, and view them on a plot:
support_0 = Support(0, (1,1,1))     # conventional fixed support
support_1 = Support(1, (1,1,0))     # conventional pin support
support_2 = Support(2, (1,0,1))     
support_3 = Support(3, (0,1,1))
support_4 = Support(4, (0,0,1))
support_5 = Support(5, (0,1,0))     # conventional roller support
support_6 = Support(6, (1,0,0))

# Note we could also explicitly define parameters as follows:
support_0 = Support(coord=0, fixed=(1,1,1))

# Now lets define some spring supports
support_7 = Support(7, (0,0,0), kx = 10)    #spring in x direction only
support_8 = Support(8, (0,0,0), ky = 5)     # spring in y direction only
support_9 = Support(9, (0,0,0), kx = 100, ky = 100)     # spring in x and y direction

# Now lets define a support which is fixed in one degree of freedom
# but has a spring stiffness in another degree of freedom
support_10 = Support(10, (0,1,0), kx = 10) #spring in x direction, fixed in y direction
support_11 = Support(11, (0,1,1), kx = 10) #spring in x direction, fixed in y and m direction

# Note we could also do the following for the same result since the spring
# stiffness overides the fixed boolean in respective directions
support_10 = Support(10, (1,1,0), kx =10)

# Now lets plot all the supports we have created
beam = Beam(11)

beam.add_supports(
    support_0,
    support_1,
    support_2,
    support_3,
    support_4,
    support_5,
    support_6,
    support_7,
    support_8,
    support_9,
    support_10,
    support_11,
)

fig = beam.plot_beam_diagram()
fig.show()