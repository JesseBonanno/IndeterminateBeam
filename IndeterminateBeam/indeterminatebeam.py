"""Main module that contains the main classes Support and Beam, and auxiliary classes PointLoadH,
PointLoadV, DistributedLoadH, and DistributedLoadV, PointLoad and Support.

Example
-------
>>> beam = Beam(6)
>>> a = Support()
>>> c = Support(6,(0,1,0))
>>> beam.add_supports(a,c)
>>> beam.add_loads(PointLoadV(-15,3))
>>> beam.add_query_points(2,4)
>>> beam.analyse()
>>> beam.plot()
"""

from collections import namedtuple
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Polygon, Rectangle, RegularPolygon, Wedge
from matplotlib.collections import PatchCollection
import numpy as np
import os
from sympy import integrate, lambdify, Piecewise, sympify, symbols, linsolve, sin, cos
from sympy.abc import x
from math import radians 


class Support:
    """
    A class to represent a support.

    Attributes:
    ---------------
        coord: (int)
            x coordinate of support on a beam (default 0)
        DOF: (tuple of 3 bools) 
            Degrees of freedom on a beam for movement in x, y and bending, 
            1 represents fixed and 0 represents free (default (1,1,1))

    Examples
    --------
    >>> Support(0, (1,1,1))  ##creates a fixed suppot at location 0
    >>> Support(5, (1,1,0))  ##creatse a pinned support at location 5
    >>> Support(5.54, (0,1,0))  ##creates a roller support at location 5.54
    """

    def __init__(self, coord=0, DOF=(1,1,1)):
        """
        Constructs all the necessary attributes for the support object

        Attributes:
        -----------
        coord: (int)
            x coordinate of support on a beam (default 0)
        DOF: (tuple of 3 bools) 
            Degrees of freedom on a beam for movement in x, y and bending, 
            1 represents fixed and 0 represents free (default (1,1,1))

        """
        if type(coord) not in [int, float]:
            raise ValueError("coord should be an integer or a float")
        if coord<0:
            raise ValueError("coord should be greater than 0")

        self._position = coord

        for a in DOF:
            if a not in [0,1]:
                raise ValueError("The provided DOF, must be a tuple of BOOLS of length 3")
        if len(DOF) != 3:
            raise ValueError("The provided DOF, must be a tuple of BOOLS of length 3")

        self._DOF = DOF
        self._id = None
        self._translation = []
        for a in DOF:
            if a ==1:
                self._translation.append("Fixed")
            else:
                self._translation.append("Free")


    def __str__(self):
        return f"""--------------------------------
        id = {self._id}
        position = {float(self._position)}
        Translation_x = {self._translation[0]}
        Translation_y = {self._translation[1]}
        Translation_M = {self._translation[2]} """

    def __repr__(self):
        if self._id:
            return f"<support, id = {self._id}>"
        return "<Support>"


##Section 1 - Loading Class definitions 

class PointLoad(namedtuple("PointLoad", "force, coord, angle")):
    """Point load described by a tuple of floats: (force, coord, angle).

    Force: force in kN
    coord: x coordinate of load on beam
    angle: angle of point load in range 0 to 180 where: 
        - 0 degrees is purely vertical
        - 90 degrees is purely horizontal
        - 180 degrees is purely vertical acting in the opposite direction


    Examples
    --------
    >>> external_force = PointLoad(10, 9, 90)  # 10 kN towards the right at x=9 m
    >>> external_force = PointLoad(-30, 3, 0)  # 30 kN downwards at x=3 m
    >>> external_force
    PointLoad(force=-30, coord=3, angle=0)
    """

class PointLoadV(namedtuple("PointLoadV", "force, coord")):
    """Vertical point load described by a tuple of floats: (force, coord).
    
    Force: force in kN
    coord: x coordinate of load on beam

    Examples
    --------
    >>> external_force = PointLoadV(-30, 3)  # 30 kN downwards at x=3 m
    >>> external_force
    PointLoadV(force=-30, coord=3)
    """

class PointLoadH(namedtuple("PointLoadH", "force, coord")):
    """Horizontal point load described by a tuple of floats: (force, coord).

    Force: force in kN
    coord: x coordinate of load on beam

    Examples
    --------
    >>> external_force = PointLoadH(10, 9)  # 10 kN towards the right at x=9 m
    >>> external_force
    PointLoadH(force=10, coord=9)
    """

class DistributedLoadV(namedtuple("DistributedLoadV", "expr, span")):
    """Distributed vertical load, described by its functional form and application interval.

    Examples
    --------
    >>> snow_load = DistributedLoadV("10*x+5", (0, 2))  # Linearly growing load for 0<x<2 m
    >>> trapezoidal_load = DistributedLoadV("-5 + 10 * x), (1,2)) # Linearly growing load starting at 5kN/m ending at 15kn/m 
    >>> UDL = DistributedLoadV(10, (1,3))
    """

class DistributedLoadH(namedtuple("DistributedLoadH", "expr, span")):
    """Distributed horizontal load, described by its functional form and application interval.
    """

class PointTorque(namedtuple("PointTorque", "torque, coord")):
    """Point clockwise torque, described by a tuple of floats: (torque, coord).

    Examples
    --------
    >>> motor_torque = PointTorque(30, 4)  # 30 kN·m (clockwise) torque at x=4 m
    
    """


class Beam:
    """
    Represents a one-dimensional beam that can take axial and tangential loads.

    Parameters
    ----------
    span : float or int
        Length of the beam span. Must be positive, and the pinned and rolling
        supports can only be placed within this span. The default value is 10.
    E: float or int
        Youngs modulus for the beam. The default value is 200 000 MPa, which
        is the youngs modulus for steel.
    I: float or int
        Second moment of area for the beam about the z axis. The default value
        is 60 000 000 mm4.
    
    Through the method `add_loads`, a Beam object can accept a list of:
    
    * PointLoad objects, and/or
    * DistributedLoad objects.

    Through the method `add_supports`, a Beam object can accept a list of Supports.

    Through the method `analyse` the unknown forces on the Beam object can be calculated.

    Notes
    -----
    * The default units package units for length, force and bending moment 
      (torque) are respectively (m, kN, kN·m)
    """
     
    def __init__(self, span: float=10, E = 2*10**5, I= 9.05*10**6):
        """Initializes a Beam object of a given length. """

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
        self._reactions = {'x':[], 'y':[], 'm':[]}
        
        self._E = E
        self._I = I
    
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
            if type(load[1]) ==tuple:
                left = min(load[1])
                right = max(load[1])
            else:
                left = right = load[1]    
            if self._x0 > left or right > self._x1:
                return ValueError(f"{load[1]} is not a point on beam")

            supported_load_types = (DistributedLoadH, DistributedLoadV, PointLoadH, PointLoadV, PointTorque)
            if isinstance(load, supported_load_types):
                self._loads.append(load)
            elif isinstance(load,PointLoad):
                force, position, angle = load
                load_x = PointLoadH(sympify(force*sin(radians(angle))).evalf(10), position)     ###when angle = 90 then force is 1
                load_y = PointLoadV(sympify(force*cos(radians(angle))).evalf(10), position)     ##when angle = 0 then force is 1
                if abs(load_x.force) >0:
                    self._loads.append(load_x)
                if abs(load_y.force) >0:
                    self._loads.append(load_y)
            else:
                raise TypeError("The provided loads must be one of the supported types: {0}".format(supported_load_types))
        self._update_loads()

    def remove_loads(self, *loads):
        """Remove an arbitrary list of (point- or distributed) loads from the beam.

        Parameters
        ----------
        loads : iterable
            An iterable containing DistributedLoad or PointLoad objects to
            be removed from the Beam object. If object not on beam then does nothing.

        """
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
                raise ValueError("support must be of type class Support")
            
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

    def remove_supports(self, *ids):
        """Remove an arbitrary list of supports (Support objects) from the beam.

        Parameters
        ----------
        ids : iterable
            An iterable containing either Support objects or Support object ids to
            be removed from the Beam object. If support not on beam then does nothing.

        """
        for support in self._supports:
            if support._id in ids or support in ids:
                self._supports.remove(support)
    ##does not display error if ask to remove somethign that isnt there, is this okay?

    def get_support_details(self):
        """Print out a readable summary of all supports on the beam. """

        print(f"There are {str(len(self._supports))} supports:",end ='\n\n')
        for support in self._supports:
            print(support, end ='\n\n')


    ##SECTION - ANALYSE
    def check_determinancy(self):
        """Check the determinancy of the beam. If 0 then beam is determinate."""

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

        x0, x1 = self._x0, self._x1

        ##create unknown sympy variables
        unknowns_x = [(symbols("x_"+str(a._id)), a._position) for a in self._supports if a._DOF[0] !=0]
        unknowns_y = [(symbols("y_"+str(a._id)), a._position) for a in self._supports if a._DOF[1] !=0]
        unknowns_m = [(symbols("m_"+str(a._id)), a._position) for a in self._supports if a._DOF[2] !=0]

        ##need to know locations where moment is fixed 
        dv_0 = [a._position for a in self._supports if a._DOF[2] == 1]

        ##need to know locations where y is fixed
        v_0  = [a._position for a in self._supports if a._DOF[1] == 1]

        ##locations where x is fixed
        sup_x = [a._position for a in self._supports if a._DOF[0] == 1]
        sup_x.sort()

        ##grab the set of all the sympy vectors and change to a list
        unknowns = [a[0] for a in unknowns_y + unknowns_m]

        ##external reaction equations
        F_Rx = sum(integrate(load, (x, x0, x1)) for load in self._distributed_forces_x) + \
            sum(f.force for f in self._point_loads_x()) + \
            sum([a[0] for a in unknowns_x])   

        F_Ry = sum(integrate(load, (x, x0, x1)) for load in self._distributed_forces_y) + \
               sum(f.force for f in self._point_loads_y()) + \
               sum([a[0] for a in unknowns_y])

        M_R = sum(integrate(load * x, (x, x0, x1)) for load in self._distributed_forces_y) + \
            sum(f.force * f.coord for f in self._point_loads_y()) + \
            sum(-1 * f.torque for f in self._point_torques()) + \
            sum([a[0] for a in unknowns_m]) + \
            sum([f[0]*f[1] for f in unknowns_y]) 
        

        ##internal beam equations
        C1, C2 = symbols('C1'), symbols('C2')
        unknowns = unknowns + [C1] +[C2]

        ##normal forces is same concept as shear forces only 
        N_i = sum(self._effort_from_pointload(f) for f in self._point_loads_x()) + \
               sum(self._effort_from_pointload(PointLoadH(*a)) for a in unknowns_x) 

        F_i = sum(integrate(load, x) for load in self._distributed_forces_y) + \
               sum(self._effort_from_pointload(f) for f in self._point_loads_y()) + \
               sum(self._effort_from_pointload(PointLoadV(*a)) for a in unknowns_y)  

        M_i = integrate(F_i,x) + \
            sum(self._effort_from_pointload(PointTorque(*a)) for a in unknowns_m) + \
            sum(self._effort_from_pointload(f) for f in self._point_torques())

             #with respect to x, + constants but the constants are the M at fixed supports

        dv_EI = integrate(M_i, x) + C1

        v_EI = integrate(dv_EI,x) + C2

        
        ##equations , create a lsit fo equations
        equations = [F_Ry,M_R]

        for position in dv_0:
            equations.append(dv_EI.subs(x,position))

        for position in v_0:
            equations.append(v_EI.subs(x,position))

        ##equation for normal forces, only for indeterminate in x
        equations_x = [F_Rx]
        unknowns_xx = [a[0] for a in unknowns_x if a[0]!=0]

        if len(sup_x)>1:
            for position in sup_x[1:]: ##dont consider the starting point? only want to look between supports and not at cantilever sections i think
                equations_x.append(
                    integrate(N_i, (x,sup_x[0], position)))
            
        if unknowns_xx == [] and equations_x ==[0]:
            solutions_x = []

        elif len(unknowns_xx) > len(equations_x): ##is this even possible
            print(f"""Unstable in resolving axial forces:
            equations = {len(equations_x)}
            unknowns  = {len(unknowns_xx)}""")
            return 1

        if len(unknowns) > len(equations):
            print(f"""unstable in resolving forces for y and m:
            equations = {len(equations)}
            unknowns  = {len(unknowns)}""")
            return 2
        
        solutions = list(linsolve(equations, unknowns))
        solutions_x = list(linsolve(equations_x, unknowns_xx))

        solutions = [a for a in solutions[0] + solutions_x[0]]

        solution_dict = dict(zip(unknowns+unknowns_xx, solutions))
        self._solution_dict = solution_dict
        self._reactions = {'x': [], 'y': [], 'm': []}

        for var, ans in solution_dict.items():
            v_EI = v_EI.subs(var,ans) ##complete deflection equation
            M_i  = M_i.subs(var,ans)  ##complete moment equation
            F_i  = F_i.subs(var,ans)  ##complete shear force equation
            N_i = N_i.subs(var,ans)   ##complete normal force equation

            if var not in [C1,C2]:
                vec, num = str(var).split('_')
                position = [a._position for a in self._supports if a._id == int(num)][0]
                self._reactions[vec].append((float(ans), position))

        ##moment unit is kn.m, dv_EI kn.m2, v_EI Kn.m3 --> *10^3, *10^9 to get base units 
        ## EI unit is N/mm2 , mm4 --> N.mm2
        self._shear_forces = F_i
        self._bending_moments = M_i
        self._deflection_equation = v_EI * 10 **12 / ( self._E * self._I )
        self._normal_forces = N_i
    
        return 0

    ##SECTION - QUERY VALUE
    def _get_query_value(self, x_coord, sym_func, return_max=False, return_min=False, return_absmax=False):  ##check if sym_func is the sum of the functions already in plot_analytical
        """Find the value of a function at position x_coord.

        Note: Priority of query parameters is return_max, return_min, return_absmax, x_coord.

        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be substituted into the equation.
            List returned (if bools all false)
        sym_func: sympy function?
            The function to be analysed
        return_max: bool
            return max value of function if true
        return_min: bool
            return minx value of function if true
        return_absmax: bool
            return absolute max value of function if true

        """
        if type(sym_func) == list:
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

         Note: Priority of query parameters is return_max, return_min, return_absmax, x_coord.

        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be substituted into the equation.
            List returned (if bools all false)
        sym_func: sympy function?
            The function to be analysed
        return_max: bool
            return max value of function if true
        return_min: bool
            return minx value of function if true
        return_absmax: bool
            return absolute max value of function if true"""

        return self._get_query_value(x_coord, sym_func = self._bending_moments, return_max = return_max, return_min = return_min, return_absmax=return_absmax )

    def get_shear_force(self, *x_coord,return_max=False,return_min=False, return_absmax=False):
        """Find the shear force(s) on the beam object. 

        Note: Priority of query parameters is return_max, return_min, return_absmax, x_coord.

        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be substituted into the equation.
            List returned (if bools all false)
        sym_func: sympy function?
            The function to be analysed
        return_max: bool
            return max value of function if true
        return_min: bool
            return minx value of function if true
        return_absmax: bool
            return absolute max value of function if true"""

        return self._get_query_value(x_coord, sym_func = self._shear_forces, return_max = return_max, return_min = return_min, return_absmax=return_absmax )

    def get_normal_force(self, *x_coord,return_max=False,return_min=False,return_absmax=False):
        """Find the normal force(s) on the beam object.
        
        Note: Priority of query parameters is return_max, return_min, return_absmax, x_coord.

        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be substituted into the equation.
            List returned (if bools all false)
        sym_func: sympy function?
            The function to be analysed
        return_max: bool
            return max value of function if true
        return_min: bool
            return minx value of function if true
        return_absmax: bool
            return absolute max value of function if true"""
        return self._get_query_value(x_coord, sym_func =self._normal_forces, return_max = return_max, return_min = return_min, return_absmax=return_absmax )

    def get_deflection(self, *x_coord,return_max=False,return_min=False,return_absmax=False):
        """Find the deflection(s) on the beam object. 
        
        Note: Priority of query parameters is return_max, return_min, return_absmax, x_coord.

        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be substituted into the equation.
            List returned (if bools all false)
        sym_func: sympy function?
            The function to be analysed
        return_max: bool
            return max value of function if true
        return_min: bool
            return minx value of function if true
        return_absmax: bool
            return absolute max value of function if true"""

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

    def remove_query_points(self, *x_coords):
        """Remove a query point added by add_query_points function.

        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be removed from query on plot.

        """
        for x_coord in x_coords:
            if x_coord in self._query:
                self._query.remove(x_coord)
            else:
                return ValueError("Not an existing query point on beam")

    def plot(self, switch_axes=False, inverted=False):
        """Generates a single figure with 4 plots corresponding respectively to:

        - a schematic of the loaded beam
        - normal force diagram,
        - shear force diagram, and
        - bending moment diagram.

        These plots can be generated separately with dedicated functions.

        Parameters
        ----------
        switch_axes: bool
            True if want the beam to be plotted along the y axis and beam equations to be plotted along the x axis.
        inverted: bool
            True if want to flip a function about the x axis.

        Returns
        -------
        figure : `~matplotlib.figure.Figure`
            Returns a handle to a figure with the 3 subplots: Beam schematic, 
            shear force diagram, and bending moment diagram.

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
        self.plot_beam_diagram(ax1)

        ax2 = fig.add_subplot(5, 1, 2)
        self.plot_normal_force(ax2, inverted=inverted)

        ax3 = fig.add_subplot(5, 1, 3)
        self.plot_shear_force(ax3, inverted=inverted)

        ax4 = fig.add_subplot(5, 1, 4)
        self.plot_bending_moment(ax4, inverted=inverted)

        ax5 = fig.add_subplot(5, 1, 5)
        self.plot_deflection(ax5, inverted=inverted)

        return fig

    def plot_beam_diagram(self, ax=None):
        """Returns a schematic of the beam and all the loads applied on it.
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
        self._draw_beam_schematic(ax)
        return ax.get_figure()

    def plot_normal_force(self, ax=None, switch_axes=False, inverted=False,maxmin_hline: bool = True, maxmin_vline:bool=False):
        """Returns a plot of the normal force as a function of the x-coordinate.
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
        self._plot_analytical(ax, -1* self._bending_moments, **plot04_params)
        return ax.get_figure()

    def plot_deflection(self, ax= None, switch_axes=False, inverted=False,maxmin_hline: bool = True, maxmin_vline:bool=False):
        """Returns a plot of the beam deflection as a function of the x-coordinate.
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

        :param ax: a matplotlib.Axes object where the data is to be plotted.
        :param x_vec: array-like, support where the provided symbolic function will be plotted
        :param sym_func: symbolic function using the variable x
        :param title: title to show above the plot, optional
        :param maxmin_hline: when set to False, the extreme values of the function are not displayed
        :param xunits: str, physical unit to be used for the x-axis. Example: "m"
        :param yunits: str, phfsysical unit to be used for the y-axis. Example: "kN"
        :param xlabel: str, physical variable displayed on the x-axis. Example: "Length"
        :param ylabel: str, physical variable displayed on the y-axis. Example: "Shear force"
        :param color: color to be used for the shaded area of the plot. No shading if not provided
        :return: a matplotlib.Axes object representing the plotted data.

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

    def _draw_beam_schematic(self, ax):
        """Auxiliary function for plotting the beam object and its applied loads.
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
        for load in ply + self._reactions['y']:
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
        plx = [a for a in self._point_loads_x()]
        for load in plx + self._reactions['x']:
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
        plm = [a for a in self._point_torques()]
        for load in plm + self._reactions['m']:
            xc = load[1]
            yc = (beam_top + beam_bottom) / 2.0
            width = yspan * 0.17
            height = xspan * 0.05
            arc_len= 180

            if load[0] < 0:
                start_angle = 90
                endX = xc + (height/2)*np.cos(np.radians(arc_len + start_angle))
                endY = yc + (width/2)*np.sin(np.radians(arc_len + start_angle))
            else:
                start_angle = 270
                endX = xc + (height/2)*np.cos(np.radians(start_angle))
                endY = yc + (width/2)*np.sin(np.radians(start_angle))

            orientation = start_angle + arc_len
            arc = Arc([xc, yc], width, height, angle=start_angle, theta2=arc_len, capstyle='round', linestyle='-', lw=2.5, color="darkgreen")
            arrow_head = RegularPolygon((endX, endY), 3, height * 0.35, np.radians(orientation), color="darkgreen")
            ax.add_patch(arc)
            ax.add_patch(arrow_head)
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


if __name__ == "__main__":
    # ##intialise a beam object
    beam_1 = Beam(5)            ##intialises a 5m long beam (assuming E = 2*10^5, I = )
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
    beam_1.plot()
