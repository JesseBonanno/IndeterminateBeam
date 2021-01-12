"""Module to help draw plotly shapes, drawing and annotations"""

from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from sympy import lambdify, sympify, sin, cos,oo
from sympy.abc import x
from math import radians 

def draw_line(fig,angle,x_sup,length=-20, xoffset=0, yoffset=0,color = 'red',line_width = 2,row=None,col=None):
    """Draw an anchored line on a plotly figure

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append line shape to.
    angle : int
        Angle of the line from the x-axis. Angle uses standard mathematical cartesian convention.
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

    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with the arrowhead appended to it.
    """
    x0 = xoffset
    y0 = yoffset
    x1 = x0 + int(sympify(length*cos(radians(angle))).evalf(2))
    y1 = y0 + int(sympify(length*sin(radians(angle))).evalf(2))
    shape = dict(type="line",
        xref="x", yref="y",
        x0=x0, y0=y0, x1=x1, y1=y1,
        line_color=color,
        line_width=line_width,
        xsizemode='pixel',
        ysizemode='pixel',
        xanchor=x_sup,
        yanchor=0)
    
    if row and col:
        fig.add_shape(shape,row=row,col=col)
    else:
        fig.add_shape(shape)

    return fig

def draw_arrowhead(fig,angle,x_sup,length=5, xoffset=0,yoffset=0,color='red',line_width =2,row=None,col=None):
    """Draw an anchored arrowhead on a plotly figure

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append arrowhead shape to.
    angle : int
        Angle of the arrowhead from the x-axis. Angle uses standard mathematical cartesian convention.
    x_sup : int
        The x position for the arrowhead to be anchored to.
    length : int, optional
        the arrowhead length, by default 5
    xoffset : int, optional
        The x-offset of the start of the arrowhead from the anchor, by default 0
    yoffset : int, optional
        The y-offset of the start of the arrowhead from the anchor, by default 0
    color : str, optional
        arrowhead color, by default 'red'
    line_width : int, optional
        Line width, by default 2

    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with the arrowhead appended to it.
    """
    ##holds lines 90 degrees apart
    ##constructed so that 0 degrees is pointing right, follows conventions in documentatino for angle
    a1 = 225 + angle
    a2 = 135 + angle
    fig = draw_line(fig,angle=a1,x_sup=x_sup,length=length,xoffset=xoffset,yoffset=yoffset,color=color,line_width=line_width,row=row,col=col)
    fig = draw_line(fig,angle=a2,x_sup=x_sup,length=length,xoffset=xoffset,yoffset=yoffset,color=color,line_width=line_width,row=row,col=col)
    return fig

def draw_arrow(fig,angle,force,x_sup, xoffset=0,yoffset=0,color='red',line_width =2, arrowhead=5, arrowlength=30,row=None,col=None):
    """Draw an anchored arrow on a plotly figure

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append arrow shape to.
    angle : int
        Angle of the arrow from the x-axis. Angle uses standard mathematical cartesian convention.
    force: int
        force that the arrow will represent. Only need to know whether it is positive or negative, 
        but it generally is easiest to just parse the whole force in.
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


    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with the arrow appended to it.
    """

    if force>0:
        d=1
    else:
        d=-1

    fig = draw_arrowhead(fig,angle,x_sup,length=arrowhead*d,xoffset=xoffset,yoffset=yoffset,color=color, line_width = line_width,row=row,col=col) 
    fig = draw_line(fig,angle,x_sup,length=-1*arrowlength*d,xoffset=xoffset,yoffset=yoffset,color=color, line_width = line_width,row=row,col=col)

    return fig

def draw_support_triangle(fig,x_sup,orientation="up",row=None,col=None):
    """Draw an anchored triangle on a plotly figure.

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append arrow shape to.
    x_sup : int
        The x position for the arrow to be anchored to.
    orientation : 'up' or 'right, optional
        direction that the arrow faces, by default "up"

    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with the triangle appended to it.
    """
    ##define the triangle as a point using the scatter marker.
    ##as the shape here is a trace hover data can be directly associated with it.
    ##meta is created to allow for the hovertemplate to use variables defined from teh support instance.
    ##meta must be the same size as the data, in this case it is easy to match since there is just one point.
    if orientation in ['up','right']:
        trace = go.Scatter(x=[x_sup], y=[0], fill="toself",
        showlegend=False, mode="markers",
        name = 'Support',
        marker= dict(symbol="arrow-"+orientation,size = 10, color = 'blue' ),
        hovertemplate=None,
        hoverinfo="skip",
        )
        if row and col:
            fig.add_trace(trace,row=row,col=col)
        else:
            fig.add_trace(trace)

    return fig

def draw_support_rectangle(fig,x_sup,orientation="up",row=None,col=None):
    """Draw an anchored rectangle on a plotly figure.

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append arrow shape to.
    x_sup : int
        The x position for the arrow to be anchored to.
    orientation : 'up' or 'right, optional
        direction that the arrow faces, by default "up"

    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with the rectangle appended to it.
    """
    if orientation in ['up','right']:
        
        ##rectangle is offset by -2 so that when a thickness of 4 is used the top (or right) of the shape directly correlates with the locatino of the support
        ##points are defined for a line length of 10
        if orientation=='up':
            x0,x1,y0,y1=-5,5,-2,-2
        elif orientation=='right':
            x0,x1,y0,y1=-2,-2,-5,5


        ##shape is added as a rect, not sure what the difference between this and a line is (maybe that you can have a hollow rectangle)

        shape = dict(type="rect",
        xref="x", yref="y",
        x0=x0, y0=y0, x1=x1, y1=y1,
        line_color="blue",
        line_width=4,
        xsizemode='pixel',
        ysizemode='pixel',
        fillcolor='blue',
        xanchor=x_sup,
        yanchor=0)

        if row and col:
            fig.add_shape(shape,row=row,col=col)
        else:
            fig.add_shape(shape)

    return fig

def draw_moment(fig, x_sup, direction='clockwise',color = 'red',row=None,col=None):
    """Draw a moment (torque) shape (circular arrow) on a plotly figure.

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append circular arrow shape to.
    x_sup : int
        The x position for the circular arrow to be anchored to.
    direction : 'clockwise' or 'anti-clockwise', optional
        direction for circular arrow to point in, default 'clockwise
    color : str, optional
        color of circular arrow, default 'red'

    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with the circular arrow appended to it.
    """

    ## lots of difficulty in creating this since its hard to draw a semi circle and also to draw an arrow in the right place.
    ## full circle is easy to use so for now that will do
    ## for arrow, a marker was previously used to draw triangle but cant have an offset for this
    ## for arrow, tried annotatino but also cant offset from anchor point
    
    if direction in ['clockwise','anti-clockwise']:
        if direction =='clockwise':
            d = "⭮"
        else:
            d = "⭯"
    annotation = dict(x=x_sup, y=0,
            text=d,
            showarrow=False,
            yshift=0,
            font_size=26,
            font_color='red',
            )
    if row and col:
        fig.add_annotation(annotation, row=row,col=col)
    else:
        fig.add_annotation(annotation)

    return fig

##Use text rather than isinstance function in order to remove circular dependency

def draw_force(fig, load, color = 'red',row=None,col=None):
    """Draw a force (for load or reaction) on a plotly figure

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append force representation to.
    load : instance of a load class
        force to be represented on figure
    color : str, optional
        color of force representation, default 'red'

    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with the force representation appended to it.
    """
    load_type = str(load).split('(')[0]

    if load_type == 'PointTorque':
        if load[0]>0:
            direction = 'anti-clockwise'
        else:
            direction= 'clockwise'
        
        fig = draw_moment(fig,load[1],direction = direction, color = color,row=row,col=col)

    elif load_type == 'PointLoadH':
        force, x_sup = load
        angle = 0
        fig = draw_arrow(fig,angle, force, x_sup, color = color,row=row,col=col)

    elif load_type == 'PointLoadV':
        force, x_sup = load
        angle = 90
        fig = draw_arrow(fig,angle, force, x_sup, color = color,row=row,col=col)

    
    elif load_type == 'PointLoad':
        force, x_sup, angle = load
        fig = draw_arrow(fig,angle, force, x_sup, color = color,row=row,col=col)

    elif load_type == 'DistributedLoadV':
        ##need to know sign for each side.
        ##determine if has x^2 in it to see if need to write function
        ##draw each function normalised to 1. ie the max is always 1.
        ##evaluate force at left and force at right to plot
        expr, interval = load
        x0, x1 = interval
        expr = sympify(expr)
        x_vec = np.linspace(x0, x1, int(min((x1-x0) * 100 + 1, 1e4)))  ## numpy array for x positions closely spaced (allow for graphing)
        y_lam = lambdify(x, expr, "numpy")                                          ##i think lambdify is needed to let the function work with numpy
        y_vec = np.array([y_lam(t) for t in x_vec])
        largest = abs(max(y_vec, key=abs))
        y_vec = (-1) * y_vec / largest ##normalise  , use -1 to flip direction so matches arrow direction
        trace = go.Scatter(x=x_vec, y=y_vec,mode='lines',line=dict(color='darkgreen', width=1),fill='tozeroy',name='DistributedLoadV',hovertemplate="",hoverinfo="skip")
        if row and col:
            fig.add_trace(trace,row=row,col=col)
        else:
            fig.add_trace(trace)

        ##draw arrow for left force and right force
        angle = 90
        if abs(y_vec[0] / largest) > 0.02:
            fig = draw_arrow(fig,angle, -y_vec[0], x_vec[0], color = 'green', arrowlength=50* abs(y_vec[0]),row=row,col=col)
        if abs(y_vec[-1] / largest) > 0.02:
            fig = draw_arrow(fig,angle, -y_vec[-1], x_vec[-1], color = 'green', arrowlength=50* abs(y_vec[-1]),row=row,col=col)


    return fig

def draw_load_hoverlabel(fig,load,row=None,col=None):
    """Draw a load hoverlabel on a plotly figure

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append force representation to.
    load : instance of a load class
        force to be represented on figure

    Returns
    -------
    plotly figure
        plotly figure to append hoverlabel representation to.
    """


    load_type = str(load).split('(')[0]
    y_sup=0


    if load_type in ['PointLoad', 'PointLoadH', 'PointLoadV', 'PointTorque']:
        x_sup= load[1]
        color = 'red'
        meta = [load[0],load[1]]  # load, position
        
        if load_type == 'PointTorque':
            hovertemplate = 'x: %{meta[1]} m<br>Moment: %{meta[0]} kN.m'
            name = 'Point<br>Torque'
        elif load_type == 'PointLoad':
            meta.append(load[2])
            hovertemplate = 'x: %{meta[1]} m<br>Force: %{meta[0]} kN<br>Angle: %{meta[2]} deg'
            name = 'Point<br>Load'
        elif load_type == 'PointLoadV':
            hovertemplate = 'x: %{meta[1]} m<br>Force: %{meta[0]} kN<br>Direction: Vertical'
            name = 'Point<br>LoadV'
        else:
            hovertemplate = 'x: %{meta[1]} m<br>Force: %{meta[0]} kN<br>Angle: Horizontal'
            name = 'Point<br>LoadH'

        trace = go.Scatter(
            x=[x_sup], y=[y_sup],
            showlegend=False, mode="markers",
            name = name,
            meta = meta,
            marker= dict(symbol="triangle-up",size = 10, color = color),
            hovertemplate=hovertemplate,
            hoverinfo="skip",
            opacity=0
            )
        
        if row and col:
            fig.add_trace(trace,row=row, col=col)
        else:
            fig.add_trace(trace)

    else:
        expr, interval = load
        x0, x1 = interval
        expr = sympify(expr)
        x_vec = np.array([x0, x1])  ## numpy array for x positions closely spaced (allow for graphing)
        y_lam = lambdify(x, expr, "numpy")                                          ##i think lambdify is needed to let the function work with numpy
        y_vec = np.array([y_lam(t) for t in x_vec])

        name = 'Distributed<br>Load'
        color = 'green'
        y_sup=1

        meta = [x0,x1,y_vec[0],y_vec[1]]
        
        trace_1 = go.Scatter(
            x=[x_vec[0]], y=[0],
            showlegend=False, mode="markers",
            name = name,
            meta = meta,
            marker= dict(symbol="triangle-up",size = 10, color = color),
            hovertemplate = 'x: %{meta[0]} m<br>Force: %{meta[2]} kN/m',
            hoverinfo="skip",
            opacity=0
            )

        trace_2 = go.Scatter(
            x=[x_vec[1]], y=[0],
            showlegend=False, mode="markers",
            name = name,
            meta = meta,
            marker= dict(symbol="triangle-up",size = 10, color = color),
            hovertemplate = 'x: %{meta[1]} m<br>Force: %{meta[3]} kN/m',
            hoverinfo="skip",
            opacity=0
            )
        
        if row and col:
            fig.add_trace(trace_1,row=row,col=col)
            fig.add_trace(trace_2,row=row,col=col)
        else:
            fig.add_trace(trace_1)
            fig.add_trace(trace_2)

    return fig
    
def draw_reaction_hoverlabel(fig,reactions, x_sup,row=None,col=None):
    """Draw a reaction hoverlabel on a plotly figure

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append force representation to.
    load : instance of a load class
        force to be represented on figure
    x_sup : int
        The position for the hoverlabel to be anchored to i.e. the position of a support or spring.

    Returns
    -------
    plotly figure
        plotly figure to append hoverlabel representation to.
    """
    #reactions should be [x,y,m]
    ## can probably change it to get rid of x_sup notation to make more consistent 
    x_,y_,m_ = reactions
    hovertemplate = "Reactions"
    if x_:
        hovertemplate += "<br>x: %{meta[0]} kN"
    if y_:
        hovertemplate += "<br>y: %{meta[1]} kN"
    if m_:
        hovertemplate += "<br>m: %{meta[2]} kN.m"

    trace = go.Scatter(
        x=[x_sup], y=[0],
        showlegend=False, mode="markers",
        name = "Reaction",
        meta = reactions,
        marker= dict(symbol="triangle-up",size = 10, color = 'red'),
        hovertemplate=hovertemplate,
        hoverinfo="skip",
        opacity=0
    )
    if row and col:
        fig.add_trace(trace,row=row,col=col)
    else:
        fig.add_trace(trace)

    return fig

def draw_support_hoverlabel(fig,support,kx=0,ky=0,row=None,col=None):
    """Draw a reaction hoverlabel on a plotly figure

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append force representation to.
    support : Support instance
        support to be represented on figure
    kx : int, optional
        The spring stiffness of the support in the x direction, default 0
    ky : int, optional
        The spring stiffness of the support in the y direction, default 0

    Returns
    -------
    plotly figure
        plotly figure with hoverlabel appended to it.
    """
    ##This could be implemented better (hovertemplates in general could be)
    if kx == oo:
        kx = 0
    if ky == oo:
        ky = 0
    ##if ky of kx is > 0 then we are deining a spring label
    ##otherwise we are definind a support label 

    fixed = support._fixed
    x_sup = support._position
    if kx or ky:
        name = "Spring"
        color = 'orange'
        meta = [kx,ky]
        hovertemplate="x: %{x} m"
        if kx:
            hovertemplate+="<br>kx: %{meta[0]} kN/mm"
        if ky:
            hovertemplate+="<br>ky: %{meta[1]} kN/mm"
    else:
        name = "Support"
        color = 'blue'
        meta = [str(fixed)]
        hovertemplate="x: %{x} m<br>Fixed: %{meta[0]}"

    
    ##necessary for hover information, opacicity 0 so not visible otherwise
    ## symbol is arbritrary since invisible
    trace = go.Scatter(
        x=[x_sup], y=[0],
        showlegend=False, mode="markers",
        name = name,
        meta = meta,
        marker= dict(symbol="triangle-up",size = 10, color = color),
        hovertemplate=hovertemplate,
        hoverinfo="skip",
        opacity=0
    )

    if row and col:
        fig.add_trace(trace,row=row,col=col)
    else:
        fig.add_trace(trace)

    return fig

def draw_support_rollers(fig,x_sup,orientation='up',offset=1,row=None,col=None):
    """Draw an anchored group of 3 circles on a plotly figure to represent a roller shape.

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append roller shape to.
    x_sup : int
        The x position for the roller shape to be anchored to.
    orientation : 'up' or 'right, optional
        direction that the arrow faces, by default "up"
    offset : int
        offset of the rollers from support location, typically 1 or 0.6, default 1.

    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with the roller shape appended to it.
    """
    radius = 1
    if orientation in ['up','right']:

        ## shifting the position to make more aesthetic for triangle or rectangle.
        ## a triangle is wider so an offset of 1 is used.
        ## a rectangle uses an offset shorter, currently 0.6 is used
        shift = offset*-13
        
        ##set centre of circles to be drawn 
        if orientation=='up':
            centres = [(0,shift),(-4,shift),(4,shift)]
        elif orientation=='right':
            centres = [(shift,0),(shift,-4),(shift,4)]
        
        ##add 3 circle shapes at the locations specified by 'centre'
        ## setting pixel means shape is defined relative to paper space and wont be zoomed in when zoom in on beam
        ## setting anchor is the point that the shape is associated with when zooming and panning about.
        #see https://plotly.com/python/shapes/ 
        for xc,yc in centres:
            shape = dict(
                type="circle",
                xref="x", yref="y",
                x0=xc-radius, y0=yc-radius, x1=xc+radius, y1=yc+radius,
                line_color="blue",
                xsizemode='pixel',
                ysizemode='pixel',
                fillcolor='blue',
                xanchor=x_sup,
                yanchor=0
            )
            if row and col:
                fig.add_shape(shape,row=row,col=col)
            else:
                fig.add_shape(shape) 

    return fig

def draw_support_spring(fig,support,orientation="up",row=None,col=None):
    """Draw an anchored spring shape on a plotly figure.

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append roller shape to.
    support : Support instance
        support to be represented on figure
    orientation : 'up' or 'right, optional
        direction that the arrow faces, by default "up"

    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with the spring shape appended to it."""

    x_sup = support._position
    
    ## x0 and y0 initialised so that when loop through each point in the coords list will have two points to reference.
    x0,y0 =0,0

    ## reduction of 0.8 used so dont have to recalculate coords and can just scale,
    reduce = 0.8

    if orientation in ['up','right']:
        ##coords are points between lines to be created
        ##label and stiffness are defined for use as meta data to be added to the hovertemplate
        if orientation =='right':
            coords = [(5,0),(7,5),(12,-5),(14,0),(19,0)]
        else:
            coords = [(0,5),(-5,7),(5,12),(0,14),(0,19)]

        ##x1 and y1 are the ends of the line to be created
        for x1,y1 in coords:
            x1,y1 = x1*reduce,y1*reduce

            ##multiple lines added but reference must always be to the same xanchor
            shape = dict(
                type="line",
                xref="x", yref="y",
                x0=x0, y0=y0, x1=x1, y1=y1,
                line_color="orange",
                line_width=2,
                xsizemode='pixel',
                ysizemode='pixel',
                xanchor=x_sup,
                yanchor=0
            )
            if row and col:
                fig.add_shape(shape,row=row,col=col)
            else:
                fig.add_shape(shape)

            ##set end point to be start point for the next line
            x0,y0 = x1,y1

    return fig

def draw_support(fig,support,row=None,col=None):
    """Draw a support on a plotly figure.

    Parameters
    ----------
    fig : plotly figure
        plotly figure to append roller shape to.
    support : Support instance
        support to be represented on figure

    Returns
    -------
    plotly figure
        Returns the plotly figure passed into function with a support drawn."""

    ## grab values from support instance
    x_sup = support._position
    fixed = support._fixed
    DOF = support._DOF

    ##DOF has 1 for partial restraint and fixed has 1 for full restraint. They are only different if a spring support exists
    springx = DOF[0]-fixed[0] 
    springy = DOF[1]-fixed[1]

    ## run through all possible cases for supports and draw the applicable shapes.
    ##Note: runs through the values in fixed not DOF so as to not represent the spring more than once (helps with clarity)
    if fixed == [0,0,0]:
        fig = fig
    else:
        fig = draw_support_hoverlabel(fig,support,row=row,col=col)
    
        if fixed == [0,0,1]:
            fig = draw_moment(fig,x_sup=support._position,direction='anti-clockwise',color='blue',row=row,col=col)

        elif fixed == [0,1,0]:
            fig = draw_support_rollers(fig,x_sup=support._position,orientation='up',offset=1,row=row,col=col)
            fig = draw_support_triangle(fig,x_sup=support._position,orientation='up',row=row,col=col)

        elif fixed == [1,0,0]:
            fig = draw_support_rollers(fig,x_sup=support._position,orientation='right',offset=1,row=row,col=col)
            fig = draw_support_triangle(fig,x_sup=support._position,orientation='right',row=row,col=col)

        elif fixed == [0,1,1]:
            fig = draw_support_rollers(fig,x_sup=support._position,orientation='up',offset=0.6,row=row,col=col)
            fig = draw_support_rectangle(fig,x_sup=support._position,orientation='up',row=row,col=col)

        elif fixed == [1,0,1]:
            fig = draw_support_rollers(fig,x_sup=support._position,orientation='right',offset=0.6,row=row,col=col)
            fig = draw_support_rectangle(fig,x_sup=support._position,orientation='right',row=row,col=col)
        elif fixed == [1,1,0]:
            fig = draw_support_triangle(fig,x_sup=support._position,orientation='up',row=row,col=col)
        elif fixed == [1,1,1]:
            fig = draw_support_rectangle(fig,x_sup=support._position,orientation='right',row=row,col=col)

        else:
            raise ValueError(f"{fixed} does not match the expected support fixed for support at {x_sup}")
        
    ##if springx then draw a spring with right orientation (value for orientation would be better written as 'x' but wanted to maintain convention used)
    if springx:
        fig = draw_support_spring(fig,support,orientation="right",row=row,col=col)

    ##if springy then draw a spring with up orientation
    if springy:
        fig = draw_support_spring(fig,support,orientation="up",row=row,col=col)

    ##draw hover lable for springs
    if springx or springy:
        fig = draw_support_hoverlabel(fig,support,kx=support._stiffness[0], ky=support._stiffness[1],row=row,col=col)

    return fig
