"""Main module that contains the main class for Beam
and auxillary class for Support.

Example
--------
>>> beam = Beam(6)
>>> a = Support()
>>> c = Support(6,(0,1,0))
>>> beam.add_supports(a,c)
>>> beam.add_loads(PointLoadV(-1500,3))
>>> beam.analyse()
>>> beam.plot_beam_external()
>>> beam.plot_beam_internal()

"""

# Standard Library Imports
from collections import namedtuple
from math import radians
import time

# Third Party Imports
import numpy as np
from sympy import (
    integrate,
    lambdify,
    Piecewise,
    sympify,
    symbols,
    linsolve,
    sin,
    cos,
    oo,
    SingularityFunction,
)
from sympy.abc import x
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# Local Application Imports'
from indeterminatebeam.data_validation import (
    assert_number,
    assert_positive_number,
    assert_strictly_positive_number,
    assert_length,
    assert_list_contents,
    assert_contents,
)
from indeterminatebeam.loading import (
    PointLoad,
    PointLoadV,
    PointLoadH,
    DistributedLoad,
    DistributedLoadV,
    DistributedLoadH,
    PointTorque,
    TrapezoidalLoad,
    TrapezoidalLoadV,
    TrapezoidalLoadH,
    UDL,
    UDLH,
    UDLV,
)
from indeterminatebeam.plotly_drawing_aid import (
    draw_line,
    draw_arrowhead,
    draw_arrow,
    draw_support_triangle,
    draw_support_rectangle,
    draw_moment,
    draw_force,
    draw_load_hoverlabel,
    draw_reaction_hoverlabel,
    draw_support_hoverlabel,
    draw_support_rollers,
    draw_support_spring,
    draw_support,
)

from indeterminatebeam.units import IMPERIAL_UNITS, METRIC_UNITS, UNIT_KEYS, UNIT_VALUES


class Support:
    """
    A class to represent a support.

    Attributes:
    -------------
        _position: float
            x coordinate of support on a beam (default 0)
        _stiffness: tuple of 3 floats or infinity
            stiffness K (default units N/m) for movement in x, y and bending. oo
            represents infinity in sympy and means a completely fixed
            conventional support, and 0 means free to move.
        _DOF : tuple of 3 booleans
            Degrees of freedom that are restraint on a beam for
            movement in x, y and bending. 1 represents that a reaction
            force exists and 0 represents free (default (1,1,1))
        _fixed: tuple of 3 booleans
            Degrees of freedom that are completely fixed on a beam for
            movement in x, y and bending. 1 represents fixed and 0
            represents free or spring  (default (1,1,1))

    Examples
    --------
    >>> # Creates a fixed suppot at location 0
    >>> Support(0, (1,1,1))
    >>> # Creates a pinned support at location 5 m
    >>> Support(5, (1,1,0))
    >>> # Creates a roller support at location 5.54 m
    >>> Support(5.54, (0,1,0))
    >>> # Creates a y direction spring support at location 7.5 m
    >>> Support(7.5, (0,1,0), ky = 5)
    """

    def __init__(self, coord=0, fixed=(1, 1, 1), kx=None, ky=None):
        """
        Constructs all the necessary attributes for the Support object.

        Parameters:
        -----------
        coord: float
            x coordinate of support on a beam (default unit m) (default 0)
        fixed: tuple of 3 booleans
            Degrees of freedom that are fixed on a beam for movement in
            x, y and bending. 1 represents fixed and 0 represents free
            (default (1,1,1))
        kx :
            stiffness of x support (default unit N/m), if set will overide the
            value placed in the fixed tuple. (default = None)
        ky : (positive number)
            stiffness of y support (default unit N/m), if set will overide the
            value placed in the fixed tuple. (default = None)
        """

        # validate coordinate
        assert_positive_number(coord, "coordinate")

        # validate support stiffness if assigned
        if kx:
            assert_positive_number(kx, "kx")
        if ky:
            assert_positive_number(ky, "ky")

        # validate fixed tuple elements
        assert_list_contents(fixed, (0, 1), "fixed")

        # validate fixed tuple length
        assert_length(fixed, 3, "fixed")

        # Spring representation, set rigid to infinity instead of 1.
        # Otherwise set to 0
        self._stiffness = [oo if a else 0 for a in fixed]

        # If kx or ky has been included override oo or 0 value
        if kx:
            self._stiffness[0] = kx
        if ky:
            self._stiffness[1] = ky

        # Assign properties for support
        self._DOF = [int(bool(e)) for e in self._stiffness]
        self._fixed = [int(bool(e)) if e == oo else 0 for e in self._stiffness]
        self._position = coord

    def __str__(self):
        return f"""--------------------------------
        position = {float(self._position)}
        Stiffness_x = {self._stiffness[0]}
        Stiffness_y = {self._stiffness[1]}
        Stiffness_M = {self._stiffness[2]} """

    def __repr__(self):
        return f"<support, position = {self._position}>"


class Beam:
    """
    Represents a one-dimensional beam that can take axial and
    tangential loads.

    Attributes
    --------------
    _x0 :float
        Left end coordinate of beam (always defined as 0).
    _x1 :float
        Right end coordinate of beam (default unit m).

    _E: float
        Young's Modulus of the beam (default unit N/m2 or Pa)
    _I: float
        Second Moment of Area of the beam (default unit m4)
    _A: float
        Cross-sectional area of the beam (default unit m2)

    _loads: list
        list of load objects associated with the beam
    _supports: list
        A list of support objects associated with the beam.
    _query: list
        A list containing x coordinates that are to have values
        explicitly written on graphs.

    _normal_forces: sympy piecewise function
        A sympy function representing the internal axial force (default unit N) as a
        function of x (m).
    _shear_forces: sympy piecewise function
        A sympy function representing the internal shear force (default unit N) as a
        function of x (m).
    _bending_moments: sympy piecewise function
        A sympy function representing the internal bending moments (default unit N.m)
        as a function of x (m).
    _deflection_equation: sympy piecewise function
        A sympy function representing the tangential deflection (default unit m) as
        a function of x (default unit m).

    _reactions: dictionary of lists
        A dictionary with keys for support positions. Each key is
        associated with a list of forces of the form ['x','y','m']
    _DATA_POINTS: integer,
        Number of data points generated for plotting (default 200).

    Notes
    -----
    * Default units are SI units all using N and m, this can
      however be changed using the update_units() method
    * The default units for length, force and bending moment (torque)
      are in N and m (m, N, N·m)
    * The default units for beam properties (E, I, A) are in N and m
      (N/m2, m4, m2)
    * The default unit for spring support stiffness is N/m
    """

    def __init__(self, span: float = 5, E=200 * 10**9, I=9.05 * 10**-6, A=0.23):
        """Initializes a Beam object of a given length.

        Parameters
        ----------
        span : float
            Length of the beam span (default unit m). Must be positive, and the pinned
            and rolling supports can only be placed within this span.
            The default value is 5 m.
        E: float
            Youngs modulus for the beam (default unit Pa). The default value is
            200 GPa, which is the youngs modulus for steel.
        I: float
            Second moment of area for the beam about the z axis (default unit m4).
            The default value is 9.05*10**-6 m4.
        A: float
            Cross-sectional area for the beam about the z axis (default unit m2).
            The default value is 0.23 m4.

        Notes
        -----
        * Default properties are for a 150UB18.0 steel beam.
        """
        # Validate inputs for span and beam properties.
        assert_strictly_positive_number(span, "span")
        assert_strictly_positive_number(E, "Young's Modulus (E)")
        assert_strictly_positive_number(I, "Second Moment of Area (I)")
        assert_strictly_positive_number(A, "Area (A)")

        # Assign input properties for beam object.
        self._x0 = 0
        self._x1 = span

        self._E = E
        self._I = I
        self._A = A

        # Intialize other beam object properties.
        self._loads = []
        self._supports = []
        self._query = []

        self._DATA_POINTS = 200
        self.update_decimal_precision(3)

        self._units = {
            "length": "m",
            "force": "N",
            "moment": "N.m",
            "distributed": "N/m",
            "stiffness": "N/m",
            "A": "m2",
            "E": "Pa",
            "I": "m4",
            "deflection": "m",
        }

        self._analysis_reset()

    def _analysis_reset(self):
        """Reset properties determined by analysis."""

        self._normal_forces = 0
        self._shear_forces = 0
        self._bending_moments = 0
        self._deflection_equation = 0

        self._reactions = {}
        self._plotting_vectors = {}

    def update_units(self, key="length", unit="m", reset=False):
        """Change units used for inputs and outputs.

        Parameters
        ----------
        key: string, default 'length'
            Identifying property with unit to be changed.
            One of the following: 'length', 'force', 'moment',
            'distributed', 'stiffness', 'A', 'E', 'I',
            'deflection'
        unit: string, default 'm'
            unit to assign should contain a unit balanced representation
            consisting of the following units: 'mm', 'cm', 'm', 'N', 'kN',
            'Pa', 'kPa', 'MPa', 'in', 'ft', 'lbf', 'kip'.
            Unit combinations are written in the following formats:
            'mm2', 'mm4', 'N/m', 'N.m', 'kip/ft2'.
        reset: boolean, default False
            If True then all units reset to default SI units.
        """
        if reset:
            self._units = {
                "length": "m",
                "force": "N",
                "moment": "N.m",
                "distributed": "N/m",
                "stiffness": "N/m",
                "A": "m2",
                "E": "Pa",
                "I": "m4",
                "deflection": "m",
            }
            self._analysis_reset()
        else:
            assert_contents(key, UNIT_KEYS, "key")
            assert_contents(unit, UNIT_VALUES[key], "unit")

            self._units[key] = unit
            self._analysis_reset()

    def add_loads(self, *loads):
        """Associate load objects with the beam object.

        Parameters
        ----------
        *loads : iterable
            An iterable containing load objects to be applied to the
            Beam object. Note that the load application point
            (or segment) must be within the Beam span.

        """
        self._analysis_reset()

        # Iterate through each load passed into function
        for load in loads:
            # Check if distributed load (will be true for V and H load
            # types since they inherit from these main load types)
            if isinstance(load, (DistributedLoad, UDL, TrapezoidalLoad)):

                # check span exists within beam
                left, right = load.span
                if self._x0 > left or right > self._x1:
                    raise ValueError(
                        f"Coordinate {load.span} for {str(load)} is not a point on beam."
                    )

                # associate force variable with force value of load,
                # in order to not add any loads that have no force later.
                if isinstance(load, DistributedLoad):
                    # set force as arbritrary non-zero value so add any
                    # Distributed load to self._loads
                    force = 1
                elif isinstance(load, UDL):
                    force = load.force
                else:
                    force = max(load.force, key=abs)

            # check if point load/torque
            elif isinstance(load, (PointTorque, PointLoad)):

                # check point exists within beam
                coordinate = load.position
                if self._x0 > coordinate or coordinate > self._x1:
                    raise ValueError(
                        f"Coordinate {coordinate} for {str(load)} is not a point on beam."
                    )

                force = load.force

            # if not a distributed load or point load then isnt a load class.
            else:
                raise ValueError(f"Load '{load}' is not a load object.")

            # if force isnt 0, then add to self._loads, otherwise will
            # have no effect on the beam and as such shouldnt add.
            if force != 0:
                self._loads.append(load)

    def remove_loads(self, *loads, remove_all=False):
        """Unassociate load objects with the beam object.

        Parameters
        ----------
        *loads : iterable
            An iterable containing load objects to be removed from
            the Beam object. If load not on beam then does nothing.
        remove_all: boolean
            If true all loads associated with beam will be removed,
            by default False.

        """

        self._analysis_reset()

        # if remove all set to True, reintialize self._loads
        if remove_all:
            self._loads = []
            return None

        # for each load remove if currently associated with beam object.
        for load in loads:
            if load in self._loads:
                self._loads.remove(load)

        # Could be considered a bug that a user isnt notified
        # if a load isnt removed because it wasnt there. This might be
        # an issue if they dont properly recreate the load they were
        # trying to remove and dont notice that they didnt actually
        # delete it.

    def add_supports(self, *supports):
        """Associate support objects with the beam object.

        Parameters
        ----------
        *supports : iterable
            An iterable containing Support objects to be applied to
            the Beam object. Note that the load application point
            (or segment) must be within the Beam span.

        """

        self._analysis_reset()

        # Check support valid then append to self._supports
        for support in supports:
            # check is a Support object
            if not isinstance(support, Support):
                raise TypeError("support must be of type class Support")

            # check support exists on beam
            if (self._x0 > support._position) or (support._position > self._x1):
                raise ValueError("Not a point on beam")

            # if currently no supports then there is nothing the
            # support being added can conflict with. Add it in.
            if self._supports == []:
                self._supports.append(support)

            # if there are already supports associated with the
            # beam object only add the new support if no support
            # exists at the same position.
            elif support._position not in [x._position for x in self._supports]:
                self._supports.append(support)

            # if already a supported associated with position raise error
            else:
                raise ValueError(
                    f"This coordinate {support._position} already has a support associated with it"
                )

    def remove_supports(self, *supports, remove_all=False):
        """Unassociate support objects with the beam object.

        Parameters
        ----------
        *supports : iterable
            An iterable containing Support objects to be removed from
            the Beam object. If support not on beam then does nothing.
        remove_all: boolean
            If true all supports associated with beam will be removed,
            by default False.
        """

        self._analysis_reset()

        # if remove all set to True, reintialize self._supports
        if remove_all:
            self._supports = []
            return None

        # for each support remove if currently associated with beam object.
        for support in self._supports:
            if support in supports:
                self._supports.remove(support)

        # Could be considered a bug that a user isnt notified
        # if a support isnt removed because it wasnt there. This might
        # be an issue if they dont properly recreate the support they
        # were trying to remove and dont notice that they didnt actually
        # delete it.

    def analyse(self):
        """Solve the beam structure for reaction and internal forces"""
        # Foreword: As a result of sympify not working on SingularityFunctions
        # for the current version of sympy the solution had to become more
        # abstract, with the use of a conversion from singualaritys to piecewise
        # functions. As all the functions use SingularityFunction, except for
        # distributed load functions which are Piecewise functions, these two
        # different types of loads had to be grouped (so the equations for
        # shear force, bending moment etc. are split into a component 1 and
        # component 2). Then at the end of this function where the conversion
        # takes place it only takes place for the singularity functions.
        # This code can be made a lot more succint given that Sympy updates
        # to allow for sympify on singularity functions. To allow for unit
        # flexibility methods these functions had to be split further
        # to seperate all load types so that appropriate unit conversion factors
        # could be applied.

        # create a dictionary that associates units with the unit conversion value,
        # i.e. the number that the input should be multiplied by to change to SI
        units = {}
        for key, val in self._units.items():
            if val in METRIC_UNITS[key].keys():
                units[key] = METRIC_UNITS[key][val]
            else:
                units[key] = IMPERIAL_UNITS[key][val]

        x1 = self._x1

        # initialised with position and stiffness.
        self._supports = sorted(self._supports, key=lambda item: item._position)

        # intialize unknowns as a dictionary of lists
        unknowns = {}
        unknowns["x"] = []
        unknowns["y"] = []
        unknowns["m"] = []

        # for each support if there is a reaction force create an appropriate,
        # sympy variable and entry in unknowns dictionary.
        # for x and y singularity function power is 0 to be added in at SF level.
        # for m singularity function power is also 0, to be added in at BM level.
        for a in self._supports:
            if a._stiffness[0] != 0:
                unknowns["x"].append(
                    {
                        "position": a._position,
                        "stiffness": a._stiffness[0],
                        "force": (
                            symbols("x_" + str(a._position))
                            * SingularityFunction(x, a._position, 0)
                        ),
                        "variable": symbols("x_" + str(a._position)),
                    }
                )
            if a._stiffness[1] != 0:
                unknowns["y"].append(
                    {
                        "position": a._position,
                        "stiffness": a._stiffness[1],
                        "force": (
                            symbols("y_" + str(a._position))
                            * SingularityFunction(x, a._position, 0)
                        ),
                        "variable": symbols("y_" + str(a._position)),
                    }
                )
            if a._stiffness[2] != 0:
                unknowns["m"].append(
                    {
                        "position": a._position,
                        "torque": (
                            symbols("m_" + str(a._position))
                            * SingularityFunction(x, a._position, 0)
                        ),
                        "variable": symbols("m_" + str(a._position)),
                    }
                )

        # grab the set of all the sympy unknowns for y and m and change
        # to a list, do same for x unknowns. To be later used by linsolve.
        unknowns_ym = [a["variable"] for a in unknowns["y"]] + [
            a["variable"] for a in unknowns["m"]
        ]

        unknowns_xx = [a["variable"] for a in unknowns["x"]]

        # Assert that there are enough supports. Even though it logically
        # works to have no x support if you have no x loading, it works
        # much better in the program and makes the code alot shorter to
        # just enforce that an x support is there, even when there is no
        # load.
        if len(unknowns_xx) < 1:
            raise ValueError(
                "You need at least one x restraint, even if there are " + "no x forces"
            )

        if len(unknowns_ym) < 2:
            raise ValueError(
                "You need at least two y or m restraints, even if there "
                + "are no y or m forces"
            )

        # external reaction equations

        # sum contribution of loads and contribution of supports.
        # for loads ._x1 represents the load distribution integrated,
        # thereby giving the total load by the end of the support.
        F_Rx = (
            sum(
                [
                    load._x1.subs(x, x1)
                    for load in self._loads
                    if isinstance(load, PointLoad)
                ]
            )
            * units["force"]
            + sum(
                [
                    load._x1.subs(x, x1)
                    for load in self._loads
                    if isinstance(load, (UDL, DistributedLoad, TrapezoidalLoad))
                ]
            )
            * units["distributed"]
            * units["length"]
            + sum([a["variable"] for a in unknowns["x"]])
        )

        # similiar to F_Rx
        F_Ry = (
            sum(
                [
                    load._y1.subs(x, x1)
                    for load in self._loads
                    if isinstance(load, PointLoad)
                ]
            )
            * units["force"]
            + sum(
                [
                    load._y1.subs(x, x1)
                    for load in self._loads
                    if isinstance(load, (UDL, DistributedLoad, TrapezoidalLoad))
                ]
            )
            * units["distributed"]
            * units["length"]
            + sum([a["variable"] for a in unknowns["y"]])
        )

        # moments taken at the left of the beam, anti-clockwise is positive
        M_R = (
            sum(load._m0 for load in self._loads if isinstance(load, PointLoad))
            * units["force"]
            * units["length"]
            + sum(
                load._m0
                for load in self._loads
                if isinstance(load, (UDL, DistributedLoad, TrapezoidalLoad))
            )
            * units["distributed"]
            * units["length"] ** 2
            + sum(load._m0 for load in self._loads if isinstance(load, PointTorque))
            * units["moment"]
            + sum([a["variable"] for a in unknowns["m"]])
            + sum([a["variable"] * a["position"] for a in unknowns["y"]])
            * units["length"]
        )

        # Create integration constants as sympy unknowns
        C1, C2 = symbols("C1"), symbols("C2")
        unknowns_ym += [C1, C2]

        # normal forces, same concept as shear forces
        N_i_1 = (
            sum(load._x1 for load in self._loads if isinstance(load, PointLoad))
            * units["force"]
            + sum(
                load._x1
                for load in self._loads
                if isinstance(load, (UDL, TrapezoidalLoad))
            )
            * units["distributed"]
            * units["length"]
            + sum([a["force"] for a in unknowns["x"]])
        )

        N_i_2 = (
            sum(load._x1 for load in self._loads if isinstance(load, DistributedLoad))
            * units["distributed"]
            * units["length"]
        )

        N_i = N_i_1 + N_i_2

        # integrate to get NF * x as a function of x. Needed
        # later for displacement which is used if x springs are present
        Nv_EA = integrate(N_i, x) * units["length"]

        # shear forces. At a point x within the beam the cumulative sum of the
        # vertical forces (represented by load._y1 + reactons) plus the
        # internal shear forces should be equal to 0. i.e.
        # load._y1 + reactions + F_i = 0 ->  - F_i = load._y1 + reactions
        # However when considering the difference in load convention (for loads
        # upwards is positive, whereas for shear forces down is postive), this
        # becomes F_i = load._y1 + reactions
        # Note PointTorque had to be included here in order to ensure the singularity
        # function was considered (a positive value is correct and units have been
        # considered in the creation of the PointTorque function) Note have to multiply
        # by moment conversion and divide by length conversion to cancel out multiplying
        # by length conversion after integrating
        F_i_1 = (
            sum(load._y1 for load in self._loads if isinstance(load, PointLoad))
            * units["force"]
            + sum(
                load._y1
                for load in self._loads
                if isinstance(load, (UDL, TrapezoidalLoad))
            )
            * units["distributed"]
            * units["length"]
            + sum([a["force"] for a in unknowns["y"]])
        )

        F_i_2 = (
            sum(load._y1 for load in self._loads if isinstance(load, DistributedLoad))
            * units["distributed"]
            * units["length"]
        )

        F_i = F_i_1 + F_i_2

        # bending moments at internal point means we are now looking left
        # along the beam when we take our moments (vs when we did external
        # external reactions and we looked right). An anti-clockwise moment
        # is adopted as positive internally. Hence we need to consider a
        # postive for our shear forces and negative for our moments by
        # our sign convention. Note that F_i includes the contributions
        # of point torques through load._y1 which represents moments
        # as a SingularityFunction of power -1 (the point moments are
        # therefore only considered once the integration below takes place)
        M_i_1 = (
            integrate(F_i_1, x) * units["length"]
            + integrate(
                sum(load._y1 for load in self._loads if isinstance(load, PointTorque)),
                x,
            )
            * units["moment"]
            - sum([a["torque"] for a in unknowns["m"]])
        )

        M_i_2 = integrate(F_i_2, x) * units["length"]

        M_i = M_i_1 + M_i_2

        # integrate M_i for beam slope equation
        dv_EI_1 = integrate(M_i_1, x) * units["length"] + C1
        dv_EI_2 = integrate(M_i_2, x) * units["length"]
        dv_EI = dv_EI_1 + dv_EI_2

        # integrate M_i twice for deflection equation
        v_EI_1 = (
            integrate(dv_EI_1, x) * units["length"] + C2
        )  # should c2 be multiplied by the value
        v_EI_2 = integrate(dv_EI_2, x) * units["length"]
        v_EI = v_EI_1 + v_EI_2

        # create a list of equations for tangential direction
        equations_ym = [F_Ry, M_R]

        # at location that moment is restaint, the slope is known (to be 0,
        # always since dont deal for rotational springs in this version.)
        for reaction in unknowns["m"]:
            equations_ym.append(dv_EI.subs(x, reaction["position"]))

        # at location that y support is restaint the deflection is known (to be
        # F/k, where k is the spring stiffness which is a real number for a
        # spring and infinity for conventional fixed support.)
        # all units are in N and m, deflection is in m.
        for reaction in unknowns["y"]:
            equations_ym.append(
                v_EI.subs(x, reaction["position"])
                / (self._E * units["E"] * self._I * units["I"])
                + reaction["variable"] / (reaction["stiffness"] * units["stiffness"])
            )

        # equation for normal forces
        equations_xx = [F_Rx]

        # the extension of the beam will be equal to the spring
        # displacement on right minus spring displacment on left.
        # between fixed supports the extension is 0.

        # Only perform calculation if axially indeterminate
        if len(unknowns_xx) > 1:
            # Assign start to be the first x support.
            start = unknowns["x"][0]
            # For each support other than the start, set an endpoint
            for end in unknowns["x"][1:]:
                # the extension between start and end is known to be
                # a result of axial deformation.
                # i.e start_v = end_v - axial deformation between.
                # where:
                # start_v = spring_displacement = F/k (start support)
                # end_v = spring_displacement = F/k (end support)
                # axial deformation at a point = NV_EA.subs(x, point)/ (EA)
                # axial deformation between start and end =
                #   (NV_EA(end) - NV_EA(start)) / (EA)
                equations_xx.append(
                    (Nv_EA.subs(x, end["position"]) - Nv_EA.subs(x, start["position"]))
                    / (self._E * units["E"] * self._A * units["A"])
                    + start["variable"] / (start["stiffness"] * units["stiffness"])
                    # represents elongation displacment on right
                    - end["variable"] / (end["stiffness"] * units["stiffness"])
                )

        # compute analysis with linsolve
        solutions_ym = list(linsolve(equations_ym, unknowns_ym))[0]
        solutions_xx = list(linsolve(equations_xx, unknowns_xx))[0]

        # Create solution dictionary
        solutions = [a for a in solutions_ym + solutions_xx]
        solution_dict = dict(zip(unknowns_ym + unknowns_xx, solutions))

        # Initialise self._reactions to hold reaction forces for each support
        self._reactions = {a._position: [0, 0, 0] for a in self._supports}

        # substitue in value inplace of variable in functions
        for var, ans in solution_dict.items():
            ans = float(ans)
            N_i_1 = N_i_1.subs(var, ans)  # complete normal force equation
            F_i_1 = F_i_1.subs(var, ans)  # complete shear force equation
            M_i_1 = M_i_1.subs(var, ans)  # complete moment equation
            v_EI_1 = v_EI_1.subs(var, ans)  # complete deflection equation
            Nv_EA = Nv_EA.subs(var, ans)  # complete axial deformation equation
            if N_i_2:
                N_i_2 = N_i_2.subs(var, ans)  # complete normal force equation
            if F_i_2:
                F_i_2 = F_i_2.subs(var, ans)  # complete shear force
                M_i_2 = M_i_2.subs(var, ans)  # complete moment equation
                v_EI_2 = v_EI_2.subs(var, ans)  # complete deflection equation

            # create self._reactions to allow for plotting of reaction
            # forces if wanted and for use with get_reaction method.
            if var not in [C1, C2]:
                # vec represents direction, num represents position
                vec, num = str(var).split("_")
                position = float(num)
                converter = units["force"]
                if vec == "x":
                    i = 0
                elif vec == "y":
                    i = 1
                else:
                    i = 2
                    converter = units["moment"]

                # assign reaction to self._reactions using support position
                # as key, and using i for correct position in list.
                # Note list for each supports reaction forces is of form
                # [x,y,m].
                self._reactions[position][i] = float(round(ans / converter, 10))

        # set calculated beam equations on beam changing all singularity
        # functions to piecewise functions (see sympy_expr_to_piecewise
        # for more details.)
        self._normal_forces = (self.sympy_expr_to_piecewise(N_i_1) + N_i_2) / units[
            "force"
        ]
        self._shear_forces = (self.sympy_expr_to_piecewise(F_i_1) + F_i_2) / units[
            "force"
        ]
        self._bending_moments = (self.sympy_expr_to_piecewise(M_i_1) + M_i_2) / units[
            "moment"
        ]

        # moment unit is in base units. E and I are already base units.
        self._deflection_equation = (
            (self.sympy_expr_to_piecewise(v_EI_1) + v_EI_2)
            / (self._E * units["E"] * self._I * units["I"])
        ) / units["deflection"]

        self._set_plotting_vectors()

    def _set_plotting_vectors(self):
        """Create vectors of data points for functions to
        allow for quicker plotting and determining of results."""

        # create vector of x coordinate points
        x_vec = np.linspace(self._x0, self._x1, self._DATA_POINTS)

        # add x coordinates minutely close to any singularity position

        # take position from reaction (x_p is for x position)
        x_p = [a for a in self._reactions.keys()]

        # take position from loading
        for a in self._loads:
            if hasattr(a, "position"):
                x_p.append(a.position)
            elif hasattr(a, "span"):
                x_p += list(a.span)

        # add incremental positions besides point to list x_i if within beam
        x_i = []
        for a in x_p:
            l = a - 0.0000001
            r = a + 0.0000001
            if l > 0:
                x_i.append(l)
            if r < self._x1:
                x_i.append(r)

        # add points to x_vec, unique removes double ups and sorts
        # need to make both numpy arrays for them to be compatible
        x_vec = np.concatenate([x_vec, np.array(x_i)])
        x_vec = np.unique(x_vec)

        # lamdify functions
        nf_func = lambdify(x, self._normal_forces, "numpy")
        sf_func = lambdify(x, self._shear_forces, "numpy")
        bm_func = lambdify(x, self._bending_moments, "numpy")
        d_func = lambdify(x, self._deflection_equation, "numpy")

        # create numpy arrays for functions (y vectors)
        nf = np.array([float(nf_func(t)) for t in x_vec])
        sf = np.array([float(sf_func(t)) for t in x_vec])
        bm = np.array([float(bm_func(t)) for t in x_vec])
        d = np.array([float(d_func(t)) for t in x_vec])

        # associate functions and vectors with self._plotting_vectors
        self._plotting_vectors = {
            "x": x_vec,
            "nf": {
                "y_lam": nf_func,
                "y_vec": nf,
            },
            "sf": {
                "y_lam": sf_func,
                "y_vec": sf,
            },
            "bm": {
                "y_lam": bm_func,
                "y_vec": bm,
            },
            "d": {
                "y_lam": d_func,
                "y_vec": d,
            },
        }

    # SECTION - QUERY VALUE
    def get_reaction(self, x_coord, direction=None):
        """Find the reactions of a support at position x.

        Parameters
        ----------
        x_coord: float
            The x_coordinates on the beam to be substituted into the
            equation. List returned (if bools all false)
        direction: str ('x','y' or 'm')
            The direction of the reaction force to be returned.
            If not specified all are returned in a list.

        Returns
        --------
        int
            If direction is 'x', 'y', or 'm' will return an integer
            representing the reaction force of the support in that
            direction at location x_coord.
        list of ints
            If direction = None, will return a list of 3 integers,
            representing the reaction forces of the support ['x','y','m']
            at location x_coord.
        None
            If there is no support at the x coordinate specified.
        """

        # Check beam has been analysed
        if not self._reactions:
            print("You must analyse the structure before calling this function")

        # check x_coord is associated with reactions
        if x_coord not in self._reactions.keys():
            return None

        directions = ["x", "y", "m"]

        # if a direction has been passed will be returning a single value
        # for the reaction force in that direction
        if direction:
            # check direction valid
            assert_contents(direction, directions, "direction")

            # if direction valid return appropriate reaction fore
            return self._reactions[x_coord][directions.index(direction)]

        # if no direction is specified return a list of all the reaction
        # forces.
        return self._reactions[x_coord]

    def _get_query_value(
        self, x_coord, func, return_max=False, return_min=False, return_absmax=False
    ):
        """Find the value of a function at position x_coord, or
        determine function extremes.

        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be substituted into the
            equation. List returned (if bools all false)
        func: str
            String representing function to query:
                'nf' if normal force.
                'sf' if shear force.
                'bm' if bending moment.
                'd' if deflection.
        return_max: bool
            return max value of function if true
        return_min: bool
            return min value of function if true
        return_absmax: bool
            return absolute max value of function if true

        Returns
        --------
        int
            Max, min or absmax value of the sympy function depending
            on which parameters are set. If single x-coordinate set
            then also returns int.
        list of ints
            If x-coordinates are specfied value at x-coordinates for
            func.

        Notes
        -----
        * Priority of query parameters is return_max, return_min,
          return_absmax, x_coord (if more than 1 of the parameters are
          specified).
        """

        y_vec = self._plotting_vectors[func]["y_vec"]
        y_lam = self._plotting_vectors[func]["y_lam"]

        # if there are no max/min parameters set to true base
        # return on x_coord
        if 1 not in (return_absmax, return_max, return_min):
            # change x_coord to be a list if it isnt so
            # can treat both cases of 1 input and multiple inputs
            # the same for the following section of code.

            if not isinstance(x_coord, tuple):
                x_coord = [x_coord]

            # loop through each x_coordinate in make a new list which
            # has point infintismally at each side.
            # (The point of this is to avoid having the exact same x
            # as a singularity function value, and in the case of
            # being at a singularity value the values from each side
            # are inspected and the absmax case is returned.)
            x_ = []
            for p in x_coord:
                l = p - 0.0000001
                r = p + 0.0000001

                a = round(float(y_lam(l)), 10)
                b = round(float(y_lam(r)), 10)

                c = max([a, b], key=abs)
                x_.append(c)

            # make a list of one only return one value to match
            # data type return from previous versions.
            if len(x_) == 1:
                return x_[0]
            return x_

        min_ = float(y_vec.min())
        max_ = float(y_vec.max())

        if return_max:
            return round(max_, 10)
        elif return_min:
            return round(min_, 10)
        else:
            return round(max(abs(min_), max_), 10)

    def get_bending_moment(
        self, *x_coord, return_max=False, return_min=False, return_absmax=False
    ):
        """Find the bending moment(s) on the beam object.

        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be substituted into the
            equation. List returned (if bools all false)
        return_max: bool
            return max value of function if true
        return_min: bool
            return minx value of function if true
        return_absmax: bool
            return absolute max value of function if true

        Returns
        --------
        int
            Max, min or absmax value of the bending moment depending
            on which parameters are set. If single x-coordinate set
            then also returns int.
        list of ints
            If x-coordinates are specfied value at x-coordinates for
            func.

        Notes
        -----
        * Priority of query parameters is return_max, return_min,
          return_absmax, x_coord (if more than 1 of the parameters are
          specified).
        """

        return self._get_query_value(
            x_coord,
            func="bm",
            return_max=return_max,
            return_min=return_min,
            return_absmax=return_absmax,
        )

    def get_shear_force(
        self, *x_coord, return_max=False, return_min=False, return_absmax=False
    ):
        """Find the shear force(s) on the beam object.

        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be substituted into the
            equation. List returned (if bools all false)
        return_max: bool
            return max value of function if true
        return_min: bool
            return minx value of function if true
        return_absmax: bool
            return absolute max value of function if true

        Returns
        --------
        int
            Max, min or absmax value of the shear force depending
            on which parameters are set. If single x-coordinate set
            then also returns int.
        list of ints
            If x-coordinates are specfied value at x-coordinates for
            func.

        Notes
        -----
        * Priority of query parameters is return_max, return_min,
          return_absmax, x_coord (if more than 1 of the parameters are
          specified).
        """

        return self._get_query_value(
            x_coord,
            func="sf",
            return_max=return_max,
            return_min=return_min,
            return_absmax=return_absmax,
        )

    def get_normal_force(
        self, *x_coord, return_max=False, return_min=False, return_absmax=False
    ):
        """Find the normal force(s) on the beam object.

        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be substituted into the
            equation. List returned (if bools all false)
        return_max: bool
            return max value of function if true
        return_min: bool
            return minx value of function if true
        return_absmax: bool
            return absolute max value of function if true

        Returns
        --------
        int
            Max, min or absmax value of the normal force depending
            on which parameters are set. If single x-coordinate set
            then also returns int.
        list of ints
            If x-coordinates are specfied value at x-coordinates for
            func.

        Notes
        -----
        * Priority of query parameters is return_max, return_min,
          return_absmax, x_coord (if more than 1 of the parameters are
          specified).
        """
        return self._get_query_value(
            x_coord,
            func="nf",
            return_max=return_max,
            return_min=return_min,
            return_absmax=return_absmax,
        )

    def get_deflection(
        self, *x_coord, return_max=False, return_min=False, return_absmax=False
    ):
        """Find the deflection(s) on the beam object.

        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be substituted into the
            equation. List returned (if bools all false)
        return_max: bool
            return max value of function if true
        return_min: bool
            return minx value of function if true
        return_absmax: bool
            return absolute max value of function if true

        Returns
        --------
        int
            Max, min or absmax value of the deflection depending
            on which parameters are set. If single x-coordinate set
            then also returns int.
        list of ints
            If x-coordinates are specfied value at x-coordinates for
            func.

        Notes
        -----
        * Priority of query parameters is return_max, return_min,
          return_absmax, x_coord (if more than 1 of the parameters are
          specified).
        """

        return self._get_query_value(
            x_coord,
            func="d",
            return_max=return_max,
            return_min=return_min,
            return_absmax=return_absmax,
        )

    # SECTION - PLOTTING

    def add_query_points(self, *x_coords):
        """Document the forces on a beam at position x_coord when
        plotting.

        Parameters
        ----------
        x_coord: list
            The x_coordinates on the beam to be queried on plot.

        """
        # Add query points to self._query if the point exists
        # on the beam object.
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
            The x_coordinates on the beam to be removed from query
            on plot.
        remove_all: boolean
            If true all query points will be removed.

        """
        # if remove all set reinitialize self._query to empty list
        if remove_all:
            self._query = []
            return None

        # otherwise for each x_coordinate passed if it is within
        # the current query list remove it.
        for x_coord in x_coords:
            if x_coord in self._query:
                self._query.remove(x_coord)
            # didnt have the following in the previous two remove functions.
            # by not adding i keep the remove functions all consistent
            # in that if try to remove something that isnt associated i
            # dont do anything.

            # else:
            #     return ValueError("Not an existing query point on beam")

    def plot_beam_external(self):
        """Generates a single figure with 2 plots corresponding
        respectively to:

        - a schematic of the loaded beam
        - reaction force diagram

        Returns
        -------
        figure : `plotly.graph_objs._figure.Figure`
            Returns a handle to a figure with the 2 subplots.

        """
        # create suplot space, note shared axis on plot
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=("Beam schematic", "Reaction Forces"),
        )

        # assign each plot to its subplot
        fig = self.plot_beam_diagram(fig=fig, row=1, col=1)
        fig = self.plot_reaction_force(fig=fig, row=2, col=1)

        # update shared axis title and place at bottom of plot
        xt = "Beam Length (" + self._units["length"] + ")"
        fig.update_xaxes(title_text=xt, row=2, col=1)

        # update layout of plot
        fig.update_layout(
            height=550,
            width=700,
            title={"text": "Beam External Conditions", "x": 0.5},
            title_font_size=24,
            showlegend=False,
            hovermode="x",
        )

        return fig

    def plot_beam_internal(self, reverse_x=False, reverse_y=False):
        """Generates a single figure with 4 plots corresponding
        respectively to:

        - normal force diagram,
        - shear force diagram,
        - bending moment diagram, and
        - deflection diagram

        Parameters
        ----------
        reverse_x : bool, optional
            reverse the x axes, by default False
        reverse_y : bool, optional
            reverse the y axes, by default False

        Returns
        -------
        figure : `plotly.graph_objs._figure.Figure`
            Returns a handle to a figure with the 4 subplots.

        """
        # make empty subplot space
        fig = make_subplots(
            rows=4,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=(
                "Normal Force Diagram",
                "Shear Force Diagram",
                "Bending Moment Diagram",
                "Deflection Diagram",
            ),
        )

        # Add each plot to its subplot space
        fig = self.plot_normal_force(
            reverse_x=reverse_x, reverse_y=reverse_y, fig=fig, row=1, col=1
        )
        fig = self.plot_shear_force(
            reverse_x=reverse_x, reverse_y=reverse_y, fig=fig, row=2, col=1
        )
        fig = self.plot_bending_moment(
            reverse_x=reverse_x, reverse_y=reverse_y, fig=fig, row=3, col=1
        )
        fig = self.plot_deflection(
            reverse_x=reverse_x, reverse_y=reverse_y, fig=fig, row=4, col=1
        )

        # update shared x axis
        xt = "Beam Length (" + self._units["length"] + ")"
        fig.update_xaxes(title_text=xt, row=4, col=1)

        # update layout
        fig.update_layout(
            height=1000,
            width=700,
            title={"text": "Analysis Results", "x": 0.5},
            title_font_size=24,
            showlegend=False,
        )

        return fig

    def plot_beam_diagram(self, fig=None, row=None, col=None):
        """Returns a schematic of the beam and all the loads applied on
        it

        Parameters
        ----------
        fig : bool, optional
            Figure to append subplot diagram too. If creating standalone
            figure then None, by default None
        row : int, optional
            row number if subplot, by default None
        col : int, optional
            column number if subplot, by default None

        Returns
        -------
        figure : `plotly.graph_objs._figure.Figure`
            Returns a handle to a figure with the beam schematic.
        """

        data = go.Scatter(
            x=[self._x0, self._x1],
            y=[0, 0],
            meta=[self._units["length"]],
            mode="lines",
            name="Beam_",
            line=dict(color="purple", width=2),
            hovertemplate="%{x} %{meta[0]}",
            hoverinfo="skip",
        )

        if fig and row and col:
            fig.add_trace(data, row=row, col=col)
            fig.update_yaxes(
                visible=False, range=[-3, 3], fixedrange=True, row=row, col=col
            )
        else:
            fig = go.Figure(data=data)
            # Hovermode x makes two hover labels appear if they are at
            # the same point (default setting means only see the last
            # updated point)
            fig.update_layout(
                height=350,
                title_text="Beam Schematic",
                title_font_size=24,
                showlegend=False,
                hovermode="x",
                title_x=0.5,
            )

            xt = "Beam Length (" + self._units["length"] + ")"
            fig.update_xaxes(title_text=xt)
            # visible false means y axis doesnt show, fixing range
            # means wont zoom in y direction

            fig.update_yaxes(visible=False, range=[-3, 3], fixedrange=True)

        # for each support append to figure to have the shapes/traces
        # needed for the drawing
        if row and col:
            for support in self._supports:
                fig = draw_support(
                    fig,
                    support,
                    row=row,
                    col=col,
                    units=self._units,
                    precision=self.decimal_precision,
                )

            for load in self._loads:
                fig = draw_force(
                    fig,
                    load,
                    row=row,
                    col=col,
                    units=self._units,
                    precision=self.decimal_precision,
                )
                fig = draw_load_hoverlabel(
                    fig,
                    load,
                    row=row,
                    col=col,
                    units=self._units,
                    precision=self.decimal_precision,
                )
        else:
            for support in self._supports:
                fig = draw_support(
                    fig, support, units=self._units, precision=self.decimal_precision
                )

            for load in self._loads:
                fig = draw_force(
                    fig, load, units=self._units, precision=self.decimal_precision
                )
                fig = draw_load_hoverlabel(
                    fig, load, units=self._units, precision=self.decimal_precision
                )

        return fig

    def plot_reaction_force(self, fig=None, row=None, col=None):
        """Returns a plot of the beam with reaction forces.

        Parameters
        ----------
        fig : bool, optional
            Figure to append subplot diagram too. If creating standalone
            figure then None, by default None
        row : int, optional
            row number if subplot, by default None
        col : int, optional
            column number if subplot, by default None

        Returns
        -------
        figure : `plotly.graph_objs._figure.Figure`
            Returns a handle to a figure with reaction forces.
        """
        # if a figure is passed it is for the subplot
        # append everything to it rather than creating a new plot.
        data = go.Scatter(
            x=[self._x0, self._x1],
            y=[0, 0],
            mode="lines",
            name="Beam",
            line=dict(color="purple", width=2),
            hovertemplate="%{x}",
            hoverinfo="skip",
        )

        if fig and row and col:
            fig.add_trace(data, row=row, col=col)
            fig.update_yaxes(
                visible=False, range=[-3, 3], fixedrange=True, row=row, col=col
            )

        else:
            fig = go.Figure(data=data)

            # Hovermode x makes two hover labels appear if they are at
            # the same point (default setting means only see the last
            # updated point)
            fig.update_layout(
                height=350,
                title_text="Reaction Forces",
                title_font_size=24,
                showlegend=False,
                hovermode="x",
                title_x=0.5,
            )

            xt = "Beam Length (" + self._units["length"] + ")"
            fig.update_xaxes(title_text=xt)

            # visible false means y axis doesnt show, fixing range means
            # wont zoom in y direction
            fig.update_yaxes(visible=False, range=[-3, 3], fixedrange=True)

        for position, values in self._reactions.items():
            x_ = round(values[0], 10)
            y_ = round(values[1], 10)
            m_ = round(values[2], 10)

            # if there are reaction forces
            if abs(x_) > 0 or abs(y_) > 0 or abs(m_) > 0:
                # subplot case
                if row and col:
                    fig = draw_reaction_hoverlabel(
                        fig,
                        reactions=[x_, y_, m_],
                        x_sup=position,
                        row=row,
                        col=col,
                        units=self._units,
                        precision=self.decimal_precision,
                    )

                    if abs(x_) > 0:
                        fig = draw_force(
                            fig,
                            PointLoad(x_, position, 0),
                            row=row,
                            col=col,
                            units=self._units,
                            precision=self.decimal_precision,
                        )
                    if abs(y_) > 0:
                        fig = draw_force(
                            fig,
                            PointLoad(y_, position, 90),
                            row=row,
                            col=col,
                            units=self._units,
                            precision=self.decimal_precision,
                        )
                    if abs(m_) > 0:
                        fig = draw_force(
                            fig,
                            PointTorque(m_, position),
                            row=row,
                            col=col,
                            units=self._units,
                            precision=self.decimal_precision,
                        )
                else:
                    fig = draw_reaction_hoverlabel(
                        fig,
                        reactions=[x_, y_, m_],
                        x_sup=position,
                        units=self._units,
                        precision=self.decimal_precision,
                    )

                    if abs(x_) > 0:
                        fig = draw_force(
                            fig,
                            PointLoad(x_, position, 0),
                            units=self._units,
                            precision=self.decimal_precision,
                        )
                    if abs(y_) > 0:
                        fig = draw_force(
                            fig,
                            PointLoad(y_, position, 90),
                            units=self._units,
                            precision=self.decimal_precision,
                        )
                    if abs(m_) > 0:
                        fig = draw_force(
                            fig,
                            PointTorque(m_, position),
                            units=self._units,
                            precision=self.decimal_precision,
                        )

        return fig

    def plot_normal_force(
        self,
        reverse_x=False,
        reverse_y=False,
        switch_axes=False,
        fig=None,
        row=None,
        col=None,
    ):
        """Returns a plot of the normal force as a function of the
        x-coordinate.

        Parameters
        ----------
        reverse_x : bool, optional
            reverse the x axes, by default False
        reverse_y : bool, optional
            reverse the y axes, by default False
        switch_axes: bool, optional
            switch the x and y axis, by default False
        fig : bool, optional
            Figure to append subplot diagram too. If creating standalone
            figure then None, by default None
        row : int, optional
            row number if subplot, by default None
        col : int, optional
            column number if subplot, by default None

        Returns
        -------
        figure : `plotly.graph_objs._figure.Figure`
            Returns a handle to a figure with the normal force diagram.
        """

        xlabel = "Beam Length"
        ylabel = "Normal Force"
        xunits = self._units["length"]
        yunits = self._units["force"]
        title = "Normal Force Plot"
        color = "red"

        fig = self.plot_analytical(
            "nf",
            color,
            title,
            xlabel,
            ylabel,
            xunits,
            yunits,
            reverse_x,
            reverse_y,
            switch_axes,
            fig=fig,
            row=row,
            col=col,
        )
        return fig

    def plot_shear_force(
        self,
        reverse_x=False,
        reverse_y=False,
        switch_axes=False,
        fig=None,
        row=None,
        col=None,
    ):
        """Returns a plot of the shear force as a function of the
        x-coordinate.

        Parameters
        ----------
        reverse_x : bool, optional
            reverse the x axes, by default False
        reverse_y : bool, optional
            reverse the y axes, by default False
        switch_axes: bool, optional
            switch the x and y axis, by default False
        fig : bool, optional
            Figure to append subplot diagram too. If creating standalone
            figure then None, by default None
        row : int, optional
            row number if subplot, by default None
        col : int, optional
            column number if subplot, by default None

        Returns
        -------
        figure : `plotly.graph_objs._figure.Figure`
            Returns a handle to a figure with the shear force diagram.
        """

        xlabel = "Beam Length"
        ylabel = "Shear Force"
        xunits = self._units["length"]
        yunits = self._units["force"]
        title = "Shear Force Plot"
        color = "aqua"

        fig = self.plot_analytical(
            "sf",
            color,
            title,
            xlabel,
            ylabel,
            xunits,
            yunits,
            reverse_x,
            reverse_y,
            switch_axes,
            fig=fig,
            row=row,
            col=col,
        )

        return fig

    def plot_bending_moment(
        self,
        reverse_x=False,
        reverse_y=False,
        switch_axes=False,
        fig=None,
        row=None,
        col=None,
    ):
        """Returns a plot of the bending moment as a function of the
        x-coordinate.

        Parameters
        ----------
        reverse_x : bool, optional
            reverse the x axes, by default False
        reverse_y : bool, optional
            reverse the y axes, by default False
        switch_axes: bool, optional
            switch the x and y axis, by default False
        fig : bool, optional
            Figure to append subplot diagram too. If creating standalone
            figure then None, by default None
        row : int, optional
            row number if subplot, by default None
        col : int, optional
            column number if subplot, by default None

        Returns
        -------
        figure : `plotly.graph_objs._figure.Figure`
            Returns a handle to a figure with the bending moment diagram.
        """

        xlabel = "Beam Length"
        ylabel = "Bending Moment"
        xunits = self._units["length"]
        yunits = self._units["moment"]
        title = "Bending Moment Plot"
        color = "lightgreen"
        fig = self.plot_analytical(
            "bm",
            color,
            title,
            xlabel,
            ylabel,
            xunits,
            yunits,
            reverse_x,
            reverse_y,
            switch_axes,
            fig=fig,
            row=row,
            col=col,
        )

        return fig

    def plot_deflection(
        self,
        reverse_x=False,
        reverse_y=False,
        switch_axes=False,
        fig=None,
        row=None,
        col=None,
    ):
        """Returns a plot of the beam deflection as a function of the
        x-coordinate.

        Parameters
        ----------
        reverse_x : bool, optional
            reverse the x axes, by default False
        reverse_y : bool, optional
            reverse the y axes, by default False
        switch_axes: bool, optional
            switch the x and y axis, by default False
        fig : bool, optional
            Figure to append subplot diagram too. If creating standalone
            figure then None, by default None
        row : int, optional
            row number if subplot, by default None
        col : int, optional
            column number if subplot, by default None

        Returns
        -------
        figure : `plotly.graph_objs._figure.Figure`
            Returns a handle to a figure with the deflection diagram.
        """

        xlabel = "Beam Length"
        ylabel = "Deflection"
        xunits = self._units["length"]
        yunits = self._units["deflection"]
        title = "Deflection Plot"
        color = "blue"
        fig = self.plot_analytical(
            "d",
            color,
            title,
            xlabel,
            ylabel,
            xunits,
            yunits,
            reverse_x,
            reverse_y,
            switch_axes,
            fig=fig,
            row=row,
            col=col,
        )

        return fig

    def plot_analytical(
        self,
        func,
        color="blue",
        title="",
        xlabel="",
        ylabel="",
        xunits="",
        yunits="",
        reverse_x=False,
        reverse_y=False,
        switch_axes=False,
        fig=None,
        row=None,
        col=None,
    ):
        """
        Auxiliary function for plotting a sympy.Piecewise analytical
        function.

        Parameters
        -----------
        func: str
            String representing function to query:
                'nf' if normal force.
                'sf' if shear force.
                'bm' if bending moment.
                'd' if deflection.
        color: str
            color to be used for plot, default blue.
        title: str
            title to show above the plot, optional
        xlabel: str
            physical variable displayed on the x-axis. Example: "Length"
        ylabel: str
            physical variable displayed on the y-axis. Example: "Shear
            force"
        xunits: str
            physical unit to be used for the x-axis. Example: "m"
        yunits: str
            phsysical unit to be used for the y-axis. Example: "kN"
        reverse_x : bool, optional
            reverse the x axes, by default False
        reverse_y : bool, optional
            reverse the y axes, by default False
        switch_axes: bool, optional
            switch the x and y axis, by default False
        fig : bool, optional
            Figure to append subplot diagram too. If creating standalone
            figure then None, by default None
        row : int, optional
            row number if subplot, by default None
        col : int, optional
            column number if subplot, by default None


        Returns
        -------
        figure : `plotly.graph_objs._figure.Figure`
            Returns a handle to a figure with the deflection diagram.
        """
        # get precision for display and assign to p
        p = self.decimal_precision

        # numpy array for x positions closely spaced (allow for graphing)
        x_vec = self._plotting_vectors["x"]
        y_vec = self._plotting_vectors[func]["y_vec"]

        fill = "tozeroy"

        if switch_axes:
            x_vec, y_vec = y_vec, x_vec
            xlabel, ylabel = ylabel, xlabel
            xunits, yunits = yunits, xunits
            fill = "tozerox"

            # will also need to update the annotation furtehr down
            # can also try add units to hoverlabels using meta?

        data = go.Scatter(
            x=x_vec.tolist(),
            y=y_vec.tolist(),
            meta=[xunits, yunits],
            mode="lines",
            line=dict(color=color, width=1),
            fill=fill,
            name=ylabel,
            hovertemplate=f"x: %{{x:.{p}f}} %{{meta[0]}}<br>f(x): %{{y:.{p}f}} %{{meta[1]}}",
        )

        if row and col and fig:
            fig = fig.add_trace(data, row=row, col=col)
        else:
            fig = go.Figure(data=data)
            fig.update_layout(title_text=title, title_font_size=30)
            fig.update_xaxes(title_text=str(xlabel + " (" + str(xunits) + ")"))

        if row and col:
            fig.update_yaxes(
                title_text=str(ylabel + " (" + str(yunits) + ")"), row=row, col=col
            )
            (
                fig.update_yaxes(autorange="reversed", row=row, col=col)
                if reverse_y
                else None
            )
            (
                fig.update_xaxes(autorange="reversed", row=row, col=col)
                if reverse_x
                else None
            )
        else:
            fig.update_yaxes(title_text=str(ylabel + " (" + str(yunits) + ")"))
            fig.update_yaxes(autorange="reversed") if reverse_y else None
            fig.update_xaxes(autorange="reversed") if reverse_x else None

        for q_val in self._query:
            q_res = self._get_query_value(q_val, func)
            if q_res < 0:
                ay = 40
            else:
                ay = -40

            if switch_axes:

                annotation = dict(
                    x=q_res,
                    y=q_val,
                    text=f"{q_val:.{p}f} {xunits}<br>{q_res:.{p}f} {yunits}",
                    showarrow=True,
                    arrowhead=1,
                    xref="x",
                    yref="y",
                    ax=ay,
                    ay=0,
                )
            else:
                annotation = dict(
                    x=q_val,
                    y=q_res,
                    text=f"{q_val:.{p}f} {xunits}<br>{q_res:.{p}f} {yunits}",
                    showarrow=True,
                    arrowhead=1,
                    xref="x",
                    yref="y",
                    ax=0,
                    ay=ay,
                )
            if row and col:
                fig.add_annotation(annotation, row=row, col=col)
            else:
                fig.add_annotation(annotation)

        return fig

    def update_decimal_precision(self, n):
        """Updates the decimal precision to show on graphs.

        Parameters
        ----------
        n : int
            Number of decimal places to be shown
        """

        # make sure input is integer
        assert type(n) is int
        self.decimal_precision = n

    def __str__(self):
        return f"""--------------------------------
        <Beam>
        length = {self._x0}
        loads = {str(len(self._loads))}"""

    def __repr__(self):
        return f"<Beam({self._x0})>"

    def sympy_expr_to_piecewise(self, func):
        """Takes a sympy function with Singularity expressions and
        changes any contained singularity expressions into Piecewise.

        Parameters
        ----------
        func: Sympy Function
            Sympy Function containing some SingularityFunction expressions.

        Returns
        -------
        func: Sympy Function
            Equivalent Sympy Function containing PieceWise functions in
            place of Singularity Functions.
        """
        # Function can be:
        # 1. a single Singularity Function
        # 2. a add function
        # a.containing multiplication functions,
        # b.containing non-SingularityFunction items,
        # c.containing SingularityFunction
        # 3. a Multiplication function
        # containing sf and other functions
        # containing other functions (ie piecewise)
        # 4. Not any of the above

        # Note: Function could be better using recursion for multiplication
        # and addition sympy classes. Can refactor in future.

        # case 1
        if isinstance(func, SingularityFunction):
            return func._eval_rewrite_as_Piecewise()
        # case 2 and 3
        elif func.is_Mul or func.is_Add:
            # nesting cases now, could use recursion to cover all possible
            # cases. Expect worst case to be add containing mul containing SF.
            # case 3
            if func.is_Mul:
                temp = 1
                for m in func.args:
                    if isinstance(m, SingularityFunction):
                        temp *= m._eval_rewrite_as_Piecewise()
                    else:
                        temp *= m
                return temp

            # case 2
            else:
                temp = 0
                for a in func.args:
                    # case 2 b
                    if isinstance(a, SingularityFunction):
                        temp += a._eval_rewrite_as_Piecewise()
                    # case 2 a
                    elif a.is_Mul:
                        temp_mul = 1
                        for m in a.args:
                            if isinstance(m, SingularityFunction):
                                temp_mul *= m._eval_rewrite_as_Piecewise()
                            else:
                                temp_mul *= m
                        temp += temp_mul
                    # case 2 c
                    else:
                        temp += a
                return temp

        # case 4.
        else:
            return func


if __name__ == "__main__":
    beam = Beam(5)
    beam.add_supports(Support(0))
    beam.add_loads(PointLoadV(2, 2), PointTorque(1, 5))
    beam.analyse()
