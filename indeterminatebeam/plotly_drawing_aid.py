"""Module to help draw plotly shapes, drawing and annotations"""

# Standard Library Imports
from math import radians

# Third Party Imports
import numpy as np
from sympy import lambdify, sympify, sin, cos, oo
from sympy.abc import x
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# Local Application Imports
from indeterminatebeam.loading import(
    PointLoad,
    PointLoadH,
    PointLoadV,
    PointTorque,
    UDL,
    TrapezoidalLoad,
    DistributedLoad,
)


def draw_line(fig, angle, x_sup, length=-20, xoffset=0, yoffset=0,
              color='red', line_width=2, row=None, col=None):
    """Draw an anchored line on a plotly figure.

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append line shape to.
    angle : int
        Angle of the line from the x-axis. Angle uses standard mathematical
        cartesian convention.
    x_sup : int
        The x position for the line to be anchored to.
    length : int, optional
        the line length, by default -20
    xoffset : int, optional
        The x-offset of the start of the line from the anchor, by default 0
    yoffset : int, optional
        The y-offset of the start of the line from the anchor, by default 0
    color : str, optional
        Line color, by default 'red'
    line_width : int, optional
        Line width, by default 2
    row : int or None,
        Row of subplot to draw line on. If None specified assumes a full plot,
        by default None.
    col : int or None,
        Column of subplot to draw line on. If None specified assumes a full
        plot, by default None.

    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with the arrowhead
        appended to it.
    """
    # Establish line start and end coordinates.
    x0 = xoffset
    y0 = yoffset
    x1 = x0 + int(sympify(length * cos(radians(angle))).evalf(2))
    y1 = y0 + int(sympify(length * sin(radians(angle))).evalf(2))

    # Create dictionary for shape object representing line.
    shape = dict(
        type="line",
        xref="x", yref="y",
        x0=x0, y0=y0, x1=x1, y1=y1,
        line_color=color, line_width=line_width,
        xsizemode='pixel', ysizemode='pixel',
        xanchor=x_sup, yanchor=0)

    # Append shape to plot or subplot
    if row and col:
        fig.add_shape(shape, row=row, col=col)
    else:
        fig.add_shape(shape)

    return fig


def draw_arrowhead(fig, angle, x_sup, length=5, xoffset=0, yoffset=0,
                   color='red', line_width=2, row=None, col=None):
    """Draw an anchored arrowhead on a plotly figure.

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append arrowhead shape to.
    angle : int
        Angle of the arrowhead from the x-axis. Angle uses standard
        mathematical cartesian convention.
    x_sup : int
        The x position for the arrowhead to be anchored to.
    length : int, optional
        the arrowhead length, by default 5
    xoffset : int, optional
        The x-offset of the start of the arrowhead from the anchor, by
        default 0
    yoffset : int, optional
        The y-offset of the start of the arrowhead from the anchor, by
        default 0
    color : str, optional
        arrowhead color, by default 'red'
    line_width : int, optional
        Line width, by default 2
    row : int or None,
        Row of subplot to draw line on. If None specified assumes a full plot,
        by default None.
    col : int or None,
        Column of subplot to draw line on. If None specified assumes a full
        plot, by default None.

    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with the arrowhead
        appended to it.
    """
    # Holds lines 90 degrees apart to represent arrowhead. Constructed so 0
    # degrees is pointing right, follows conventions in documentation for angle

    # Angle conversion to allow for compatability with draw_line function
    a1 = 225 + angle
    a2 = 135 + angle

    # Append line to figure (half of arrowhead)
    fig = draw_line(
        fig,
        angle=a1,
        x_sup=x_sup,
        length=length,
        xoffset=xoffset,
        yoffset=yoffset,
        color=color,
        line_width=line_width,
        row=row,
        col=col)

    # Append line to figure (half of arrowhead)
    fig = draw_line(
        fig,
        angle=a2,
        x_sup=x_sup,
        length=length,
        xoffset=xoffset,
        yoffset=yoffset,
        color=color,
        line_width=line_width,
        row=row,
        col=col)

    return fig


def draw_arrow(fig, angle, force, x_sup, xoffset=0, yoffset=0, color='red',
               line_width=2, arrowhead=5, arrowlength=40, show_values=True,
               row=None, col=None,units="N", precision=3):
    """Draw an anchored arrow on a plotly figure.

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append arrow shape to.
    angle : int
        Angle of the arrow from the x-axis. Angle uses standard
        mathematical cartesian convention.
    force: int
        force that the arrow will represent. Only need to know whether it
        is positive or negative, but it generally is easiest to just parse
        the whole force in.
    x_sup : int
        The x position for the arrow to be anchored to.
    xoffset : int, optional
        The x-offset of the start of the arrow from the anchor, by default 0
    yoffset : int, optional
        The y-offset of the start of the arrow from the anchor, by default 0
    color : str, optional
        arrow color, by default 'red'
    line_width : int, optional
        Line width, by default 2
    arrowhead : int, optional
        Size of the arrowhead lines, by default 5
    arrowlength: int, optional
        length of the arrow line, by default 30
    show_values: bool,optional
        If true annotates numerical force value next to arrow, by default True.
    row : int or None,
        Row of subplot to draw line on. If None specified assumes a full plot,
        by default None.
    col : int or None,
        Column of subplot to draw line on. If None specified assumes a full
        plot, by default None.
    units: str,
        The units suffix drawn with the force value.
    precision: int,
        The decimal precision to be displayed for annotations, by default 3.

    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with the arrow
        appended to it.
    """
    # get precision as p
    p = precision

    # Factor to switch arrow direction based on force sign
    if force > 0:
        d = 1
    elif force < 0:
        d = -1
    else:
        return fig

    # Draw arrowhead for force
    fig = draw_arrowhead(
        fig,
        angle,
        x_sup,
        length=arrowhead * d,
        xoffset=xoffset,
        yoffset=yoffset,
        color=color,
        line_width=line_width,
        row=row,
        col=col)

    # Draw arrowline for force
    fig = draw_line(
        fig,
        angle,
        x_sup,
        length=-1 * arrowlength * d,
        xoffset=xoffset,
        yoffset=yoffset,
        color=color,
        line_width=line_width,
        row=row,
        col=col)
    if show_values:
        # determine start and end of arrow
        x0 = xoffset + x_sup
        y0 = yoffset
        x1 = (
            int(sympify(-arrowlength * d * cos(radians(angle))).evalf(2))
            ) * 1.1
        y1 = (
            int(sympify(-arrowlength * d * sin(radians(angle))).evalf(2))
            ) * 1.3

        # make so text doesnt intersect x axis
        if abs(y1) < 5:
            if y1 >= 0:
                y1 = 10
            else:
                y1 = -10

        annotation = dict(
            xref="x", yref="y",
            x=x0,
            y=y0,
            xshift=x1,
            yshift=y1,
            text=f"{force:.{p}f} {units}",
            font_color=color,
            showarrow=False,
        )

        # Append shape to plot or subplot
        if row and col:
            fig.add_annotation(annotation, row=row, col=col)
        else:
            fig.add_annotation(annotation)

    return fig


def draw_support_triangle(fig, x_sup, orientation="up", row=None, col=None):
    """Draw an anchored triangle on a plotly figure.

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append arrow shape to.
    x_sup : int
        The x position for the arrow to be anchored to.
    orientation : 'up' or 'right, optional
        direction that the arrow faces, by default "up"
    row : int or None,
        Row of subplot to draw line on. If None specified assumes a full plot,
        by default None.
    col : int or None,
        Column of subplot to draw line on. If None specified assumes a full
        plot, by default None.


    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with the triangle
        appended to it.
    """

    if orientation in ['up', 'right']:

        # Define the triangle as a point using the scatter marker.
        trace = go.Scatter(
            x=[x_sup],
            y=[0],
            fill="toself",
            showlegend=False,
            mode="markers",
            name='Support',
            marker=dict(
                symbol="arrow-" + orientation,
                size=10,
                color='blue'),
            hovertemplate=None,
            hoverinfo="skip")

        # Append trace to plot or subplot
        if row and col:
            fig.add_trace(trace, row=row, col=col)
        else:
            fig.add_trace(trace)

    return fig


def draw_support_rectangle(fig, x_sup, orientation="up", row=None, col=None):
    """Draw an anchored rectangle on a plotly figure.

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append arrow shape to.
    x_sup : int
        The x position for the arrow to be anchored to.
    orientation : 'up' or 'right, optional
        direction that the arrow faces, by default "up"
    row : int or None,
        Row of subplot to draw line on. If None specified assumes a full plot,
        by default None.
    col : int or None,
        Column of subplot to draw line on. If None specified assumes a full
        plot, by default None.


    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with the rectangle
        appended to it.
    """
    if orientation in ['up', 'right']:

        # rectangle is offset by -2 so that when a thickness of 4 is used
        # points are defined for a line length of 10
        if orientation == 'up':
            x0, x1, y0, y1 = -5, 5, -2, -2
        elif orientation == 'right':
            x0, x1, y0, y1 = -2, -2, -5, 5

        # Create dictionary for shape object representing rectangle.
        shape = dict(
            type="rect",
            xref="x", yref="y",
            x0=x0, y0=y0, x1=x1, y1=y1,
            line_color="blue",
            line_width=4,
            xsizemode='pixel',
            ysizemode='pixel',
            fillcolor='blue',
            xanchor=x_sup,
            yanchor=0)

        # Append shape to plot or subplot
        if row and col:
            fig.add_shape(shape, row=row, col=col)
        else:
            fig.add_shape(shape)

    return fig


def draw_moment(
        fig,
        moment,
        x_sup,
        color='magenta',
        show_values=True,
        row=None,
        col=None,
        units="N.m",
        precision=3):
    """Draw a moment (torque) shape (circular arrow) on a plotly figure.

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append circular arrow shape to.
    x_sup : int
        The x position for the circular arrow to be anchored to.
    moment: float,
        magnitude of moment, used for direction and appending value.
    color : str, optional
        color of circular arrow, default 'magenta'
    show_values: bool,optional
        If true annotates numerical force value next to arrow, by default True.
    row : int or None,
        Row of subplot to draw line on. If None specified assumes a full plot,
        by default None.
    col : int or None,
        Column of subplot to draw line on. If None specified assumes a full
        plot, by default None.
    units: str,
        The units suffix drawn with the moment value. Default is 'N.m'.
    precision: int,
        The number of decimal places to display on annotation, by default 3.

    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with the circular
        arrow appended to it.
    """
    # Choose symbol based on direction given
    if moment < 0:
        d = "⭮"
    elif moment > 0:
        d = "⭯"
    else:
        return fig

    # Create dictionary for annotation object representing moment.
    annotation = dict(
        x=x_sup, y=0,
        text=d,
        showarrow=False,
        yshift=0,
        font_size=26,
        font_color=color,
    )

    # Append shape to plot or subplot
    if row and col:
        fig.add_annotation(annotation, row=row, col=col)
    else:
        fig.add_annotation(annotation)

    # get precision and name as p
    p = precision

    # Add text if show_values is true
    if show_values:

        annotation = dict(
            xref="x", yref="y",
            x=x_sup,
            y=0,
            yshift=-20,
            text=f"{moment:.{p}f} {units}",
            font_color=color,
            showarrow=False,
        )

        # Append shape to plot or subplot
        if row and col:
            fig.add_annotation(annotation, row=row, col=col)
        else:
            fig.add_annotation(annotation)

    return fig


def draw_force(
    fig,
    load,
    row=None,
    col=None,
    units={'moment':'N.m', 'force':'N','distributed':"N/m"},
    precision=3):
    """Draw a force (for load or reaction) on a plotly figure

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append force representation to.
    load : instance of a load class
        force to be represented on figure
    row : int or None,
        Row of subplot to draw line on. If None specified assumes a full plot,
        by default None.
    col : int or None,
        Column of subplot to draw line on. If None specified assumes a full
        plot, by default None.
    units : dict,
        unit dictionary associating the units with different properties of the beam.
        default is {'moment':'N.m', 'force':'N','distributed':"N/m"}.
    precision: int,
        The number of decimal places to display on annotation, by default 3.


    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with the force
        representation appended to it.
    """

    if isinstance(load, PointTorque):
        moment, x_sup = load.force, load.position
        fig = draw_moment(
            fig,
            moment,
            x_sup,
            row=row,
            col=col,
            units=units['moment'],
            precision=precision)

    elif isinstance(load, PointLoad):
        force, x_sup, angle = load.force, load.position, load.angle

        fig = draw_arrow(
            fig,
            angle,
            force,
            x_sup,
            row=row,
            col=col,
            units=units['force'],
            precision=precision,
            )

    elif isinstance(load, (DistributedLoad, UDL, TrapezoidalLoad)):
        angle = load.angle
        if angle % 90 == 0:
            # vertical or horizontal
            color = 'mediumpurple'
        if angle % 180 == 0:
            # horizontal only
            color = 'maroon'
        elif angle % 90 != 0:
            color = 'green'

        if sin(angle) >= 0:
            angle_factor = -1
        else:
            angle_factor = 1

        if isinstance(load, DistributedLoad):
            name = 'Distributed<br>Load'
            x0, x1 = load.span
            expr = load.expr
            # numpy array for x positions closely spaced (allow for graphing)
            x_vec = np.linspace(x0, x1, int(min((x1 - x0) * 100 + 1, 1e3)))
            y_lam = lambdify(x, expr, 'numpy')
            y_vec = np.array([round(float(y_lam(t)), 10) for t in x_vec])

        elif isinstance(load, UDL):
            name = 'UDL'
            x_vec = np.array(load.span)
            y_vec = np.array([load.force, load.force])
        else:
            name = 'Trapezoidal<br>Load'
            x_vec = np.array(load.span)
            y_vec = np.array(load.force)

        largest = abs(max(y_vec, key=abs))

        # draw each function normalised to 1. ie the max is always 1.
        # largest accounts for magnitude, angle factor rectifies polarity.
        y_vec = (angle_factor) * y_vec / largest

        # Create trace object for graph of distributed force
        trace = go.Scatter(
            x=x_vec.tolist(),
            y=y_vec.tolist(),
            mode='lines',
            line=dict(
                color=color,
                width=1),
            fill='tozeroy',
            name=name,
            hovertemplate="",
            hoverinfo="skip")

        # Append to plot or subplot
        if row and col:
            fig.add_trace(trace, row=row, col=col)
        else:
            fig.add_trace(trace)

        # draw arrow for left force and right force (if larger than 2% of
        # max load)
        for a in [0, -1]:
            if abs(y_vec[a]) > 0.02:
                fig = draw_arrow(
                    fig,
                    angle,
                    angle_factor * y_vec[a] * largest,
                    x_vec[a],
                    color=color,
                    arrowlength=30 * abs(y_vec[a]),
                    row=row,
                    col=col,
                    units=units['distributed'])

    return fig


def draw_load_hoverlabel(
    fig,
    load,
    row=None,
    col=None,
    units={'length':'m','moment':'N.m', 'force':'N','distributed':"N/m"},
    precision=3,
    ):
    """Draw a load hoverlabel on a plotly figure

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append force representation to.
    load : instance of a load class
        force to be represented on figure
    row : int or None,
        Row of subplot to draw line on. If None specified assumes a full plot,
        by default None.
    col : int or None,
        Column of subplot to draw line on. If None specified assumes a full
        plot, by default None.
    units : dict,
        unit dictionary associating the units with different properties of the beam.
        default is {'length':'m','moment':'N.m', 'force':'N','distributed':"N/m"}.
    precision: int,
        The number of decimal places to display on annotation, by default 3.

    Returns
    -------
    plotly figure
        plotly figure to append hoverlabel representation to.
    """
    y_sup = 0

    # get precision and name as p
    p = precision

    if isinstance(load, (PointLoad, PointTorque)):
        x_sup = load.position
        color = 'red'
        meta = [load.force, load.position, units['length'], units['force'], units['moment']]  # load, position

        if isinstance(load, PointTorque):
            color = 'magenta'
            hovertemplate = f'x: %{{meta[1]:.{p}f}} %{{meta[2]}}<br>Moment: %{{meta[0]:.{p}f}} %{{meta[4]}}'
            name = 'Point<br>Torque'
        elif isinstance(load, PointLoad):
            meta.append(load.angle)
            hovertemplate = f'x: %{{meta[1]:.{p}f}} %{{meta[2]}}<br>Force: %{{meta[0]:.{p}f}} %{{meta[3]}}\
            <br>Angle: %{{meta[5]:.{p}f}} deg'
            name = 'Point<br>Load'

        # Define hoverlabel as a marker with 0 opacity and a hovertemplate that
        # relies on meta data field
        trace = go.Scatter(
            x=[x_sup], y=[y_sup],
            showlegend=False, mode="markers",
            name=name,
            meta=meta,
            marker=dict(symbol="triangle-up", size=10, color=color),
            hovertemplate=hovertemplate,
            hoverinfo="skip",
            opacity=0
        )

        # Append hoverlabel to plot or subplot
        if row and col:
            fig.add_trace(trace, row=row, col=col)
        else:
            fig.add_trace(trace)

    # Else is distributed load type, hoverlabel needed for arrow at each side
    # of function
    elif isinstance(load, (DistributedLoad, UDL, TrapezoidalLoad)):
        if load.angle % 90 == 0:
            # vertical or horizontal
            color = 'mediumpurple'
        if load.angle % 180 == 0:
            # horizontal only
            color = 'maroon'
        elif load.angle % 90 != 0:
            color = 'green'

        x0, x1 = load.span
        angle = load.angle
        name = 'Distributed<br>Load'

        if isinstance(load, DistributedLoad):
            expr = load.expr
            meta = [
                (x0, round(float(expr.subs(x, x0)), 10), angle),
                (x1, round(float(expr.subs(x, x1)), 10), angle)
            ]

        elif isinstance(load, UDL):
            meta = [
                (x0, load.force, angle),
                (x1, load.force, angle)
            ]
        else:
            meta = [
                (x0, load.force[0], angle),
                (x1, load.force[1], angle)
            ]
        
        
        hovertemplate = f'x: %{{meta[0]:.{p}f}} %{{meta[3]}}<br>Force: %{{meta[1]:.{p}f}} %{{meta[4]}}\
        <br>Angle: %{{meta[2]:.{p}f}} deg'

        for x_, y_, a_ in meta:
            trace = go.Scatter(
                x=[x_], y=[0],
                showlegend=False, mode="markers",
                name=name,
                meta=[x_, y_, a_, units['length'], units['distributed']],
                marker=dict(symbol="triangle-up", size=10, color=color),
                hovertemplate=hovertemplate,
                hoverinfo="skip",
                opacity=0
            )

            if row and col:
                fig.add_trace(trace, row=row, col=col)
            else:
                fig.add_trace(trace)

    return fig


def draw_reaction_hoverlabel(
    fig,
    reactions,
    x_sup,
    row=None,
    col=None,
    units={'length':'m','moment':'N.m', 'force':'N','distributed':"N/m"},
    precision=3
    ):
    """Draw a reaction hoverlabel on a plotly figure

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append force representation to.
    load : instance of a load class
        force to be represented on figure
    x_sup : int
        The position for the hoverlabel to be anchored to i.e. the position
        of a support or spring.
    row : int or None,
        Row of subplot to draw line on. If None specified assumes a full plot,
        by default None.
    col : int or None,
        Column of subplot to draw line on. If None specified assumes a full
        plot, by default None.
    units : dict,
        unit dictionary associating the units with different properties of the beam.
        default is {'length':'m','moment':'N.m', 'force':'N','distributed':"N/m"}.
    precision: int,
        The number of decimal places to display on annotation, by default 3.

    Returns
    -------
    plotly figure
        plotly figure to append hoverlabel representation to.
    """
    # reactions should be [x,y,m]
    x_, y_, m_ = reactions

    # get precision as p
    p = precision

    # Write hovertemplate depending on support restraints
    hovertemplate = f"Reactions<br>x coord: %{{x:.{p}f}} %{{meta[3]}}"
    if x_:
        hovertemplate += f"<br>x: %{{meta[0]:.{p}f}} %{{meta[4]}}"
    if y_:
        hovertemplate += f"<br>y: %{{meta[1]:.{p}f}} %{{meta[4]}}"
    if m_:
        hovertemplate += f"<br>m: %{{meta[2]:.{p}f}} %{{meta[5]}}"

    # Create scatter object with opacity 0 for hovertemplate
    trace = go.Scatter(
        x=[x_sup], y=[0],
        showlegend=False, mode="markers",
        name="Reaction",
        meta=[x_, y_, m_, units['length'], units['force'], units['moment']],
        marker=dict(symbol="triangle-up", size=10, color='red'),
        hovertemplate=hovertemplate,
        hoverinfo="skip",
        opacity=0
    )

    # Add to plot or subplot
    if row and col:
        fig.add_trace(trace, row=row, col=col)
    else:
        fig.add_trace(trace)

    return fig


def draw_support_hoverlabel(
    fig,
    support,
    kx=0,
    ky=0,
    row=None,
    col=None,
    units={'length':'m','stiffness':"N/m"},
    precision=3,
    ):
    """Draw a reaction hoverlabel on a plotly figure

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append force representation to.
    support : Support instance
        support to be represented on figure
    kx : int, optional
        The stiffness of the support in the x direction, default 0
    ky : int, optional
        The stiffness of the support in the y direction, default 0
    row : int or None,
        Row of subplot to draw line on. If None specified assumes a full plot,
        by default None.
    col : int or None,
        Column of subplot to draw line on. If None specified assumes a full
        plot, by default None.
    units : dict,
        unit dictionary associating the units with different properties of the beam.
        default is {'length':'m','stiffness':"N/m"}.
    precision: int,
        The number of decimal places to display on annotation, by default 3.

    Returns
    -------
    plotly figure
        plotly figure with hoverlabel appended to it.
    """
    # This could be implemented better (hovertemplates in general could be)
    if kx == oo:
        kx = 0
    if ky == oo:
        ky = 0

    # if ky of kx is > 0 then we are defining a spring label
    # otherwise we are definind a support label

    fixed = support._fixed
    x_sup = support._position

    # get p as precison
    p = precision

    # Spring
    if kx or ky:
        name = "Spring"
        color = 'orange'
        meta = [kx, ky, units['length'], units['distributed']]
        hovertemplate = f"x: %{{x:.{p}f}} %{{meta[2]}}"
        if kx:
            hovertemplate += f"<br>kx: %{{meta[0]:.{p}f}} %{{meta[3]}}"
        if ky:
            hovertemplate += f"<br>ky: %{{meta[1]:.{p}f}} %{{meta[3]}}"

    # Support
    else:
        name = "Support"
        color = 'blue'
        meta = [str(fixed), units['length']]
        hovertemplate = f"x: %{{x:.{p}f}} %{{meta[1]}}<br>Fixed: %{{meta[0]}}"

    # necessary for hover information, opacicity 0 so not visible otherwise
    # symbol is arbritrary since invisible
    trace = go.Scatter(
        x=[x_sup], y=[0],
        showlegend=False, mode="markers",
        name=name,
        meta=meta,
        marker=dict(symbol="triangle-up", size=10, color=color),
        hovertemplate=hovertemplate,
        hoverinfo="skip",
        opacity=0
    )

    # Append to plot or subplot.
    if row and col:
        fig.add_trace(trace, row=row, col=col)
    else:
        fig.add_trace(trace)

    return fig


def draw_support_rollers(fig, x_sup, orientation='up', offset=1, row=None,
                         col=None):
    """Draw an anchored group of 3 circles on a plotly figure to represent a
    roller shape.

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append roller shape to.
    x_sup : int
        The x position for the roller shape to be anchored to.
    orientation : 'up' or 'right, optional
        direction that the arrow faces, by default "up"
    offset : int
        offset of the rollers from support location, typically 1 or 0.6,
        default 1.
    row : int or None,
        Row of subplot to draw line on. If None specified assumes a full plot,
        by default None.
    col : int or None,
        Column of subplot to draw line on. If None specified assumes a full
        plot, by default None.

    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with the roller shape
        appended to it.
    """
    radius = 1
    if orientation in ['up', 'right']:

        # shifting the position from x_sup to make more aesthetic for
        # triangle or rectangle.
        # A triangle is wider so an offset of 1 is used.
        # A rectangle uses an offset shorter, currently 0.6 is used.
        shift = offset * -13

        # set centre of circles to be drawn
        if orientation == 'up':
            centres = [(0, shift), (-4, shift), (4, shift)]
        elif orientation == 'right':
            centres = [(shift, 0), (shift, -4), (shift, 4)]

        for xc, yc in centres:

            # Create circle for each point defined in centres
            shape = dict(
                type="circle",
                xref="x", yref="y",
                x0=xc - radius, y0=yc - radius, x1=xc + radius, y1=yc + radius,
                line_color="blue",
                xsizemode='pixel',
                ysizemode='pixel',
                fillcolor='blue',
                xanchor=x_sup,
                yanchor=0
            )

            # Append circle to plot or subplot.
            if row and col:
                fig.add_shape(shape, row=row, col=col)
            else:
                fig.add_shape(shape)

    return fig


def draw_support_spring(
        fig,
        support,
        orientation="up",
        color='orange',
        show_values=True,
        row=None,
        col=None,
        units="N/m",
        precision=3
        ):
    """Draw an anchored spring shape on a plotly figure.

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append roller shape to.
    support : Support instance
        support to be represented on figure
    orientation : 'up' or 'right, optional
        direction that the arrow faces, by default "up"
    color : str, optional
        color of spring, by default 'orange'.
    show_values: bool,optional
        If true annotates numerical force value next to arrow, by default True.
    row : int or None,
        Row of subplot to draw line on. If None specified assumes a full plot,
        by default None.
    col : int or None,
        Column of subplot to draw line on. If None specified assumes a full
        plot, by default None.
    units: str,
        The units suffix drawn with the stiffness value. Default is 'N/m'.
    precision: int,
        The number of decimal places to display on annotation, by default 3.

    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with the spring shape
        appended to it."""

    # get precision as p
    p = precision

    x_sup = support._position

    # x0 and y0 initialised so that when loop through each point in the coords
    # list will have two points to reference.
    x0, y0 = 0, 0

    # reduction of 0.8 used on coords specified (simple reduction modification)
    reduce = 0.8

    if orientation in ['up', 'right']:
        # coords are points between lines to be created
        # label and stiffness are defined for use as meta data to be added to
        # the hovertemplate
        if orientation == 'right':
            coords = [(5, 0), (7, 5), (12, -5), (14, 0), (19, 0)]
            stiffness = support._stiffness[0]
        else:
            coords = [(0, 5), (-5, 7), (5, 12), (0, 14), (0, 19)]
            stiffness = support._stiffness[1]

        # x1 and y1 are the ends of the line to be created
        for x1, y1 in coords:
            x1, y1 = x1 * reduce, y1 * reduce

            # Create dictionary for line shape object. Note: multiple lines
            # added but reference must always be to the same xanchor
            shape = dict(
                type="line",
                xref="x", yref="y",
                x0=x0, y0=y0, x1=x1, y1=y1,
                line_color=color,
                line_width=2,
                xsizemode='pixel',
                ysizemode='pixel',
                xanchor=x_sup,
                yanchor=0
            )

            # Append line to plot or subplot
            if row and col:
                fig.add_shape(shape, row=row, col=col)
            else:
                fig.add_shape(shape)

            # set end point to be start point for the next line
            x0, y0 = x1, y1

        if show_values:
            y0 = max(y0, 7)

            annotation = dict(
                xref="x", yref="y",
                x=x_sup,
                y=0,
                yshift=y0 * 1.5,
                xshift=x0 * 2,
                text=f"{stiffness:.{p}f} {units}",
                font_color=color,
                showarrow=False,
            )

            # Append shape to plot or subplot
            if row and col:
                fig.add_annotation(annotation, row=row, col=col)
            else:
                fig.add_annotation(annotation)

    return fig


def draw_support(
    fig,
    support,
    row=None,
    col=None,
    units = {'length':'m', 'stiffness':'N/m'},
    precision=3):
    """Draw a support on a plotly figure.

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append roller shape to.
    support : Support instance
        support to be represented on figure
    row : int or None,
        Row of subplot to draw line on. If None specified assumes a full plot,
        by default None.
    col : int or None,
        Column of subplot to draw line on. If None specified assumes a full
        plot, by default None.
    units : dict,
        unit dictionary associating the units with different properties of the beam.
        default is {'length':'m', 'stiffness':'N/m'}.
    precision: int,
        The number of decimal places to display on annotation, by default 3.

    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with a support drawn."""

    # grab values from support instance
    x_sup = support._position
    fixed = support._fixed
    DOF = support._DOF

    # DOF has 1 for partial restraint and fixed has 1 for full restraint. They
    # are only different if a spring support exists
    springx = DOF[0] - fixed[0]
    springy = DOF[1] - fixed[1]

    # run through all possible cases for supports and draw.
    # Note: runs through the values in fixed not DOF so as to not represent
    # the spring more than once (helps with clarity)
    if fixed == [0, 0, 0]:
        fig = fig
    else:
        fig = draw_support_hoverlabel(fig, support, row=row, col=col, precision=precision)

        if fixed == [0, 0, 1]:
            fig = draw_moment(
                fig,
                moment=1,
                x_sup=support._position,
                color='blue',
                show_values=False,
                row=row,
                col=col)

        elif fixed == [0, 1, 0]:
            fig = draw_support_rollers(
                fig,
                x_sup=support._position,
                orientation='up',
                offset=1,
                row=row,
                col=col)
            fig = draw_support_triangle(
                fig,
                x_sup=support._position,
                orientation='up',
                row=row,
                col=col)

        elif fixed == [1, 0, 0]:
            fig = draw_support_rollers(
                fig,
                x_sup=support._position,
                orientation='right',
                offset=1,
                row=row,
                col=col)
            fig = draw_support_triangle(
                fig,
                x_sup=support._position,
                orientation='right',
                row=row,
                col=col)

        elif fixed == [0, 1, 1]:
            fig = draw_support_rollers(
                fig,
                x_sup=support._position,
                orientation='up',
                offset=0.6,
                row=row,
                col=col)
            fig = draw_support_rectangle(
                fig,
                x_sup=support._position,
                orientation='up',
                row=row,
                col=col)

        elif fixed == [1, 0, 1]:
            fig = draw_support_rollers(
                fig,
                x_sup=support._position,
                orientation='right',
                offset=0.6,
                row=row,
                col=col)
            fig = draw_support_rectangle(
                fig,
                x_sup=support._position,
                orientation='right',
                row=row,
                col=col)
        elif fixed == [1, 1, 0]:
            fig = draw_support_triangle(
                fig,
                x_sup=support._position,
                orientation='up',
                row=row,
                col=col)
        elif fixed == [1, 1, 1]:
            fig = draw_support_rectangle(
                fig,
                x_sup=support._position,
                orientation='right',
                row=row,
                col=col)

        else:
            raise ValueError(
                f"{fixed} does not match the expected support fixed \
                    for support at {x_sup}")

    # if springx then draw a spring with right orientation (value for
    # orientation would be better written as 'x' but wanted to maintain
    # convention used)
    if springx:
        fig = draw_support_spring(
            fig,
            support,
            orientation="right",
            row=row,
            col=col,
            units=units['stiffness'],
            precision=precision,
        )

    # if springy then draw a spring with up orientation
    if springy:
        fig = draw_support_spring(
            fig,
            support,
            orientation="up",
            row=row,
            col=col,
            units=units['stiffness'],
            precision=precision,
        )

    # draw hover label for springs
    if springx or springy:
        fig = draw_support_hoverlabel(
            fig,
            support,
            kx=support._stiffness[0],
            ky=support._stiffness[1],
            row=row,
            col=col,
            units=units,
            precision=precision)

    return fig
