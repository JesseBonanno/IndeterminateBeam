from sympy.abc import x
from sympy import oo, integrate, SingularityFunction, sympify, cos, sin

from data_validation import (
    assert_length, 
    assert_number, 
    assert_positive_number, 
    assert_strictly_positive_number
)

from math import radians

class Load:
    def _integrate_load(self):
        # self._x0 represents w(x), load as a function of x
        self._x1 = integrate(self._x0, x) #NF

        # self._y0 represents w(x), load as a function of x
        self._y1 = integrate(self._y0, x) #SF


# Main load types

class PointTorque(Load):
    """Point clockwise torque, described by a tuple of floats:
    (torque, coord).

    Parameters:
    -----------
    torque: float
        Torque in kN.m
    coord: float
        x coordinate of torque on beam

    Examples
    --------
    # 30 kN·m (clockwise) torque at x=4 m
    >>> motor_torque = PointTorque(30, 4)
    """

    
    def __init__(self, force = 0, coord=0):
        assert_number(force, 'force')
        assert_positive_number(coord, 'coordinate')
        
        self._x0 = 0
        self._y0 = force * SingularityFunction(x, coord, -1)

        self._integrate_load()
        self._m0 = force

        self.position = coord
        self.force = force

class PointLoad(Load):
    """Point load described by a tuple of floats: (force, coord, angle).

    Parameters:
    -----------
    Force: float
        Force in kN
    coord: float
        x coordinate of load on beam
    angle: float
        angle of point load where:
        - 0 degrees is purely horizontal +ve
        - 90 degrees is purely vertical +ve
        - 180 degrees is purely horizontal -ve of force sign specified.


    Examples
    --------
    # 10 kN towards the right at x=9 m
    >>> external_force = PointLoad(10, 9, 90)
    # 30 kN downwards at x=3 m
    >>> external_force = PointLoad(-30, 3, 0)
    >>> external_force
    PointLoad(force=-30, coord=3, angle=0)
    """
    
    def __init__(self, force = 0, coord=0, angle=0):
        assert_number(force, 'force')
        assert_positive_number(coord, 'coordinate')
        assert_number(angle, 'angle')

        force_x = force * cos(radians(angle)).evalf(8)
        force_y = force * sin(radians(angle)).evalf(8)

        if abs(round(force_x,5)) > 0:
            self._x0 = force_x * SingularityFunction(x, coord, -1)
        else: 
            self._x0 = 0
        
        if abs(round(force_y,5)) > 0:
            self._y0 = force_y * SingularityFunction(x, coord, -1)
        else: 
            self._y0 = 0

        self._integrate_load()
        self._m0 = integrate(self._y0 * x, (x, 0, coord))

        self.position = coord
        self.force = force
        self.angle = angle

class UDL(Load):
    
    def __init__(self, force = 0, span =(0, 0), angle = 0):
        
        # Validate span input
        assert_length(span, 2, 'span')
        assert_positive_number(span[0], 'span start')
        assert_strictly_positive_number(span[1]-span[0], 'span start minus span end')

        # validate angle input
        assert_number(angle, 'angle')

        # validate force input
        assert_number(force, 'force')

        force_x = force * cos(radians(angle)).evalf(8)
        force_y = force * sin(radians(angle)).evalf(8)

        expr = SingularityFunction(x, span[0], 0) - SingularityFunction(x, span[1], 0)

        if abs(round(force_x,5)) > 0:
            self._x0 = force_x * expr
        else: 
            self._x0 = 0
        
        if abs(round(force_y,5)) > 0:
            self._y0 = force_y * expr
        else: 
            self._y0 = 0

        self._integrate_load()
        self._m0 = integrate(self._y0 * x, (x, 0, span[1]))

        self.expr = expr
        self.span = span
        self.force = force
        self.angle = angle

class TrapezoidalLoad(Load):

    def __init__(self, force = (0,0), span =(0, 0), angle = 0):
        # Validate force input
        assert_length(force, 2, 'force')

        # check if UDL (not sure if this code will work properly)
        if force[0] == force [1]:
            return UDL(force[0], span, angle)

        # Validate span input
        assert_length(span, 2, 'span')
        assert_positive_number(span[0], 'span start')
        assert_strictly_positive_number(span[1]-span[0], 'span start minus span end')

        # validate angle input
        assert_number(angle, 'angle')

        #turn trapezoid into a triangle + rectangle
        UDL_component = force[0] * (
            SingularityFunction(x, span[0], 0) 
            - SingularityFunction(x, span[1], 0)
        )

        # express values for triangular load distribution
        xa, xb = span[0], span[1]
        a, b = 0, force[1] - force[0]
        slope = b / (span[1] - span[0])

        force_x = cos(radians(angle)).evalf(10)
        force_y = sin(radians(angle)).evalf(10)

        triangular_component = sum([
            + slope * SingularityFunction(x, xa, 1),
            - b * SingularityFunction(x, xb, 0),
            - slope * SingularityFunction(x, xb, 1),
        ])

        expr = triangular_component + UDL_component

        if abs(round(force_x,8)) > 0:
            self._x0 = force_x * expr
        else: 
            self._x0 = 0
        
        if abs(round(force_y,8)) > 0:
            self._y0 = force_y * expr
        else: 
            self._y0 = 0

        self._integrate_load()
        self._m0 = integrate(self._y0 * x, (x, 0, span[1]))

        self.expr = expr
        self.span = span
        self.force = force
        self.angle = angle

class DistributedLoad(Load):
    """Distributed load, described by its functional form, application 
    interval and the angle of the load relative to the beam.

    Parameters:
    -----------
    expr: sympy expression
        Sympy expression of the distributed load function expressed
        using variable x which represents the beam x-coordinate.
        Requires quotation marks around expression.
    span: tuple of floats
        A tuple containing the starting and ending coordinate that
         the function is applied to.
    angle: float
        angle of point load where:
        - 0 degrees is purely horizontal +ve
        - 90 degrees is purely vertical +ve
        - 180 degrees is purely horizontal -ve of force sign specified.
    Examples
    --------
    # Linearly growing load for 0<x<2 m
    >>> snow_load = DistributedLoad("10*x+5", (0, 2),90)
    """

    def __init__(self, expr, span =(0, 0), angle = 0):
        try:
            expr = sympify(expr)
        except:
            print("Can not convert expression to sympy function. \
            Function should only contain variable x, should be \
            encapsulated by quotations, and should have * between x \
            and coefficients i.e 2 * x rather than 2x")
        
        # Validate span input
        assert_length(span, 2, 'span')
        assert_positive_number(span[0], 'span start')
        assert_strictly_positive_number(span[1]-span[0], 'span start minus span end')

        # validate angle input
        assert_number(angle, 'angle')

        force_x = cos(radians(angle)).evalf(10)
        force_y = sin(radians(angle)).evalf(10)

        if abs(round(force_x,8)) > 0:
            self._x0 = force_x * expr
        else: 
            self._x0 = 0
        
        if abs(round(force_y,8)) > 0:
            self._y0 = force_y * expr
        else: 
            self._y0 = 0

        self._integrate_load()
        self._m0 = integrate(self._y0 * x, (x, 0, span[1]))
        
        self.span = span
        self.expr = expr
        self.angle = angle

# simplified load types- vertical and horizontal direction classes

class PointLoadV(PointLoad):
    def __init__(self, force = 0, coord = 0):
        super().__init__(force,coord,angle=90)

class PointLoadH(PointLoad):
    def __init__(self, force = 0, coord = 0):
        super().__init__(force,coord,angle=0)

class DistributedLoadV(DistributedLoad):
    def __init__(self, expr = 0, span = (0,0)):
        super().__init__(expr, span, angle=90)

class DistributedLoadH(DistributedLoad):
    def __init__(self, expr = 0, span = (0,0)):
        super().__init__(expr, span, angle=0)
