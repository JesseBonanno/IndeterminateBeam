"""Main module that contains the main class Beam, and auxiliary classes Support, PointLoadH,
PointLoadV, DistributedLoadH, and DistributedLoadV, PointLoad and PointTorque.

Example
-------
>>> beam = Beam(6)
>>> a = Support()
>>> c = Support(6,(0,1,0))
>>> beam.add_supports(a,c)
>>> beam.add_loads(PointLoadV(-15,3))
>>> beam.analyse()
>>> beam.plot()
"""

from collections import namedtuple
import numpy as np
import os
from sympy import integrate, lambdify, Piecewise, sympify, symbols, linsolve, sin, cos,oo
from sympy.abc import x
from math import radians 
from indeterminatebeam.data_validation import assert_number, assert_positive_number, assert_strictly_positive_number
from indeterminatebeam.plotly_drawing_aid import draw_line, draw_arrowhead, draw_arrow, draw_support_triangle, draw_support_rectangle, \
                               draw_moment, draw_force, draw_load_hoverlabel, draw_reaction_hoverlabel, \
                               draw_support_hoverlabel, draw_support_rollers, draw_support_spring, draw_support
from plotly.subplots import make_subplots
import plotly.graph_objects as go

class Support:
    """
    A class to represent a support.

    Attributes:
    -------------
        _position: float
            x coordinate of support on a beam (default 0)
        _stiffness: tuple of 3 floats or infinity
            stiffness K (kN/mm) for movement in x, y and bending, oo represents infinity in sympy
            and means a completely fixed conventional support, and 0 means free to move.
        _DOF : tuple of 3 booleans
            Degrees of freedom that are restraint on a beam for movement in x, y and bending, 1 
            represents that a reaction force exists and 0 represents free (default (1,1,1))
        _fixed: tuple of 3 booleans
            Degrees of freedom that are completely fixed on a beam for movement in x, y and 
            bending, 1 represents fixed and 0 represents free or spring  (default (1,1,1))
        _id : positive number
            id assigned when support associated with Beam object, to help remove supports.

    Examples
    --------
    >>> Support(0, (1,1,1))  ##creates a fixed suppot at location 0
    >>> Support(5, (1,1,0))  ##creatse a pinned support at location 5
    >>> Support(5.54, (0,1,0))  ##creates a roller support at location 5.54
    >>> Support(7.5, (0,1,0), ky = 5)  ##creates a y direction spring support at location 7.5
    """

    def __init__(self, coord=0, fixed =(1,1,1), kx = None, ky = None):
        """
        Constructs all the necessary attributes for the Support object

        Parameters:
        -----------
        coord: float
            x coordinate of support on a beam (default 0)
            (default not 0.0 due to a float precision error that previously occured)
        fixed: tuple of 3 booleans
            Degrees of freedom that are fixed on a beam for movement in x, y and 
            bending, 1 represents fixed and 0 represents free (default (1,1,1))
        kx : 
            stiffness of x support (kN/mm), if set will overide the value placed in the fixed tuple. (default = None)
        ky : (positive number)
            stiffness of y support (kN/mm), if set will overide the value placed in the fixed tuple. (default = None)
        """
        ##input validation
        assert_positive_number(coord, 'coordinate')

        if kx:
            assert_positive_number(kx, 'kx')
        if ky:
            assert_positive_number(ky, 'ky')

        for a in fixed:
            if a not in [0,1]:
                raise ValueError("The provided DOF, must be a tuple of booleans of length 3")
        if len(fixed) != 3:
            raise ValueError("The provided DOF, must be a tuple of booleans of length 3")

        ##lets change our formulation so that now our springs are represented 
        self._stiffness = [oo if a else 0 for a in fixed]

        if kx:
            self._stiffness[0] = kx
        if ky:
            self._stiffness[1] = ky

        self._DOF = [int(bool(e)) for e in self._stiffness]
        self._fixed = [int(bool(e)) if e==oo else 0 for e in self._stiffness]
        self._position = coord
        self._id = None

    def __str__(self):
        return f"""--------------------------------
        id = {self._id}
        position = {float(self._position)}
        Stiffness_x = {self._stiffness[0]}
        Stiffness_y = {self._stiffness[1]}
        Stiffness_M = {self._stiffness[2]} """

    def __repr__(self):
        if self._id:
            return f"<support, id = {self._id}>"
        return "<Support>"

class PointLoad(namedtuple("PointLoad", "force, coord, angle")):
    """Point load described by a tuple of floats: (force, coord, angle).

    Parameters:
    -----------
    Force: float
        Force in kN
    coord: float 
        x coordinate of load on beam
    angle: float (between 0 and 180)
        angle of point load in range 0 to 180 where: 
        - 0 degrees is purely horizontal +ve
        - 90 degrees is purely vertical +ve
        - 180 degrees is purely horizontal -ve of force sign specified.


    Examples
    --------
    >>> external_force = PointLoad(10, 9, 90)  # 10 kN towards the right at x=9 m
    >>> external_force = PointLoad(-30, 3, 0)  # 30 kN downwards at x=3 m
    >>> external_force
    PointLoad(force=-30, coord=3, angle=0)
    """

class PointLoadV(namedtuple("PointLoadV", "force, coord")):
    """Vertical point load described by a tuple of floats: (force, coord).
    
    Parameters:
    -----------
    Force: float
        Force in kN
    coord: float 
        x coordinate of load on beam

    Examples
    --------
    >>> external_force = PointLoadV(-30, 3)  # 30 kN downwards at x=3 m
    >>> external_force
    PointLoadV(force=-30, coord=3)
    """

class PointLoadH(namedtuple("PointLoadH", "force, coord")):
    """Horizontal point load described by a tuple of floats: (force, coord).

    Parameters:
    -----------
    Force: float
        Force in kN
    coord: float 
        x coordinate of load on beam


    Examples
    --------
    >>> external_force = PointLoadH(10, 9)  # 10 kN towards the right at x=9 m
    >>> external_force
    PointLoadH(force=10, coord=9)
    """

class DistributedLoadV(namedtuple("DistributedLoadV", "expr, span")):
    """Distributed vertical load, described by its functional form and application interval.

    Parameters:
    -----------
    expr: sympy expression
        Sympy expression of the distributed load function expressed using variable x
        which represents the beam x-coordinate. Requires quotation marks around expression.
    span: tuple of floats
        A tuple containing the starting and ending coordinate that the function is applied to.


    Examples
    --------
    >>> snow_load = DistributedLoadV("10*x+5", (0, 2))  # Linearly growing load for 0<x<2 m
    >>> trapezoidal_load = DistributedLoadV("-5 + 10 * x", (1,2)) # Linearly growing load starting at 5kN/m ending at 15kn/m 
    >>> UDL = DistributedLoadV(10, (1,3))
    """

class DistributedLoadH(namedtuple("DistributedLoadH", "expr, span")):
    """Distributed horizontal load, described by its functional form and application interval.

    Parameters:
    -----------
    expr: sympy expression
        Sympy expression of the distributed load function expressed using variable x
        which represents the beam x-coordinate. Requires quotation marks around expression.
    span: tuple of floats
        A tuple containing the starting and ending coordinate that the function is applied to.

        Examples
    --------
    >>> weight = DistributedLoadH("10*x+5", (0, 2))  # Linearly growing load for 0<x<2 m
    """
    
class PointTorque(namedtuple("PointTorque", "torque, coord")):
    """Point clockwise torque, described by a tuple of floats: (torque, coord).

    Parameters:
    -----------
    torque: float
        Torque in kN.m
    coord: float 
        x coordinate of torque on beam

    Examples
    --------
    >>> motor_torque = PointTorque(30, 4)  # 30 kN·m (clockwise) torque at x=4 m
    """

def TrapezoidalLoad(force = (0, 0), span = (0, 0)):
    """Wrapper for the DistributedLoadV class, used to express a trapezoidal load distribution.

    Parameters
    ------------
        force : tuple of two floats
            Describes the starting force value and ending force value (kN/m)
        span : tuple of two floats
            Describes the starting coordinate value and ending coordinate value (m)

    Examples
    --------
    >>> trapezoidal_load = TrapezoidalLoad((5,15), (1,2)) # Linearly growing load starting at 5kN/m ending at 15kn/m
    >>> trapezoidal_load = DistributedLoadV("-5 + 10 * x", (1,2)) #Equivalent expression created using DistributedLoadV
    """

    if len(force) != 2 or len(span) != 2:
        raise TypeError("A tuple of length 2 is required for both the force and span arguments")

    start_load, end_load = force
    start_coordinate, end_coordinate = span

    assert_number(start_load, "force[0] (The starting force)")
    assert_number(end_load, "force[1] (The ending force)")

    assert_number(start_coordinate, "span[0] (The starting coordinate) ")
    assert_number(end_coordinate, "span[1] (The ending coordinate)")

    if start_coordinate >= end_coordinate:
        raise ValueError("start coordinate should be less than end coordinate")

    if start_coordinate == end_coordinate:
        return DistributedLoadV(0, (start_coordinate, end_coordinate))

    elif end_load == start_load:
        return DistributedLoadV(start_load, (start_coordinate, end_coordinate))

    else:
        a = (end_load - start_load) / (end_coordinate - start_coordinate)
        b = start_load - start_coordinate  *a

        return DistributedLoadV(f"{a}*x+{b}", (start_coordinate, end_coordinate))

class Beam:
    """
    Represents a one-dimensional beam that can take axial and tangential loads.

    Attributes
    --------------
    _x0 :float
        Left end coordinate of beam. This module always takes this value as 0.
    _x1 :float
        Right end coordinate of beam. This module always takes this to be the same as the beam span.

    _loads: list
        list of load objects associated with the beam
    _distributed_forces_x: list
        list of distributed forces implemented as piecewise functions
    _distributed_forces_y:
        list of distributed forces implemented as piecewise functions

    _normal_forces: sympy piecewise function
        A sympy function representing the internal axial force as a function of x.
    _shear_forces: sympy piecewise function
        A sympy function representing the internal shear force as a function of x.
    _bending_moments: sympy piecewise function
        A sympy function representing the internal bending moments as a function of x.

    _query: list
        A list containing x coordinates that are to have values explicitly written on graphs.
    _supports: list
        A list of support objects associated with the beam.
    _reactions: dictionary of lists
        A dictionary with keys for support positions. Each key is associated with a list of forces
        of the form ['x','y','m']

    _E: float
        Young's Modulus of the beam (N/mm2 or MPa)
    _I: float
        Second Moment of Area of the beam (mm4)
    _A: float
        Cross-sectional area of the beam (mm2)

    Notes
    -----
    * The default units for length, force and bending moment 
      (torque) are in kN and m (m, kN, kN·m)
    * The default units for beam properties (E, I, A) are in N and mm 
       (N/mm2, mm4, mm2)
    * The default unit for spring supports is kN/mm
    * Default properties are for a 150UB18.0 steel beam.
    """

    def __init__(self, span: float=10, E = 2*10**5, I= 9.05*10**6, A = 2300):
        """Initializes a Beam object of a given length.
        
        Parameters
        ----------
        span : float
            Length of the beam span. Must be positive, and the pinned and rolling
            supports can only be placed within this span. The default value is 10.
        E: float
            Youngs modulus for the beam. The default value is 200 000 MPa, which
            is the youngs modulus for steel.
        I: float
            Second moment of area for the beam about the z axis. The default value
            is 905 000 000 mm4.
        A: float
            Cross-sectional area for the beam about the z axis. The default value
            is 2300 mm4.
        """

        assert_strictly_positive_number(span, 'span')
        assert_strictly_positive_number(E, "Young's Modulus (E)")
        assert_strictly_positive_number(I, 'Second Moment of Area (I)')
        assert_strictly_positive_number(A, 'Area (A)')


        self._x0 = 0
        self._x1 = span

        self._loads = []
        self._distributed_forces_x = []
        self._distributed_forces_y = []
        
        self._normal_forces = []
        self._shear_forces = []
        self._bending_moments = []

        self._query = []
        self._supports = []
        self._reactions = {}
        
        self._E = E
        self._I = I
        self._A = A

    def add_loads(self, *loads):
        """Apply an arbitrary list of (point- or distributed) loads to the beam.

        Parameters
        ----------
        loads : iterable
            An iterable containing DistributedLoad or PointLoad objects to
            be applied to the Beam object. Note that the load application point
            (or segment) must be within the Beam span.

        """
        for load in loads:
            ##note have currently ignored distributed load h in this version of the program
            if isinstance(load,(PointLoad,PointLoadH,PointLoadV,PointTorque,DistributedLoadV)):
                if isinstance(load,DistributedLoadV):
                    left = min(load[1])
                    right = max(load[1])
                    assert_positive_number(left, "span left")
                    assert_positive_number(right, "span right")

                    if self._x0 > left or right > self._x1:
                        raise ValueError(f"Coordinate {load[1]} for {str(load)} is not a point on beam.")

                    elif len(load[1]) != 2:
                        raise ValueError(f"Coordinates for {str(load)} span should only have two numbers entered.")
                    
                    else:
                        self._loads.append(load)

                elif isinstance(load,(PointTorque,PointLoadV,PointLoadH,PointLoad)):
                    assert_number(load[0],'force')
                    assert_positive_number(load[1],'x coordinate')

                    if self._x0 > load[1] or load[1] > self._x1:
                        raise ValueError(f"Coordinate {load[1]} for {str(load)} is not a point on beam.")

                    if isinstance(load,PointLoad):
                        assert_number(load[2],'angle')

                    if abs(round(load[0],10)) > 0:
                        self._loads.append(load)

        self._update_loads()

    def remove_loads(self, *loads, remove_all = False):
        """Remove an arbitrary list of (point- or distributed) loads from the beam.

        Parameters
        ----------
        loads : iterable
            An iterable containing DistributedLoad or PointLoad objects to
            be removed from the Beam object. If object not on beam then does nothing.
        remove_all: boolean
            If true all loads associated with beam will be removed.

        """
        if remove_all:
            self._loads = []
            self._update_loads()
            return None

        for load in loads:
            if load in self._loads:
                self._loads.remove(load)

        self._update_loads()
    
    def add_supports(self, *supports):
        """Apply an arbitrary list of supports (Support objects) to the beam.

        Parameters
        ----------
        supports : iterable
            An iterable containing Support objects to
            be applied to the Beam object. Note that the load application point
            (or segment) must be within the Beam span.

        """
        for support in supports:
            if not isinstance(support, Support):
                raise TypeError("support must be of type class Support")
            
            if (self._x0 > support._position) or (support._position > self._x1):
                raise ValueError("Not a point on beam")

            elif self._supports == []:
                support._id = 1
                self._supports.append(support)

            elif support._position not in [x._position for x in self._supports]:
                support._id = self._supports[-1]._id + 1
                self._supports.append(support)
            else:
                raise ValueError(f"This coordinate {support._position} already has a support associated with it")
        
        self._reactions = {a._position : [0,0,0] for a in self._supports}

    def remove_supports(self, *supports, remove_all = False):
        """Remove an arbitrary list of supports (Support objects) from the beam.

        Parameters
        ----------
        ids : iterable
            An iterable containing either Support objects or Support object ids to
            be removed from the Beam object. If support not on beam then does nothing.
        remove_all: boolean
            If true all supports associated with beam will be removed.

        """
        if remove_all:
            self._supports = []
            return None

        for support in self._supports:
            if support._id in supports or support in supports:
                self._supports.remove(support)
    ##does not display error if ask to remove somethign that isnt there, is this okay?

    def get_support_details(self):
        """Print out a readable summary of all supports on the beam. """

        print(f"There are {str(len(self._supports))} supports:",end ='\n\n')
        for support in self._supports:
            print(support, end ='\n\n')


    ##SECTION - ANALYSE
    def check_determinancy(self):
        """Check the determinancy of the beam.
        
        Returns
        ---------
        int
            < 0 if the beam is unstable
            0 if the beam is statically determinate
            > 0 if the beam is statically indeterminate
        
        """

        unknowns = np.array([0,0,0])
        equations = 3

        for support in self._supports:
            unknowns = np.array(support._DOF) + unknowns

        if unknowns[0] == 0:
            equations -= 1

        if unknowns[1] == 0:
            equations -= 1

        unknowns = sum(unknowns)

        if unknowns == 0:
            return ValueError("No reaction forces exist")

        if unknowns < equations:
            return ValueError("Structure appears to be unstable")

        else:
            self._determinancy = (unknowns - equations)
            return (unknowns - equations)

    def analyse(self):
        """Solve the beam structure for reaction and internal forces  """

        x0,x1 = self._x0, self._x1

        ##create unknown sympy variables
        unknowns_x = {a._position: [symbols("x_"+str(a._id)), a._stiffness[0]] for a in self._supports if a._stiffness[0] !=0}
        unknowns_y = {a._position: [symbols("y_"+str(a._id)), a._stiffness[1]] for a in self._supports if a._stiffness[1] !=0}
        unknowns_m = {a._position: [symbols("m_"+str(a._id)), a._stiffness[2]] for a in self._supports if a._stiffness[2] !=0}

        ##grab the set of all the sympy unknowns for y and m and change to a list, do same for x unknowns
        unknowns_ym = [a[0] for a in unknowns_y.values()] + [a[0] for a in unknowns_m.values()]
        unknowns_xx = [a[0] for a in unknowns_x.values()]

        ##Assert that there are enough supports. Even though it logically works to have no x support if you have no
        ## x loading, it works much better in the program and makes the code alot shorter to just enforce that an x support is 
        ## there, even when there is no load.
        if len(unknowns_xx) < 1:
            raise ValueError('You need at least one x restraint, even if there are no x forces')

        if len(unknowns_ym) <2 :
            raise ValueError('You need at least two y or m restraints, even if there are no y or m forces')
        
        ##locations where x reaction is and order, for indeterminate axial determaintion
        x_0 = [a for a in unknowns_x.keys()]
        x_0.sort()

        ##external reaction equations
        F_Rx = sum(integrate(load, (x, x0, x1)) for load in self._distributed_forces_x) \
               + sum(f.force for f in self._point_loads_x()) \
               + sum([a[0] for a in unknowns_x.values()])   

        F_Ry = sum(integrate(load, (x, x0, x1)) for load in self._distributed_forces_y) \
               + sum(f.force for f in self._point_loads_y()) \
               + sum([a[0] for a in unknowns_y.values()])


        ##moments taken at the left of the beam, anti-clockwise is positive
        M_R = sum(integrate(load * x, (x, x0, x1)) for load in self._distributed_forces_y) \
              + sum(f.force * f.coord for f in self._point_loads_y()) \
              + sum([p*v[0] for p,v in unknowns_y.items()]) \
              + sum(f.torque for f in self._point_torques()) \
              + sum([a[0] for a in unknowns_m.values()])

        ##internal beam equations
        C1, C2 = symbols('C1'), symbols('C2')
        unknowns_ym = unknowns_ym + [C1] +[C2]

        ##normal forces is same concept as shear forces only no distributed for now.
        N_i = sum(self._effort_from_pointload(f) for f in self._point_loads_x()) \
              + sum(self._effort_from_pointload(PointLoadH(v[0],p)) for p,v in unknowns_x.items()) 

        ## shear forces, an internal force acting down would be considered positive by adopted convention
        ##hence if the sum of forces on the beam are all positive, our internal force would also be positive due to difference in convention
        F_i = sum(integrate(load, x) for load in self._distributed_forces_y) \
              + sum(self._effort_from_pointload(f) for f in self._point_loads_y()) \
              + sum(self._effort_from_pointload(PointLoadV(v[0],p)) for p,v in unknowns_y.items())  

        ##bending moments at internal point means we are now looking left along the beam when we take our moments (vs when we did external external reactions and we looked right)
        ##An anti-clockwise moment is adopted as positive internally. 
        ## Hence we need to consider a postive for our shear forces and negative for our moments by our sign convention
        M_i = sum(integrate(load, x, x) for load in self._distributed_forces_y) \
              + sum(integrate(self._effort_from_pointload(f), x)  for f in self._point_loads_y()) \
              + sum(integrate(self._effort_from_pointload(PointLoadV(v[0],p)), x) for p,v in unknowns_y.items()) \
              - sum(self._effort_from_pointload(PointTorque(v[0],p)) for p,v in unknowns_m.items()) \
              - sum(self._effort_from_pointload(f) for f in self._point_torques())


             #with respect to x, + constants but the constants are the M at fixed supports

        dv_EI = sum(integrate(load, x, x ,x) for load in self._distributed_forces_y) \
                + sum(integrate(self._effort_from_pointload(f), x, x)  for f in self._point_loads_y()) \
                + sum(integrate(self._effort_from_pointload(PointLoadV(v[0],p)), x, x) for p,v in unknowns_y.items()) \
                - sum(integrate(self._effort_from_pointload(PointTorque(v[0],p)), x) for p,v in unknowns_m.items()) \
                - sum(integrate(self._effort_from_pointload(f), x) for f in self._point_torques()) \
                + C1

        v_EI = sum(integrate(load, x, x ,x, x) for load in self._distributed_forces_y) \
               + sum(integrate(self._effort_from_pointload(f), x, x, x)  for f in self._point_loads_y()) \
               + sum(integrate(self._effort_from_pointload(PointLoadV(v[0],p)), x, x, x) for p,v in unknowns_y.items()) \
               - sum(integrate(self._effort_from_pointload(PointTorque(v[0],p)), x, x) for p,v in unknowns_m.items()) \
               - sum(integrate(self._effort_from_pointload(f), x, x) for f in self._point_torques()) \
               + C1*x \
               + C2

        ##equations , create a lsit fo equations
        equations_ym = [F_Ry,M_R]

        ##at location that moment is restaint, the slope is known (to be 0, since dont deal for rotational springs)
        for position in unknowns_m.keys():
            equations_ym.append(dv_EI.subs(x,position))

        ##at location that y support is restaint the deflection is known (to be F/k)
        for position in unknowns_y.keys():
            equations_ym.append(v_EI.subs(x,position)* 10 **12 /(self._E*self._I) +unknowns_y[position][0]/unknowns_y[position][1])

        ##equation for normal forces, only for indeterminate in x
        equations_xx = [F_Rx]

        ##the extension of the beam will be equal to the spring displacement on right minus spring displacment on left
        if len(x_0)>1:
            start = x_0[0]
            for position in x_0[1:]: ##dont consider the starting point? only want to look between supports and not at cantilever sections i think
                equations_xx.append(
                    (
                    sum(integrate(self._effort_from_pointload(f), (x,x_0[0], position)) for f in self._point_loads_x())
                    + sum(integrate(self._effort_from_pointload(PointLoadH(v[0],p)), (x,x_0[0], position)) for p,v in unknowns_x.items())
                    )
                    *10**3 /(self._E*self._A)
                    + unknowns_x[start][0]/unknowns_x[start][1]
                    - unknowns_x[position][0]/unknowns_x[position][1]   ##represents elongation displacment on right
                    )


        ##compute analysis with linsolve
        solutions_ym = list(linsolve(equations_ym, unknowns_ym))[0]
        solutions_xx = list(linsolve(equations_xx, unknowns_xx))[0]

        solutions = [a for a in solutions_ym + solutions_xx]

        solution_dict = dict(zip(unknowns_ym+unknowns_xx, solutions))

        self._reactions = {a._position : [0,0,0] for a in self._supports}

        ##substitue in value instead of variable in functions
        for var, ans in solution_dict.items():
            v_EI = v_EI.subs(var,ans) ##complete deflection equation
            M_i  = M_i.subs(var,ans)  ##complete moment equation
            F_i  = F_i.subs(var,ans)  ##complete shear force equation
            N_i = N_i.subs(var,ans)   ##complete normal force equation

            ##create self._reactions to allow for plotting of reaction forces if wanted and for use with get_reaction method.
            if var not in [C1,C2]:
                vec, num = str(var).split('_')
                position = [a._position for a in self._supports if a._id == int(num)][0]
                if vec == 'x':
                    i = 0
                elif vec == 'y':
                    i = 1
                else:
                    i = 2
                self._reactions[position][i] = round(ans,5)

        ##moment unit is kn.m, dv_EI kn.m2, v_EI Kn.m3 --> *10^3, *10^9 to get base units 
        ## EI unit is N/mm2 , mm4 --> N.mm2
        self._shear_forces = F_i
        self._bending_moments = M_i
        self._deflection_equation = v_EI * 10 **12 / ( self._E * self._I )   ## a positive moment indicates a negative deflection, i thought??
        self._normal_forces = N_i

    ##SECTION - QUERY VALUE
    def get_reaction(self, x_coord, direction = None):
        """Find the reactions of a support at position x.

        Parameters
        ----------
        x_coord: float
            The x_coordinates on the beam to be substituted into the equation.
            List returned (if bools all false)
        direction: str ('x','y' or 'm')
            The direction of the reaction force to be returned. If not specified all are returned in a list.

        Returns
        --------
        int
            If direction is 'x', 'y', or 'm' will return an integer representing the reaction force of the support in that direction at location x_coord.
        list of ints
            If direction = None, will return a list of 3 integers, representing the reaction forces of the support ['x','y','m'] at location x_coord.
        None
            If there is no support at the x coordinate specified.
        """
        
        if not self._reactions:
            print("You must analyse the structure before calling this function")
        
        assert_positive_number(x_coord, 'x coordinate')

        if x_coord not in self._reactions.keys():
            return None

        directions = ['x','y','m']

        if direction:
            if direction not in directions:
                raise ValueError("direction should be the value 'x', 'y' or 'm'")
            else:
                return self._reactions[x_coord][directions.index(direction)]
        else:
            return self._reactions[x_coord]



    def _get_query_value(self, x_coord, sym_func, return_max=False, return_min=False, return_absmax=False):  ##check if sym_func is the sum of the functions already in plot_analytical
        """Find the value of a function at position x_coord.

        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be substituted into the equation.
            List returned (if bools all false)
        sym_func: sympy function
            The function to be analysed
        return_max: bool
            return max value of function if true
        return_min: bool
            return minx value of function if true
        return_absmax: bool
            return absolute max value of function if true

        Returns
        --------
        int
            Max, min or absmax value of the sympy function depending on which parameters are set.
        list of ints
            If x-coordinate(s) are specfied value of sym_func at x-coordinate(s).

        Notes
        -----
        * Priority of query parameters is return_max, return_min, return_absmax, x_coord (if more than 1 of the parameters are specified).

        """

        if isinstance(sym_func, list):
            sym_func = sum(sym_func)
        func = lambdify(x, sym_func, "numpy")  
        
        if 1 not in (return_absmax, return_max, return_min):
            if type(x_coord)==tuple:
                return [round(float(func(x_)),3) for x_ in x_coord] 
            else:
                return round(float(func(x_coord)),3)

        x_vec = np.linspace(self._x0, self._x1, int(1000))  ## numpy array for x positions closely spaced (allow for graphing)                                      ##i think lambdify is needed to let the function work with numpy
        y_vec = np.array([func(t) for t in x_vec])  
        min_ = float(y_vec.min())
        max_ = float(y_vec.max())
 
        if return_max:
            return round(max_,3)
        elif return_min:
            return round(min_,3)
        elif return_absmax:
            return round(max(abs(min_), max_),3)

    def get_bending_moment(self, *x_coord,return_max=False,return_min=False, return_absmax = False):
        """Find the bending moment(s) on the beam object.

        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be substituted into the equation.
            List returned (if bools all false)
        return_max: bool
            return max value of function if true
        return_min: bool
            return minx value of function if true
        return_absmax: bool
            return absolute max value of function if true
        
        Returns
        --------
        int
            Max, min or absmax value of the bending moment function depending on which parameters are set.
        list of ints
            If x-coordinate(s) are specfied value of the bending moment function at x-coordinate(s).

        Notes
        -----
        * Priority of query parameters is return_max, return_min, return_absmax, x_coord (if more than 1 of the parameters are specified).

        """

        return self._get_query_value(x_coord, sym_func = self._bending_moments, return_max = return_max, return_min = return_min, return_absmax=return_absmax )

    def get_shear_force(self, *x_coord,return_max=False,return_min=False, return_absmax=False):
        """Find the shear force(s) on the beam object. 

        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be substituted into the equation.
            List returned (if bools all false)
        return_max: bool
            return max value of function if true
        return_min: bool
            return minx value of function if true
        return_absmax: bool
            return absolute max value of function if true

        Returns
        --------
        int
            Max, min or absmax value of the shear force function depending on which parameters are set.
        list of ints
            If x-coordinate(s) are specfied value of the shear force function at x-coordinate(s).
             
        Notes
        -----
        * Priority of query parameters is return_max, return_min, return_absmax, x_coord (if more than 1 of the parameters are specified).

        """

        return self._get_query_value(x_coord, sym_func = self._shear_forces, return_max = return_max, return_min = return_min, return_absmax=return_absmax )

    def get_normal_force(self, *x_coord,return_max=False,return_min=False,return_absmax=False):
        """Find the normal force(s) on the beam object.
        
        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be substituted into the equation.
            List returned (if bools all false)
        return_max: bool
            return max value of function if true
        return_min: bool
            return minx value of function if true
        return_absmax: bool
            return absolute max value of function if true
         
        Returns
        --------
        int
            Max, min or absmax value of the normal force function depending on which parameters are set.
        list of ints
            If x-coordinate(s) are specfied value of the normal force function at x-coordinate(s).
                       
        Notes
        -----
        * Priority of query parameters is return_max, return_min, return_absmax, x_coord (if more than 1 of the parameters are specified).

        """
        return self._get_query_value(x_coord, sym_func =self._normal_forces, return_max = return_max, return_min = return_min, return_absmax=return_absmax )

    def get_deflection(self, *x_coord,return_max=False,return_min=False,return_absmax=False):
        """Find the deflection(s) on the beam object. 
        
        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be substituted into the equation.
            List returned (if bools all false)
        return_max: bool
            return max value of function if true
        return_min: bool
            return minx value of function if true
        return_absmax: bool
            return absolute max value of function if true
        
        Returns
        --------
        int
            Max, min or absmax value of the deflection function depending on which parameters are set.
        list of ints
            If x-coordinate(s) are specfied value of the deflection function at x-coordinate(s).
            
        Notes
        -----
        * Priority of query parameters is return_max, return_min, return_absmax, x_coord (if more than 1 of the parameters are specified).

        """

        return self._get_query_value(x_coord, sym_func =self._deflection_equation, return_max = return_max, return_min = return_min, return_absmax=return_absmax )


    #SECTION - PLOTTING
    def add_query_points(self, *x_coords):
        """Document the forces on a beam at position x_coord when plotting.

        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be queried on plot.

        """
        for x_coord in x_coords:
            if self._x0 <= x_coord <= self._x1:
                self._query.append(x_coord)
            else:
                return ValueError("Not a point on beam")

    def remove_query_points(self, *x_coords, remove_all=False):
        """Remove a query point added by add_query_points function.

        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be removed from query on plot.
        remove_all: boolean
            if true all query points will be removed.

        """
        if remove_all:
            self._query = []
            return None

        for x_coord in x_coords:
            if x_coord in self._query:
                self._query.remove(x_coord)
            else:
                return ValueError("Not an existing query point on beam")

    def plot_beam_external(self):
        """A wrapper of several plotting functions that generates a single figure with 2 plots corresponding respectively to:

        - a schematic of the loaded beam
        - reaction force diagram

        Returns
        -------
        figure : `plotly.graph_objs._figure.Figure`
            Returns a handle to a figure with the 2 subplots.

        """
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=("Beam schematic", "Reaction Forces")
        )

        fig = self.plot_beam_diagram(fig=fig, row=1, col=1)
        fig = self.plot_reaction_force(fig=fig, row=2, col=1)

        fig.update_xaxes(title_text='Beam Length (m)',row=2,col=1)

        fig.update_layout(
                        height=550, 
                        title={'text': "Beam External Conditions",'x':0.5},
                        showlegend=False,
                        hovermode='x')

        return fig

    def plot_beam_internal(self, reverse_x=False, reverse_y=False, switch_axes=False):
        """A wrapper of several plotting functions that generates a single figure with 4 plots corresponding respectively to:

        - normal force diagram,
        - shear force diagram, 
        - bending moment diagram, and
        - deflection diagram 

        Parameters
        ----------
        switch_axes: bool
            True if want the beam to be plotted along the y axis and beam equations to be plotted along the x axis.
        inverted: bool
            True if want to flip a function about the x axis.
        draw_reactions: bool
            True if want to show the reaction forces in the beam schematic

        Returns
        -------
        figure : `plotly.graph_objs._figure.Figure`
            Returns a handle to a figure with the 4 subplots.

        """
        fig = make_subplots(rows=4, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.05,
                    subplot_titles=("Normal Force Diagram","Shear Force Diagram", "Bending Moment Diagram", "Deflection Diagram"))

        fig = self.plot_normal_force(reverse_x=reverse_x, reverse_y=reverse_y, fig=fig, row=1, col=1)
        fig = self.plot_shear_force(reverse_x=reverse_x, reverse_y=reverse_y, fig=fig, row=2, col=1)
        fig = self.plot_bending_moment(reverse_x=reverse_x, reverse_y=reverse_y, fig=fig, row=3, col=1)
        fig = self.plot_deflection(reverse_x=reverse_x, reverse_y=reverse_y, fig=fig, row=4, col=1)

        # fig.update_xaxes(title_text='Beam Length (m)',row=4,col=1)

        # fig.update_layout(
        #                 height=1000, 
        #                 title={'text': "Analysis Results",'x':0.5},
        #                 title_font_size = 24,
        #                 showlegend=False,
        #                 )

        return fig

    def plot_beam_diagram(self,fig=None,row=None,col=None):
        """Returns a schematic of the beam and all the loads applied on it

        Parameters
        ----------
        fig : bool, optional
            Figure to append subplot diagram too. If creating standalone figure then None, by default None
        row : int, optional
            row number if subplot, by default None
        col : int, optional
            column number if subplot, by default None

        Returns
        -------
        figure : `plotly.graph_objs._figure.Figure`
            Returns a handle to a figure with the beam schematic.
        """
        ##can do point loads as arrows, not sure about directional point loads though, hmm
            ##can have a set length for the arrow , say 50, and use trigonometry to find the x and y offset to achieve.
        ##for torques idk
        ##for 

        ##hoverinfo is skip to not show any default values, hover template is used to show only the x value and to not worry about the y value 
        data = go.Scatter(x=[self._x0,self._x1], y=[0,0],mode='lines',name="Beam_",line=dict(color='purple', width=2),hovertemplate="%{x} m",hoverinfo='skip')

        if fig and row and col:
            fig.add_trace(data,row=row,col=col)
        else:
            fig = go.Figure(data=data)
            ##Hovermode x makes two hover labels appear if they are at the same point (default setting means only see the last updated point)
            fig.update_layout(title_text="Beam Schematic", title_font_size=24,showlegend=False,hovermode='x',title_x=0.5)
            fig.update_xaxes(title_text='Beam Length (m)')
            ##visible false means y axis doesnt show, fixing range means wont zoom in y direction
        
        fig.update_yaxes(visible=False, range =[-3,3], fixedrange=True)


        #for each support append to figure to have the shapes/traces needed for the drawing
        if row and col:
            for support in self._supports:
                fig = draw_support(fig,support,row=row,col=col)

            for load in self._loads:
                fig = draw_force(fig,load,row=row,col=col)
                fig = draw_load_hoverlabel(fig,load,row=row,col=col)
        else:
            for support in self._supports:
                fig = draw_support(fig,support)

            for load in self._loads:
                fig = draw_force(fig,load)
                fig = draw_load_hoverlabel(fig,load)

        return fig

    def plot_reaction_force(self,fig=None,row=None,col=None):
        """Returns a plot of the beam with reaction forces.        
        
        Parameters
        ----------
        fig : bool, optional
            Figure to append subplot diagram too. If creating standalone figure then None, by default None
        row : int, optional
            row number if subplot, by default None
        col : int, optional
            column number if subplot, by default None

        Returns
        -------
        figure : `plotly.graph_objs._figure.Figure`
            Returns a handle to a figure with reaction forces.
        """
        ##if a figure is passed it is for the subplot
        ##append everything to it rather than creating a new plot.
        data = go.Scatter(
            x=[self._x0,self._x1], 
            y=[0,0],
            mode='lines',
            name="Beam",
            line=dict(color='purple', width=2),
            hovertemplate="%{x} m",
            hoverinfo='skip'
            )
        
        
        if fig and row and col:
            fig.add_trace(data,row=row,col=col)
        else:
            fig = go.Figure(data=data)

            ##Hovermode x makes two hover labels appear if they are at the same point (default setting means only see the last updated point)
            fig.update_layout(title_text="Reaction Forces", title_font_size=30,showlegend=False,hovermode='x',title_x=0.5)
            fig.update_xaxes(title_text='Beam Length (m)')

        ##visible false means y axis doesnt show, fixing range means wont zoom in y direction
        fig.update_yaxes(visible=False, range =[-3,3], fixedrange=True)

        for position, values in self._reactions.items():
            x_ = round(values[0],3)
            y_ = round(values[1],3)
            m_ = round(values[2],3)

            if abs(x_)>0 or abs(y_)>0 or abs(m_) > 0:
                if row and col:
                    fig = draw_reaction_hoverlabel(fig, reactions = [x_,y_,m_], x_sup=position,row=row,col=col)

                    if abs(x_) > 0:
                        fig = draw_force(fig,PointLoadH(x_,position),row=row,col=col)
                    if abs(y_) > 0:
                        fig = draw_force(fig,PointLoadV(y_,position),row=row,col=col)
                    if abs(m_) > 0:
                        fig = draw_force(fig,PointTorque(m_,position),row=row,col=col)
                else:
                    fig = draw_reaction_hoverlabel(fig, reactions = [x_,y_,m_], x_sup=position)

                    if abs(x_) > 0:
                        fig = draw_force(fig,PointLoadH(x_,position))
                    if abs(y_) > 0:
                        fig = draw_force(fig,PointLoadV(y_,position))
                    if abs(m_) > 0:
                        fig = draw_force(fig,PointTorque(m_,position))

        return fig

    def plot_normal_force(self, reverse_x=False, reverse_y=False, fig=None,row=None,col=None):
        """Returns a plot of the normal force as a function of the x-coordinate.

        Parameters
        ----------
        reverse_x : bool, optional
            reverse the x axes, by default False
        reverse_y : bool, optional
            reverse the y axes, by default False
        fig : bool, optional
            Figure to append subplot diagram too. If creating standalone figure then None, by default None
        row : int, optional
            row number if subplot, by default None
        col : int, optional
            column number if subplot, by default None

        Returns
        -------
        figure : `plotly.graph_objs._figure.Figure`
            Returns a handle to a figure with the normal force diagram.
        """

        xlabel = 'Beam Length'
        ylabel = 'Normal Force'
        xunits = 'm'
        yunits = 'kN'
        title = "Normal Force Plot"
        color = "red"

        fig = self.plot_analytical(self._normal_forces,color,title,xlabel,ylabel,xunits,yunits,reverse_x,reverse_y, fig=fig, row=row, col=col)
        return fig

    def plot_shear_force(self, reverse_x=False, reverse_y=False, fig=None,row=None,col=None):
        """Returns a plot of the shear force as a function of the x-coordinate.

        Parameters
        ----------
        reverse_x : bool, optional
            reverse the x axes, by default False
        reverse_y : bool, optional
            reverse the y axes, by default False
        fig : bool, optional
            Figure to append subplot diagram too. If creating standalone figure then None, by default None
        row : int, optional
            row number if subplot, by default None
        col : int, optional
            column number if subplot, by default None

        Returns
        -------
        figure : `plotly.graph_objs._figure.Figure`
            Returns a handle to a figure with the shear force diagram.
        """

        xlabel = 'Beam Length'
        ylabel = 'Shear Force'
        xunits = 'm'
        yunits = 'kN'
        title = "Shear Force Plot"
        color = "aqua"

        fig = self.plot_analytical(self._shear_forces,color,title,xlabel,ylabel,xunits,yunits,reverse_x,reverse_y, fig=fig, row=row, col=col)

        return fig

    def plot_bending_moment(self, reverse_x=False, reverse_y=False, switch_axes=False,fig=None,row=None,col=None):
        """Returns a plot of the bending moment as a function of the x-coordinate.

        Parameters
        ----------
        reverse_x : bool, optional
            reverse the x axes, by default False
        reverse_y : bool, optional
            reverse the y axes, by default False
        fig : bool, optional
            Figure to append subplot diagram too. If creating standalone figure then None, by default None
        row : int, optional
            row number if subplot, by default None
        col : int, optional
            column number if subplot, by default None

        Returns
        -------
        figure : `plotly.graph_objs._figure.Figure`
            Returns a handle to a figure with the bending moment diagram.
        """

        xlabel = 'Beam Length'
        ylabel = 'Bending Moment'
        xunits = 'm'
        yunits = 'kN.m'
        title = "Bending Moment Plot"
        color = "lightgreen"
        fig = self.plot_analytical(self._bending_moments,color,title,xlabel,ylabel,xunits,yunits,reverse_x,reverse_y,fig=fig, row=row, col=col)

        return fig

    def plot_deflection(self, reverse_x=False, reverse_y=False, fig=None,row=None,col=None):
        """Returns a plot of the beam deflection as a function of the x-coordinate.

        Parameters
        ----------
        reverse_x : bool, optional
            reverse the x axes, by default False
        reverse_y : bool, optional
            reverse the y axes, by default False
        fig : bool, optional
            Figure to append subplot diagram too. If creating standalone figure then None, by default None
        row : int, optional
            row number if subplot, by default None
        col : int, optional
            column number if subplot, by default None

        Returns
        -------
        figure : `plotly.graph_objs._figure.Figure`
            Returns a handle to a figure with the deflection diagram.
        """

        xlabel = 'Beam Length'
        ylabel = 'Deflection'
        xunits = 'm'
        yunits = 'mm'
        title = "Deflection Plot"
        color = "blue"
        fig = self.plot_analytical(self._deflection_equation,color,title,xlabel,ylabel,xunits,yunits,reverse_x,reverse_y, fig=fig, row=row, col=col)

        return fig

    def plot_analytical(self, sym_func,color="blue",title="",xlabel="",ylabel="",xunits="",yunits="",reverse_x=False,reverse_y=False,fig=None,row=None,col=None):
        """
        Auxiliary function for plotting a sympy.Piecewise analytical function.

        Parameters
        -----------
        sym_func: sympy function
            symbolic function using the variable x
        color: str
            color to be used for plot, default blue.
        title: str
            title to show above the plot, optional
        xlabel: str
            physical variable displayed on the x-axis. Example: "Length"
        ylabel: str
            physical variable displayed on the y-axis. Example: "Shear force"
        xunits: str
            physical unit to be used for the x-axis. Example: "m"
        yunits: str
            phsysical unit to be used for the y-axis. Example: "kN"
        reverse_x : bool, optional
            reverse the x axes, by default False
        reverse_y : bool, optional
            reverse the y axes, by default False
        fig : bool, optional
            Figure to append subplot diagram too. If creating standalone figure then None, by default None
        row : int, optional
            row number if subplot, by default None
        col : int, optional
            column number if subplot, by default None
 

        Returns
        -------
        figure : `plotly.graph_objs._figure.Figure`
            Returns a handle to a figure with the deflection diagram.
        """
        x_vec = np.linspace(self._x0, self._x1, int(1000))  ## numpy array for x positions closely spaced (allow for graphing)
        y_lam = lambdify(x, sym_func, "numpy")                                          ##transform sympy expressions to lambda functions which can be used to calculate numerical values very fast (with numpy)
        y_vec = np.array([y_lam(t) for t in x_vec])   
                                          ##np.array for y values created 
                                          ##np.array for y values created 
        data = go.Scatter(
            x=x_vec.tolist(),
            y=y_vec.tolist(),
            mode='lines',
            line=dict(color=color, width=1),
            fill='tozeroy',
            )

        if row and col and fig:
            fig = fig.add_trace(data,row=row,col=col)
        else:
            fig = go.Figure(data=data)
            fig.update_layout(title_text=title, title_font_size=30)
            fig.update_xaxes(title_text=str(xlabel+" ("+str(xunits)+")"))

        if row and col:
            fig.update_yaxes(title_text=str(ylabel+" ("+str(yunits)+")"),row=row,col=col)
            fig.update_yaxes(autorange="reversed",row=row,col=col) if reverse_y else None
            fig.update_xaxes(autorange="reversed",row=row,col=col) if reverse_x else None
        else:
            fig.update_yaxes(title_text=str(ylabel+" ("+str(yunits)+")"))
            fig.update_yaxes(autorange="reversed") if reverse_y else None
            fig.update_xaxes(autorange="reversed") if reverse_x else None

        for q_val in self._query:
            q_res = self._get_query_value(q_val, sym_func)
            if q_res <0:
                    ay = 40
            else:
                ay = -40

            annotation = dict(
                x=q_val, y=q_res,
                text=f"{str(q_val)}<br>{str(q_res)}",
                showarrow=True,
                arrowhead=1,
                xref='x',
                yref='y',
                ax=0,
                ay=ay
            )
            if row and col:
                fig.add_annotation(annotation,row=row,col=col)
            else:
                fig.add_annotation(annotation)

        return fig

    def _update_loads(self):
        self._distributed_forces_x = [self._create_distributed_force(f) for f in self._distributed_loads_x()]
        self._distributed_forces_y = [self._create_distributed_force(f) for f in self._distributed_loads_y()]

    def _create_distributed_force(self, load: DistributedLoadH or DistributedLoadV, shift: bool=True):
        """
        Create a sympy.Piecewise object representing the provided distributed load.

        :param expr: string with a valid sympy expression.
        :param interval: tuple (x0, x1) containing the extremes of the interval on
        which the load is applied.
        :param shift: when set to False, the x-coordinate in the expression is
        referred to the left end of the beam, instead of the left end of the
        provided interval.
        :return: sympy.Piecewise object with the value of the distributed load.
        """
        expr, interval = load
        x0, x1 = interval
        expr = sympify(expr)
        if shift:
            expr.subs(x, x - x0)
        return Piecewise((0, x < x0), (0, x > x1), (expr, True))

    def _effort_from_pointload(self, load: PointLoadH or PointLoadV or PointTorque):
        """
        Create a sympy.Piecewise object representing the shear force caused by a
        point load.

        :param value: float or string with the numerical value of the point load.
        :param coord: x-coordinate on which the point load is applied.
        :return: sympy.Piecewise object with the value of the shear force produced
        by the provided point load.
        """
        value, coord = load
        return Piecewise((0, x < coord), (value, True))

    def _point_loads_x(self):
        for f in self._loads:
            if isinstance(f, PointLoadH):
                yield f
            elif isinstance(f,PointLoad):
                force, position, angle = f
                force_x =  sympify(force*cos(radians(angle))).evalf(10)     ##when angle = 0 then force is 1
                
                if abs(round(force_x,3)) > 0:
                    yield PointLoadH(force_x,position)

    def _point_loads_y(self):
        for f in self._loads:
            if isinstance(f, PointLoadV):
                yield f
            elif isinstance(f,PointLoad):
                force, position, angle = f
                force_y =  sympify(force*sin(radians(angle))).evalf(10)     ###when angle = 90 then force is 1
                
                if abs(round(force_y,3)) > 0:
                    yield PointLoadV(force_y,position)

    def _distributed_loads_x(self):
        for f in self._loads:
            if isinstance(f, DistributedLoadH):
                yield f

    def _distributed_loads_y(self):
        for f in self._loads:
            if isinstance(f, DistributedLoadV):
                yield f

    def _point_torques(self):
        for f in self._loads:
            if isinstance(f, PointTorque):
                yield f

    def __str__(self):
        return f"""--------------------------------
        <Beam>
        length = {self._x0}
        loads = {str(len(self._loads))}"""

    def __repr__(self):
        return f"<Beam({self._x0})>"


if __name__ == "__main__":
    beam = Beam(5)

    a = Support(0,(1,1,1))
    b = Support(5,(0,1,0))
    beam.add_supports(a,b)

    load_1 = PointLoad(5,1,90)
    load_2 = PointTorque(2,2)
    load_3 = TrapezoidalLoad((0,1),(0,1))
    beam.add_loads(load_1,load_2,load_3)
        
    beam.add_query_points(1,2,3)


    beam.analyse()
    beam.plot_shear_force()

