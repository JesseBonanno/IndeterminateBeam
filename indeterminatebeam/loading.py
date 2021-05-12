"""Module containing load classes."""

# Standard Libary Imports
from math import radians

# Third Party Imports
from sympy.abc import x
from sympy import oo, integrate, SingularityFunction, sympify, cos, sin, Piecewise

# Local application imports
from indeterminatebeam.data_validation import (
    assert_length,
    assert_number,
    assert_positive_number,
    assert_strictly_positive_number
)


class Load:
    """Load class from which all other types of loads inherit."""

    def _add_load_functions(self, angle, expr):
        """Convert the load as a function of x (w(x)) into:
        - Total vertical force
        - Total moment (about x = 0)
        - Shear force as a function of x
        - Normal force as a function of x

        Parameters
        ----------
        angle : float
            load angle
        expr : float
            value of load as function of x
        """
        # x and y vectors for force
        force_x = cos(radians(angle))
        force_y = sin(radians(angle))

        # self._x0 represents w(x), load as a function of x
        if abs(round(force_x, 8)) > 0:
            self._x0 = force_x * expr
        else:
            self._x0 = 0

        # self._y0 represents w(x), load as a function of x
        if abs(round(force_y, 8)) > 0:
            self._y0 = force_y * expr
        else:
            self._y0 = 0

        # self._x1 represents NF(x), normal force as function of x.
        self._x1 = integrate(self._x0, x)  # NF

        # self._y1 represents SF(x), shear force as function of x.
        self._y1 = integrate(self._y0, x)  # SF


class PointTorque(Load):
    """Point clockwise torque.

    Parameters:
    -----------
    force: float
        Torque load (default units N.m), (named force for consistency 
        with other load types)
    coord: float
        x coordinate of torque on beam (default units m)

    Examples
    ---------
    >>> # 30 N·m (anti-clockwise) torque at x = 4 m
    >>> motor_torque = PointTorque(30, 4)

    Note: Anti-clockwise is positive

    """

    def __init__(self, force=0, coord=0):
        # Data Validation.
        assert_number(force, 'force')
        assert_positive_number(coord, 'coordinate')

        # load as a function of x (non-directional)
        # the minus is to rectify sign convention, since
        # a positive shear causes a negative moment
        expr =  - force * SingularityFunction(x, coord, -2)

        # add load as a function of x (directional)
        # and add integration of this function to object.
        # angle 90 as moment only affects vertical direction.
        angle = 90
        self._add_load_functions(angle, expr)

        # self._m0 is moment induced by load about coord 0.
        self._m0 = force

        # Assign other inputs to load object
        self.position = coord
        self.force = force


class PointLoad(Load):
    """Point load.

    Parameters:
    -----------
    Force: float
        Force load (default units m)
    coord: float
        x coordinate of load on beam (default units m)
    angle: float
        angle of point load where:
        - 0 degrees is purely horizontal +ve
        - 90 degrees is purely vertical +ve
        - 180 degrees is purely horizontal -ve of force sign specified.

    Examples
    --------
    >>> # 100 N towards the right at x = 9 m
    >>> external_force = PointLoad(100, 9, 90)
    >>> # 300 N downwards at x = 3 m
    >>> external_force = PointLoad(-300, 3, 0)
    >>> external_force
        PointLoad(force=-300, coord=3, angle=0)
    """

    def __init__(self, force=0, coord=0, angle=0):
        # Data Validation for inputs
        assert_number(force, 'force')
        assert_positive_number(coord, 'coordinate')
        assert_number(angle, 'angle')

        # load as a function of x (non-directional)
        expr = force * SingularityFunction(x, coord, -1)

        # add load as a function of x (directional)
        # and add integration of this function to object
        self._add_load_functions(angle, expr)

        # self._m0 is moment induced by load about coord 0.
        force_y = sin(radians(angle))
        self._m0 = force * coord * force_y

        # Assign other inputs to load object
        self.position = coord
        self.force = force
        self.angle = angle


class UDL(Load):
    """Uniformly Distributed Load (UDL).

    Parameters
    ----------
    force : int, optional
        UDL load (default units N/m), by default 0
    span: tuple of floats
        A tuple containing the starting and ending coordinate that
        the UDL is applied to (default units m).
    angle: float
        angle of point load where:
        - 0 degrees is purely horizontal +ve
        - 90 degrees is purely vertical +ve
        - 180 degrees is purely horizontal -ve of force sign specified.

    Examples
    --------
    >>> # load of 1000 N/m from 1 m <= x <= 4 m (vertical)
    >>> self_weight = UDL(1000, (1, 4), 90)
    """

    def __init__(self, force=0, span=(0, 0), angle=0):

        # Validate span input
        assert_length(span, 2, 'span')
        assert_positive_number(span[0], 'span start')
        assert_strictly_positive_number(
            round(span[1] - span[0],5),
            'span start minus span end'
        )

        # validate angle input
        assert_number(angle, 'angle')

        # validate force input
        assert_number(force, 'force')

        # load as a function of x (non-directional)
        expr = force * (
            SingularityFunction(x, span[0], 0)
            - SingularityFunction(x, span[1], 0)
        )

        # add load as a function of x (directional)
        # and add integration of this function to object
        self._add_load_functions(angle, expr)

        # self._m0 is moment induced by load about coord 0.
        xa, length = span[0], span[1] - span[0]
        force_y = sin(radians(angle))

        self._m0 = force * length * (xa + length / 2) * force_y

        # Assign other inputs to load object
        self.expr = expr
        self.span = span
        self.force = force
        self.angle = angle


class TrapezoidalLoad(Load):
    """Trapezoidal Distributed Load.

    Parameters
    ----------
    force : tuple of floats
        A tuple containing the starting and ending loads of
        the trapezoidal load (default units N/m).
    span: tuple of floats
        A tuple containing the starting and ending coordinate that
        the trapezoidal load is applied to (default units m).
    angle: float
        angle of point load where:
        - 0 degrees is purely horizontal +ve
        - 90 degrees is purely vertical +ve
        - 180 degrees is purely horizontal -ve of force sign specified.

    Examples
    --------
    >>> # trapezoidal load starting at 2000 N/m at 1 m and ending at 3000 N/m
    >>> # at 4 m (vertical)
    >>> self_weight = UDL((2000, 3000), (1, 4), 90) 
    """

    def __init__(self, force=(0, 0), span=(0, 0), angle=0):
        # Validate force input
        assert_length(force, 2, 'force')

        # Validate span input
        assert_length(span, 2, 'span')
        assert_positive_number(span[0], 'span start')
        assert_strictly_positive_number(
            round(span[1] - span[0],5),
            'span start minus span end')

        # validate angle input
        assert_number(angle, 'angle')

        # Assign intermediate variables
        xa, xb = span[0], span[1]
        a, b = 0, force[1] - force[0]
        length = xb - xa

        # turn trapezoid into a triangle (1) + rectangle (2) for
        # load as a function of x (non-directional).
        # (1) UDL/rectangle Component
        UDL_component = force[0] * (
            SingularityFunction(x, span[0], 0)
            - SingularityFunction(x, span[1], 0)
        )

        # (2) triangular component
        if force[0] != force[1]:
            # express values for triangular load distribution
            slope = b / (span[1] - span[0])

            # Last two terms to deal with continuity past xb
            # triangular component is negative if slope is down,
            # as need to cut away from UDL. If slope is up/positive
            # then triangular component is positive as need to add to UDL.
            triangular_component = sum([
                + slope * SingularityFunction(x, xa, 1),
                - b * SingularityFunction(x, xb, 0),
                - slope * SingularityFunction(x, xb, 1),
            ])

        else:
            triangular_component = 0

        # load as a function of x (non-directional).
        expr = triangular_component + UDL_component

        # add load as a function of x (directional)
        # and add integration of this function to object
        self._add_load_functions(angle, expr)

        # self._m0 is moment induced by load about coord 0.
        UDL_m0 = (force[0] * length) * (xa + length / 2)
        triangle_m0 = (b * length / 2) * (xa + length * 2 / 3)
        force_y = sin(radians(angle))

        self._m0 = (UDL_m0 + triangle_m0) * force_y

        # Assign other inputs to load object
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
        Requires quotation marks around expression (default units in N/m).
    span: tuple of floats
        A tuple containing the starting and ending coordinate that
         the function is applied to (default units m).
    angle: float
        angle of point load where:
        - 0 degrees is purely horizontal +ve
        - 90 degrees is purely vertical +ve
        - 180 degrees is purely horizontal -ve of force sign specified.

    Examples
    --------
    >>> # Linearly growing load for 0 < x < 2 m
    >>> snow_load = DistributedLoad("10 * x + 5", (0, 2), 90)
    """

    def __init__(self, expr, span=(0, 0), angle=0):
        # Validate expr.
        try:
            expr = sympify(expr)
            expr = Piecewise((0, x < span[0]), (0, x > span[1]), (expr, True))
            
        except BaseException:
            print("Can not convert expression to sympy function. "+
            "Function should only contain variable x, should be " +
            "encapsulated by quotations, and should have * between x " +
            "and coefficients i.e 2 * x rather than 2x"
            )

        # Validate span input
        assert_length(span, 2, 'span')
        assert_positive_number(span[0], 'span start')
        assert_strictly_positive_number(
            round(span[1] - span[0],5),
            'span start minus span end')

        # validate angle input
        assert_number(angle, 'angle')

        # load as a function of x (directional).
        self._add_load_functions(angle, expr)

        # self._m0 is moment induced by load about coord 0.
        self._m0 = integrate(self._y0 * x, (x, 0, span[1]))

        # Assign other inputs to load object
        self.span = span
        self.expr = expr
        self.angle = angle

# simplified load types- vertical and horizontal direction classes

class PointLoadV(PointLoad):
    """Vertical Point Load.

    Parameters:
    -----------
    Force: float
        Force load (default units N)
    coord: float
        x coordinate of load on beam (default units m)

    Examples
    --------
    >>> # 100 N towards the right at x = 9 m
    >>> external_force = PointLoad(100, 9)

    Note: Positive force acts up.
    """

    def __init__(self, force=0, coord=0):
        super().__init__(force, coord, angle=90)


class PointLoadH(PointLoad):
    """Horizontal Point Load.

    Parameters:
    -----------
    Force: float
        Force load (default units m)
    coord: float
        x coordinate of load on beam (default units m)

    Examples
    --------
    >>> # 100 N up at x = 9 m
    >>> external_force = PointLoad(100, 9)

    Note: Positive force acts right.
    """

    def __init__(self, force=0, coord=0):
        super().__init__(force, coord, angle=0)


class UDLV(UDL):
    """Vertical Uniformly Distributed Load.
    
    Parameters
    ----------
    Force: float
        Force load (default units N/m)
    span: tuple of floats
        A tuple containing the starting and ending coordinate that
        the UDL is applied to (default units m).

    Examples
    --------
    >>> # load of 1000 N/m (acting down) from 1 <= x <= 4 m
    >>> self_weight = UDL(-1000, (1, 4))

    Note: Positive force acts up.
    """

    def __init__(self, force=0, span=(0, 0)):
        super().__init__(force, span, angle=90)


class UDLH(UDL):
    """Horizontal Uniformly Distributed Load.
    
    Parameters
    ----------
    Force: float
        Force load (default units N/m)
    span: tuple of floats
        A tuple containing the starting and ending coordinate that
        the UDL is applied to (default units m).

    Examples
    --------
    >>> # load of 1000 N/m (acting right) from 1 <= x <= 4 m
    >>> self_weight = UDL(-1000, (1, 4))

    Note: Positive force acts right.
    """

    def __init__(self, force=0, span=(0, 0)):
        super().__init__(force, span, angle=0)


class TrapezoidalLoadV(TrapezoidalLoad):
    """Vertical Trapezoidal Distributed Load.

    Parameters
    ----------
    force : tuple of floats
        A tuple containing the starting and ending loads of
        the trapezoidal load (default units N/m).
    span: tuple of floats
        A tuple containing the starting and ending coordinate that
        the trapezoidal load is applied to (default units m).

    Examples
    --------
    >>> # trapezoidal load starting at 2000 N/m at 1 m and ending at 3000 N/m
    >>> # at 4 m (acting down)
    >>> self_weight = UDL((-2000,-3000), (1, 4))

    Note: Positive force acts up.
    """

    def __init__(self, force=(0, 0), span=(0, 0)):
        super().__init__(force, span, angle=90)


class TrapezoidalLoadH(TrapezoidalLoad):
    """Horizontal Trapezoidal Distributed Load.
    
    Parameters
    ----------
    force : tuple of floats
        A tuple containing the starting and ending loads of
        the trapezoidal load (default units N/m).
    span: tuple of floats
        A tuple containing the starting and ending coordinate that
        the trapezoidal load is applied to (default units m).

    Examples
    --------
    >>> # trapezoidal load starting at 2000 N/m at 1 m and ending at 3 N/m
    >>> # at 4 m (acting right)
    >>> self_weight = UDL((2000, 3000), (1, 4))

    Note: Positive force acts right.
    """

    def __init__(self, force=(0, 0), span=(0, 0)):
        super().__init__(force, span, angle=0)


class DistributedLoadV(DistributedLoad):
    """Vertical distributed load, described by its functional form, 
    application interval and the angle of the load relative to the beam.

    Parameters:
    -----------
    expr: sympy expression
        Sympy expression of the distributed load function expressed
        using variable x which represents the beam x-coordinate (default
        units N/m).Requires quotation marks around expression.
    span: tuple of floats
        A tuple containing the starting and ending coordinate that
         the function is applied to (default units m).
   
    Examples
    --------
    >>> # Linearly growing load (acting down) for 0 < x < 2 m
    >>> snow_load = DistributedLoad("-10*x-5", (0, 2))

    Note: Positive force acts up.
    """

    def __init__(self, expr=0, span=(0, 0)):
        super().__init__(expr, span, angle=90)


class DistributedLoadH(DistributedLoad):
    """Horizontal distributed load, described by its functional form, 
    application interval and the angle of the load relative to the beam.

    Parameters:
    -----------
    expr: sympy expression
        Sympy expression of the distributed load function expressed
        using variable x which represents the beam x-coordinate (default
        units N/m). Requires quotation marks around expression.
    span: tuple of floats
        A tuple containing the starting and ending coordinate that
         the function is applied to (default units m).
   
    Examples
    --------
    >>> # Linearly growing load (acting right) for 0 < x < 2 m
    >>> snow_load = DistributedLoad("10*x+5", (0, 2))

    Note: Positive force acts right.
    """

    def __init__(self, expr=0, span=(0, 0)):
        super().__init__(expr, span, angle=0)
