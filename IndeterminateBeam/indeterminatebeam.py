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
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Polygon, Rectangle, RegularPolygon, Wedge, Circle
from matplotlib.collections import PatchCollection
import numpy as np
import os
from sympy import integrate, lambdify, Piecewise, sympify, symbols, linsolve, sin, cos,oo
from sympy.abc import x
from math import radians 
from data_validation import assert_number, assert_positive_number

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
            Degrees of freedom that are fixed on a beam for movement in x, y and bending, 1 
            represents that a reaction force exists and 0 represents free (default (1,1,1))
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


##Section 1 - Loading Class definitions 

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
    _reactions_plot_tuples: dictionary of lists
        A dictionary where the first key is either 'x', 'y' or 'm'. Each value associated with
        these keys is a list of tuples where the tuples are (force, position) and can be thought
        of as PointLoadV (for 'y'), PointLoadH (for 'x') or PointTorque (for 'm') objects 
        although it isnt explicitly defined.
    reactions: dictionary of lists
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

        assert_positive_number(span, 'span')
        assert_positive_number(E, "Young's Modulus (E)")
        assert_positive_number(I, 'Second Moment of Area (I)')
        assert_positive_number(A, 'Area (A)')


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
        self._reactions_plot_tuple = {'x':[], 'y':[], 'm':[]}
        self.reactions = {}
        
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
            if isinstance(load[1],tuple):
                left = min(load[1])
                right = max(load[1])
            else:
                left = right = load[1]    
            if self._x0 > left or right > self._x1:
                raise ValueError(f"{load[1]} is not a point on beam")

            supported_load_types = (DistributedLoadH, DistributedLoadV, PointLoadH, PointLoadV, PointTorque)

            if isinstance(load, supported_load_types):
                self._loads.append(load)

            elif isinstance(load,PointLoad):
                force, position, angle = load
                assert_number(angle, 'angle')
                if angle > 180 or angle <0:
                    raise ValueError('Angle should be between 0 and 180 degrees')
                load_y = PointLoadV(sympify(force*sin(radians(angle))).evalf(10), position)     ###when angle = 90 then force is 1
                load_x = PointLoadH(sympify(force*cos(radians(angle))).evalf(10), position)     ##when angle = 0 then force is 1
                if abs(round(load_x.force,3)) >0:
                    self._loads.append(load_x)
                if abs(round(load_y.force,3)) >0:
                    self._loads.append(load_y)
            else:
                raise TypeError("The provided loads must be one of the supported types: {0}".format(supported_load_types))

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
            if isinstance(load,PointLoad):
                force, position, angle = load
                load_x = PointLoadH(sympify(force*sin(radians(angle))).evalf(10), position)     ###when angle = 90 then force is 1
                load_y = PointLoadV(sympify(force*cos(radians(angle))).evalf(10), position)     ##when angle = 0 then force is 1
                if load_x in self._loads:
                    self._loads.remove(load_x)
                if load_y in self._loads:
                    self._loads.remove(load_y)
            elif load in self._loads:
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
            
            if self._x0 > support._position or support._position > self._x1:
                return ValueError("Not a point on beam")

            elif self._supports == []:
                support._id = 1
                self._supports.append(support)

            elif support._position not in [x._position for x in self._supports]:
                support._id = self._supports[-1]._id + 1
                self._supports.append(support)
            else:
                raise ValueError(f"This coordinate {support._position} already has a support associated with it")

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
        F_Rx = sum(integrate(load, (x, x0, x1)) for load in self._distributed_forces_x) + \
            sum(f.force for f in self._point_loads_x()) + \
            sum([a[0] for a in unknowns_x.values()])   

        F_Ry = sum(integrate(load, (x, x0, x1)) for load in self._distributed_forces_y) + \
               sum(f.force for f in self._point_loads_y()) + \
               sum([a[0] for a in unknowns_y.values()])

        ##moments taken at the left of the beam, anti-clockwise is positive
        M_R = sum(integrate(load * x, (x, x0, x1)) for load in self._distributed_forces_y) + \
            sum(f.force * f.coord for f in self._point_loads_y()) + \
            sum([p*v[0] for p,v in unknowns_y.items()]) + \
            sum(f.torque for f in self._point_torques()) + \
            sum([a[0] for a in unknowns_m.values()])

        ##internal beam equations
        C1, C2 = symbols('C1'), symbols('C2')
        unknowns_ym = unknowns_ym + [C1] +[C2]

        ##normal forces is same concept as shear forces only no distributed for now.
        N_i = sum(self._effort_from_pointload(f) for f in self._point_loads_x()) + \
               sum(self._effort_from_pointload(PointLoadH(v[0],p)) for p,v in unknowns_x.items()) 

        ## shear forces, an internal force acting down would be considered positive by adopted convention
        ##hence if the sum of forces on the beam are all positive, our internal force would also be positive due to difference in convention
        F_i = sum(integrate(load, x) for load in self._distributed_forces_y) + \
               sum(self._effort_from_pointload(f) for f in self._point_loads_y()) + \
               sum(self._effort_from_pointload(PointLoadV(v[0],p)) for p,v in unknowns_y.items())  

        ##bending moments at internal point means we are now looking left along the beam when we take our moments (vs when we did external external reactions and we looked right)
        ##An anti-clockwise moment is adopted as positive internally. 
        ## Hence we need to consider a postive for our shear forces and negative for our moments by our sign convention
        M_i = (integrate(F_i,x)) - \
            sum(self._effort_from_pointload(PointTorque(v[0],p)) for p,v in unknowns_m.items()) - \
            sum(self._effort_from_pointload(f) for f in self._point_torques())

             #with respect to x, + constants but the constants are the M at fixed supports

        dv_EI = integrate(M_i, x) + C1

        v_EI = integrate(dv_EI,x) + C2

        
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
                    integrate(N_i, (x,x_0[0], position))*10**3 /(self._E*self._A) + \
                    unknowns_x[start][0]/unknowns_x[start][1] - \
                    unknowns_x[position][0]/unknowns_x[position][1]   ##represents elongation displacment on right
                    )
        
        ##compute analysis with linsolve
        solutions_ym = list(linsolve(equations_ym, unknowns_ym))[0]
        solutions_xx = list(linsolve(equations_xx, unknowns_xx))[0]
        
        solutions = [a for a in solutions_ym + solutions_xx]

        solution_dict = dict(zip(unknowns_ym+unknowns_xx, solutions))

        self._reactions_plot_tuple = {'x': [], 'y': [], 'm': []}

        ##substitue in value instead of variable in functions
        for var, ans in solution_dict.items():
            v_EI = v_EI.subs(var,ans) ##complete deflection equation
            M_i  = M_i.subs(var,ans)  ##complete moment equation
            F_i  = F_i.subs(var,ans)  ##complete shear force equation
            N_i = N_i.subs(var,ans)   ##complete normal force equation

            ##create self._reactions_plot_tuple to allow for plotting of reaction forces if wanted.
            if var not in [C1,C2]:
                vec, num = str(var).split('_')
                position = [a._position for a in self._supports if a._id == int(num)][0]
                self._reactions_plot_tuple[vec].append((float(ans), position))

        ##create self.reactions, to allow for user to get reactions at a point      
        self.reactions = {a._position : [0,0,0] for a in self._supports}
        for i, a in enumerate(['x','y','m']):
            if self._reactions_plot_tuple[a]:
                for f,p in self._reactions_plot_tuple[a]:
                    self.reactions[p][i] = round(f,5)

        ##moment unit is kn.m, dv_EI kn.m2, v_EI Kn.m3 --> *10^3, *10^9 to get base units 
        ## EI unit is N/mm2 , mm4 --> N.mm2
        self._shear_forces = F_i
        self._bending_moments = M_i
        self._deflection_equation = v_EI * 10 **12 / ( self._E * self._I )   ## a positive moment indicates a negative deflection, i thought??
        self._normal_forces = N_i

    ##SECTION - QUERY VALUE
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

        x_vec = np.linspace(self._x0, self._x1, int(min(self._x1 * 1000 + 1, 1e4)))  ## numpy array for x positions closely spaced (allow for graphing)                                      ##i think lambdify is needed to let the function work with numpy
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

    def plot(self, switch_axes=False, inverted=False,draw_reactions=False):
        """A wrapper of several plotting functions that generates a single figure with 5 plots corresponding respectively to:

        - a schematic of the loaded beam
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
        figure : `~matplotlib.figure.Figure`
            Returns a handle to a figure with the 5 subplots: Beam schematic, normal force diagram,
            shear force diagram, bending moment diagram, and deflection diagram.

        """
        if switch_axes:
            fig = plt.figure(figsize=(14, 6))
            fig.subplots_adjust(wspace=0.8)

            # ax1 = fig.add_subplot(1, 5, 1)
            # self.plot_beam_diagram(ax1, switch_axes = switch_axes)

            ax2 = fig.add_subplot(1, 5, 2)
            self.plot_normal_force(ax2,switch_axes = True, inverted=inverted,maxmin_hline= False, maxmin_vline=True)

            ax3 = fig.add_subplot(1, 5, 3)
            self.plot_shear_force(ax3, switch_axes = True, inverted=inverted,maxmin_hline= False, maxmin_vline=True)

            ax4 = fig.add_subplot(1, 5, 4)
            self.plot_bending_moment(ax4, switch_axes = True, inverted=inverted,maxmin_hline= False, maxmin_vline=True)

            ax5 = fig.add_subplot(1, 5, 5)
            self.plot_deflection(ax5, switch_axes = True, inverted=inverted,maxmin_hline= False, maxmin_vline=True)

            return fig
            

        fig = plt.figure(figsize=(6, 14))
        fig.subplots_adjust(hspace=0.8)

        ax1 = fig.add_subplot(5, 1, 1)
        self.plot_beam_diagram(ax1, draw_reactions=draw_reactions) ##inverted hasnt been completed for beam diagram

        ax2 = fig.add_subplot(5, 1, 2)
        self.plot_normal_force(ax2, inverted=inverted)

        ax3 = fig.add_subplot(5, 1, 3)
        self.plot_shear_force(ax3, inverted=inverted)

        ax4 = fig.add_subplot(5, 1, 4)
        self.plot_bending_moment(ax4, inverted=inverted)

        ax5 = fig.add_subplot(5, 1, 5)
        self.plot_deflection(ax5, inverted=inverted)

        return fig

    def plot_beam_diagram(self, ax=None, draw_reactions=False):
        """Returns a schematic of the beam and all the loads applied on it.

        Parameters
        ----------
        draw_reactions: bool
            True if want to show the reaction forces in the beam schematic

        Returns
        -------
        figure : `~matplotlib.figure.Figure`
            Returns a handle to a figure with the beam schematic.
        """

        plot01_params = {'ylabel': "Beam loads", 'yunits': r'kN / m',
                         # 'xlabel':"Beam axis", 'xunits':"m",
                         'color': "g",
                         'inverted': True,
                         'query': False}
        if ax is None:
            ax = plt.figure(figsize=(6, 2.5)).add_subplot(1,1,1)
        ax.set_title("Loaded beam diagram")
        self._plot_analytical(ax, sum(self._distributed_forces_y), **plot01_params)
        self._draw_beam_schematic(ax, draw_reactions=draw_reactions)
        return ax.get_figure()

    def plot_normal_force(self, ax=None, switch_axes=False, inverted=False,maxmin_hline: bool = True, maxmin_vline:bool=False):
        """Returns a plot of the normal force as a function of the x-coordinate.
        
        Parameters
        ----------
        switch_axes: bool
            True if want the beam to be plotted along the y axis and beam equations to be plotted along the x axis.
        inverted: bool
            True if want to flip a function about the x axis.
        maxmin_hline: bool
            True if want a horizontal line displaying the maximum and minimum value reached on the y-axis
        maxmin_vline: bool 
            True if want a vertical line displaying the maximum and minimum value reached on the x-axis
        
        Returns
        -------
        figure : `~matplotlib.figure.Figure`
            Returns a handle to a figure with the normal force diagram.
        """
        plot02_params = {'ylabel': "Normal force", 'yunits': r'kN',
                         # 'xlabel':"Beam axis", 'xunits':"m",
                         'color': "b",
                         'switch_axes': switch_axes,
                         'inverted': inverted,
                         'maxmin_hline':maxmin_hline,
                         'maxmin_vline':maxmin_vline}
        if ax is None:
            if switch_axes:
                ax = plt.figure(figsize=(2.5, 6)).add_subplot(1,1,1)
            else:
                ax = plt.figure(figsize=(6, 2.5)).add_subplot(1,1,1)
        self._plot_analytical(ax, self._normal_forces, **plot02_params)
        return ax.get_figure()

    def plot_shear_force(self, ax=None, switch_axes=False, inverted=False,maxmin_hline: bool = True, maxmin_vline:bool=False):
        """Returns a plot of the shear force as a function of the x-coordinate.

        Parameters
        ----------
        switch_axes: bool
            True if want the beam to be plotted along the y axis and beam equations to be plotted along the x axis.
        inverted: bool
            True if want to flip a function about the x axis.
        maxmin_hline: bool
            True if want a horizontal line displaying the maximum and minimum value reached on the y-axis
        maxmin_vline: bool 
            True if want a vertical line displaying the maximum and minimum value reached on the x-axis

        Returns
        -------
        figure : `~matplotlib.figure.Figure`
            Returns a handle to a figure with the shear force diagram.
        """

        plot03_params = {'ylabel': "Shear force", 'yunits': r'kN',
                          'xlabel':"Beam axis", 'xunits':"m",
                         'color': "r",
                         'switch_axes': switch_axes,
                         'inverted': inverted,
                         'maxmin_hline':maxmin_hline,
                         'maxmin_vline':maxmin_vline}
        if ax is None:
            if switch_axes:
                ax = plt.figure(figsize=(2.5, 6)).add_subplot(1,1,1)
            else:
                ax = plt.figure(figsize=(6, 2.5)).add_subplot(1,1,1)
        self._plot_analytical(ax, self._shear_forces, **plot03_params)
        return ax.get_figure()

    def plot_bending_moment(self, ax=None, switch_axes=False, inverted=False,maxmin_hline: bool = True, maxmin_vline:bool=False):
        """Returns a plot of the bending moment as a function of the x-coordinate.

        Parameters
        ----------
        switch_axes: bool
            True if want the beam to be plotted along the y axis and beam equations to be plotted along the x axis.
        inverted: bool
            True if want to flip a function about the x axis.
        maxmin_hline: bool
            True if want a horizontal line displaying the maximum and minimum value reached on the y-axis
        maxmin_vline: bool 
            True if want a vertical line displaying the maximum and minimum value reached on the x-axis

        Returns
        -------
        figure : `~matplotlib.figure.Figure`
            Returns a handle to a figure with the bending moment diagram.
        """

        plot04_params = {'ylabel': "Bending moment", 'yunits': r'kN·m',
                         'xlabel': "Beam axis", 'xunits': "m",
                         'color': "y",
                         'switch_axes': switch_axes,
                         'inverted': inverted,
                         'maxmin_hline':maxmin_hline,
                         'maxmin_vline':maxmin_vline}
        if ax is None:
            if switch_axes:
                ax = plt.figure(figsize=(2.5, 6)).add_subplot(1,1,1)
            else:
                ax = plt.figure(figsize=(6, 2.5)).add_subplot(1,1,1)
        self._plot_analytical(ax, self._bending_moments, **plot04_params)
        return ax.get_figure()

    def plot_deflection(self, ax= None, switch_axes=False, inverted=False,maxmin_hline: bool = True, maxmin_vline:bool=False):
        """Returns a plot of the beam deflection as a function of the x-coordinate.

        Parameters
        ----------
        switch_axes: bool
            True if want the beam to be plotted along the y axis and beam equations to be plotted along the x axis.
        inverted: bool
            True if want to flip a function about the x axis.
        maxmin_hline: bool
            True if want a horizontal line displaying the maximum and minimum value reached on the y-axis
        maxmin_vline: bool 
            True if want a vertical line displaying the maximum and minimum value reached on the x-axis

        Returns
        -------
        figure : `~matplotlib.figure.Figure`
            Returns a handle to a figure with the deflection diagram.
        """

        plot05_params = {'ylabel': "Deflection", 'yunits': r'mm',
                         'xlabel': "Beam axis", 'xunits': "m",
                         'color': "c",
                         'switch_axes': switch_axes,
                         'inverted': inverted,
                         'maxmin_hline':maxmin_hline,
                         'maxmin_vline':maxmin_vline}
        if ax is None:
            if switch_axes:
                ax = plt.figure(figsize=(2.5, 6)).add_subplot(1,1,1)
            else:
                ax = plt.figure(figsize=(6, 2.5)).add_subplot(1,1,1)
        self._plot_analytical(ax, self._deflection_equation, **plot05_params)
        return ax.get_figure()

    def _plot_analytical(self, ax: plt.axes, sym_func, title: str = "", maxmin_hline: bool = True, maxmin_vline:bool=False, xunits: str = "",
                        yunits: str = "", xlabel: str = "", ylabel: str = "", color=None, inverted=False, query = True, switch_axes=False):
        """
        Auxiliary function for plotting a sympy.Piecewise analytical function.

        Parameters
        -----------
        ax: matplotlib.Axes
            A matplotlib.Axes object where the data is to be plotted
        sym_func: sympy function
            symbolic function using the variable x
        title: str
            title to show above the plot, optional
        maxmin_hline: bool
            when set to False, the extreme values of the function are not displayed
        xunits: str
            physical unit to be used for the x-axis. Example: "m"
        yunits: str
            phsysical unit to be used for the y-axis. Example: "kN"
        xlabel: str
            physical variable displayed on the x-axis. Example: "Length"
        ylabel: str
            physical variable displayed on the y-axis. Example: "Shear force"
        color: str
            color to be used for the shaded area of the plot. No shading if not provided

        Returns
        -------
        figure : `~matplotlib.figure.Figure`
            A matplotlib.Axes object representing the plotted data
        """
        x_vec = np.linspace(self._x0, self._x1, int(min(self._x1 * 1000 + 1, 1e4)))  ## numpy array for x positions closely spaced (allow for graphing)
        y_lam = lambdify(x, sym_func, "numpy")                                          ##i think lambdify is needed to let the function work with numpy
        y_vec = np.array([y_lam(t) for t in x_vec])   
                                          ##np.array for y values created 
        original_yunits = yunits

        if switch_axes:
            _label = xlabel
            _units = xunits
            _vec = x_vec[:]

            xlabel = ylabel
            xunits = yunits
            x_vec = y_vec[:]

            ylabel = _label
            yunits = _units
            y_vec = _vec[:]

        if inverted:
            y_vec *= -1                                                                 ##would flip the graph about y


        if color:
            if switch_axes:
                a, b = y_vec[0], y_vec[-1]
                verts = [(0,a)] + list(zip(x_vec, y_vec)) + [(0,b)]
            else:
                a, b = x_vec[0], x_vec[-1]
                verts = [(a, 0)] + list(zip(x_vec, y_vec)) + [(b, 0)]                           ##verts is a list of tuples makign up the graph (starting and ending to help close it)
            poly = Polygon(verts, facecolor=color, edgecolor='0.5', alpha=0.4)
            ax.add_patch(poly)

        if maxmin_vline:
            tol = 1e-3
            
            if abs(max(x_vec)) > tol:
                ax.axvline(x=max(x_vec), linestyle='--', color="g", alpha=0.5)
                max_idy = x_vec.argmax()
                plt.annotate('${:0.1f}'.format((x_vec[max_idy])).rstrip('0').rstrip('.') + " $ {}".format(original_yunits),
                            xy=(x_vec[max_idy], y_vec[max_idy]), xytext=(8, 0), xycoords=('data', 'data'),
                            textcoords='offset points', size=12)

            if abs(min(x_vec)) > tol:
                ax.axvline(x=min(x_vec), linestyle='--', color="g", alpha=0.5)
                min_idy = x_vec.argmin()
                plt.annotate('${:0.1f}'.format((x_vec[min_idy])).rstrip('0').rstrip('.') + " $ {}".format(original_yunits),
                            xy=(x_vec[min_idy], y_vec[min_idy]), xytext=(8, 0), xycoords=('data', 'data'),
                            textcoords='offset points', size=12)

        if maxmin_hline:
            tol = 1e-3

            if abs(max(y_vec)) > tol:
                ax.axhline(y=max(y_vec), linestyle='--', color="g", alpha=0.5)
                max_idx = y_vec.argmax()
                plt.annotate('${:0.1f}'.format(y_vec[max_idx]).rstrip('0').rstrip('.') + " $ {}".format(original_yunits),
                            xy=(x_vec[max_idx], y_vec[max_idx]), xytext=(8, 0), xycoords=('data', 'data'),
                            textcoords='offset points', size=12)

            if abs(min(y_vec)) > tol:
                ax.axhline(y=min(y_vec), linestyle='--', color="g", alpha=0.5)
                min_idx = y_vec.argmin()
                plt.annotate('${:0.1f}'.format(y_vec[min_idx]).rstrip('0').rstrip('.') + " $ {}".format(original_yunits),
                            xy=(x_vec[min_idx], y_vec[min_idx]), xytext=(8, 0), xycoords=('data', 'data'),
                            textcoords='offset points', size=12)

        if query:
            for q_val in self._query:
                if switch_axes:
                    ax.axhline(y=q_val, linestyle='--', color="g", alpha=0.5)
                else:
                    ax.axvline(x=q_val, linestyle='--', color="g", alpha=0.5)
                ##need to get values by a differnt method -- cant use id
                q_res = self._get_query_value(q_val, sym_func)
                if switch_axes:
                    plt.annotate('${:0.1f}'.format(q_res).rstrip('0').rstrip('.') + " $ {}".format(original_yunits),
                                xy=(q_res, q_val*(1-2*inverted)), xytext=(0, 0), xycoords=('data', 'data'),
                                textcoords='offset points', size=8)
                else:
                    plt.annotate('${:0.1f}'.format(q_res*(1-2*inverted)).rstrip('0').rstrip('.') + " $ {}".format(original_yunits),
                                xy=(q_val, q_res*(1-2*inverted)), xytext=(0, 0), xycoords=('data', 'data'),
                                textcoords='offset points', size=8)


        if switch_axes:
            yspan = y_vec.max() - y_vec.min()
            ax.set_ylim([y_vec.min() - 0.01 * yspan, y_vec.max() + 0.01 * yspan])
        else:
            xspan = x_vec.max() - x_vec.min()
            ax.set_xlim([x_vec.min() - 0.01 * xspan, x_vec.max() + 0.01 * xspan])
            

        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)

        if title:
            ax.set_title(title)

        if xlabel or xunits:
            ax.set_xlabel('{} [{}]'.format(xlabel, xunits))

        if ylabel or yunits:
            ax.set_ylabel("{} [{}]".format(ylabel, yunits))

        return ax

    def _draw_beam_schematic(self, ax, draw_reactions=False):
        """Auxiliary function for plotting the beam object and its applied loads.
        
        Parameters
        ----------
        draw_reactions: bool
            True if want to show the reaction forces in the beam schematic
        """

        # Adjust y-axis
        ymin, ymax = -5, 5
        ylim = (min(ax.get_ylim()[0], ymin), max(ax.get_ylim()[1], ymax))
        ax.set_ylim(ylim)
        xspan = ax.get_xlim()[1] - ax.get_xlim()[0]
        yspan = ylim[1] - ylim[0]

        # Draw beam body
        beam_left, beam_right = self._x0, self._x1
        beam_length = beam_right - beam_left
        beam_height = yspan * 0.06
        beam_bottom = -(0.75) * beam_height
        beam_top = beam_bottom + beam_height
        beam_body = Rectangle(
            (beam_left, beam_bottom), beam_length, beam_height, fill=True,
            facecolor="brown", clip_on=False, alpha=0.7
        )
        ax.add_patch(beam_body)

        # Markers at beam supports
        supports = []
        for support in self._supports:
            supports.append(Polygon(np.array([support._position + 0.01*xspan*np.array((-1, -1, 0, 1, 1)), 
                                            beam_bottom + 0.05*np.array((-1.5, -1,0,-1, -1.5))*yspan]).T))
            # rolling_support = [Polygon(np.array([self.rolling_support + 0.01*xspan*np.array((-1, 0, 1)), 
            #                                     beam_bottom + 0.05*np.array((-1,0,-1))*yspan]).T),
            #                    Polygon(np.array([self.rolling_support + 0.01*xspan*np.array((-1, -1, 1, 1)), 
            #                                     beam_bottom + 0.05*np.array((-1.5,-1.25, -1.25, -1.5))*yspan]).T)]
        support_patch = PatchCollection(supports, facecolor="black")
        ax.add_collection(support_patch)

        # Draw arrows at point loads
        arrowprops = dict(arrowstyle="simple", color="darkgreen", shrinkA=0.1, mutation_scale=18)
        ply = [a for a in self._point_loads_y()]
        plx = [a for a in self._point_loads_x()]
        plm = [a for a in self._point_torques()]
        
        if draw_reactions:
            ply += self._reactions_plot_tuple['y']
            plx += self._reactions_plot_tuple['x']
            plm += self._reactions_plot_tuple['m']

        for load in ply:
            x0 = x1 = load[1]
            if load[0] < 0:
                y0, y1,y2 = beam_top, beam_top + 0.17 * yspan, beam_top + 0.17 * yspan + 0.6
            else:
                y0, y1,y2 = beam_bottom, beam_bottom - 0.17 * yspan,  beam_bottom - 0.17 * yspan - 0.6
            ax.annotate("",
                        xy=(x0, y0), xycoords='data',
                        xytext=(x1, y1), textcoords='data',
                        arrowprops=arrowprops
                        )
            ax.annotate("",
                        xy=(x0, y0), xycoords='data',
                        xytext=(x1, y1), textcoords='data',
                        arrowprops=arrowprops
                        )
            plt.annotate('${:0.1f}'.format(load[0]).rstrip('0').rstrip('.') + " $ {}".format('kN'),
                                xy=(x1, y2), xytext=(0, 0), xycoords=('data', 'data'),
                                textcoords='offset points', size=8)
        

        for load in plx:
            x0 = load[1]
            y0 = y1 = (beam_top + beam_bottom) / 2.0
            if load[0] < 0:
                x1 = x0 + xspan * 0.05
                x2 = x1 + 0.05
            else:
                x1 = x0 - xspan * 0.05
                x2 = x1 - 0.4
            ax.annotate("",
                        xy=(x0, y0), xycoords='data',
                        xytext=(x1, y1), textcoords='data',
                        arrowprops=arrowprops
                        )
            plt.annotate('${:0.1f}'.format(load[0]).rstrip('0').rstrip('.') + " $ {}".format('kN'),
                    xy=(x2, y1), xytext=(0, 0), xycoords=('data', 'data'),
                    textcoords='offset points', size=8)
        
        # Draw a round arrow at point torques

        for load in plm:
            xc = load[1]
            yc = (beam_top + beam_bottom) / 2.0
            width = yspan * 0.17
            height = xspan * 0.05
            arc_len= 180

            if load[0] > 0:
                start_angle = 90
                endX = xc + (height/2)*np.cos(np.radians(arc_len + start_angle))
                endY = yc + (width/2)*np.sin(np.radians(arc_len + start_angle))
            else:
                start_angle = 270
                endX = xc + (height/2)*np.cos(np.radians(start_angle))
                endY = yc + (width/2)*np.sin(np.radians(start_angle))

            orientation = start_angle + arc_len
            arc = Arc([xc, yc], width, height, angle=start_angle, theta2=arc_len, capstyle='round', linestyle='-', lw=2.5, color="blue")
            arrow_head = RegularPolygon((endX, endY), 3, height * 0.5, np.radians(orientation), color="blue")
            centre_point = Circle((xc,yc), yc/8, color="blue")
            ax.add_patch(arc)
            ax.add_patch(arrow_head)
            ax.add_patch(centre_point)
            plt.annotate('${:0.1f}'.format(load[0]).rstrip('0').rstrip('.') + " $ {}".format('kN.m'),
                    xy=(xc, beam_top+height), xytext=(0, 0), xycoords=('data', 'data'),
                    textcoords='offset points', size=8)

        ax.axes.get_yaxis().set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        # ax.tick_params(left="off")

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

    def _point_loads_y(self):
        for f in self._loads:
            if isinstance(f, PointLoadV):
                yield f

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
        unknowns = {str(sum([a._DOF for a in self._supports]))}"""
#loads = {str(len(self._loads))}

    def __repr__(self):
        return f"<Beam({self._x0})>"


if __name__ == "__main__":
    # ##intialise a beam object
    beam_1 = Beam(5)            ##intialises a 5m long beam (assuming E = 2*10^5, I = )
    beam_1.add_query_points(1,3,5)
    beam_1.remove_query_points(3)
    
    beam_2 = Beam(5, E=1, I=1)

    ##create support objects
    a = Support(0,(1,1,1))      ##defines a fixed support at point 0m point
    b = Support(2,(0,1,0))      ##defines a roller support restaint only in the y direction at 2m point
    c = Support(5,(1,1,0))      ##defines pinned support at 5m point

    ##add supports to beam object
    beam_1.add_supports(a,b,c)        ##create a statically indeterminate beam
    beam_2.add_supports(a,b,c)        ##intially create as a statically determinate beam
    beam_2.remove_supports(a)         ## remove support a to make beam statically determinate

    ##create load objects
    load_1 = PointLoad(1,3,45)
    load_2 = DistributedLoadV(2,(0,1))
    load_3 = PointTorque(3,4)

    ##add load objects to beams
    beam_1.add_loads(load_1,)
    beam_1.add_loads(load_2,load_3)
    beam_2.add_loads(load_1, load_2, load_3)
    beam_2.remove_loads((load_2,))

    ##compute solutions for beams
    print("TIME TO ANALYSE")
    beam_1.analyse()
    beam_2.analyse()
    print("ALL DONE")
