import sys
import os
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table
from dash_table.Format import Format, Scheme, Sign, Symbol
from indeterminatebeam.indeterminatebeam import (
    Beam, Support, PointLoad, PointTorque, DistributedLoadV, TrapezoidalLoad
)
from datetime import datetime
import time

# the style arguments for the sidebar.
SIDEBAR_STYLE = {
    'position': 'fixed',
    'top': 0,
    'left': 0,
    'bottom': 0,
    'width': '20%',
    'padding': '40px 40px',
    'background-color': '#f8f9fa'
}

# the style arguments for the main content page.
CONTENT_STYLE = {
    'margin-left': '25%',
    'margin-right': '5%',
    'padding': '20px 10p'
}

TEXT_STYLE = {
    'textAlign': 'center',
    'color': '#191970'
}

CARD_TEXT_STYLE = {
    'textAlign': 'center',
    'color': '#0074D9'
}

# side bar markdown text
about = dcc.Markdown('''

This webpage is a graphical user interface (GUI) for the opensource \
`IndeterminateBeam` Python package created using Dash.

For more, you can view:

* The Python package [here](
    https://github.com/JesseBonanno/IndeterminateBeam)
* The package documentation [here](
    https://indeterminatebeam.readthedocs.io/en/main/?badge=main)
* The sign conventions used [here](
    https://indeterminatebeam.readthedocs.io/en/main/theory.html#sign-convention)
* The Python based Jupyter Notebook examples [here](
    https://colab.research.google.com/github/JesseBonanno/IndeterminateBeam/blob/main/indeterminatebeam/simple_demo.ipynb)
* The JOSE article concerning this package [here](
    https://github.com/JesseBonanno/IndeterminateBeam/blob/main/paper.md)

Note: As the Python package calculations are purely analytical calculation \
times can be relatively slow. Each distributed load generally adds \
around 4 seconds to the calculation time.
''')

# the content for the sidebar
sidebar_content = html.Div(
    about
)


sidebar = html.Div(
    [
        html.H2('About', style=TEXT_STYLE),
        html.Hr(),
        sidebar_content
    ],
    style=SIDEBAR_STYLE,
)


# Properties for Beam Tab

beam_table_data = {
    'Length': {
        'init': 5,
        'units': ' m',
        'type': 'numeric'
    },
    "Young's Modulus (MPa)": {
        'init': 2 * 10**5,
        'units': ' MPa',
        'type': 'numeric'
    },
    "Second Moment of Area (mm4)": {
        'init': 9.05 * 10**6,
        'units': ' mm4',
        'type': 'numeric'
    },
    "Cross-Sectional Area (mm2)": {
        'init': 2300,
        'units': ' mm2',
        'type': 'numeric'
    },
}

beam_table_init = {k: v['init'] for k, v in beam_table_data.items()}

beam_table = dash_table.DataTable(
    id='beam-table',
    columns=[{
        'name': d,
        'id': d,
        'deletable': False,
        'renamable': False,
        'type': beam_table_data[d]['type'],
        'format': Format(
            symbol=Symbol.yes,
            symbol_suffix=beam_table_data[d]['units'])
    } for d in beam_table_data.keys()],
    data=[beam_table_init],
    editable=True,
    row_deletable=False,
)


beam_content = dbc.Card(
    dbc.CardBody(
        [
            beam_table,
        ]
    ),
    className="mt-3",
)

# Properties for Support Tab
# Just do as a table but let inputs be
# R - Restraint, F- Free, or number for spring, Spring not an option for m.

support_table_data = {
    'Coordinate (m)': {
        'init': 0,
        'units': ' m',
        'type': 'numeric'
    },
    "X": {
        'init': 'R',
        'units': ' kN/mm',
        'type': 'any'
    },
    "Y": {
        'init': 'R',
        'units': ' kN/mm',
        'type': 'any'
    },
    "M": {
        'init': 'R',
        'units': ' kN/mm',
        'type': 'any',
    }
}


support_table_init = {k: v['init'] for k, v in support_table_data.items()}

support_table = dash_table.DataTable(
    id='support-table',
    columns=[{
        'name': d,
        'id': d,
        'deletable': False,
        'renamable': False,
        'type': support_table_data[d]['type'],
        'format': Format(
            symbol=Symbol.yes,
            symbol_suffix=support_table_data[d]['units'])
    } for d in support_table_data.keys()],
    data=[support_table_init],
    editable=True,
    row_deletable=True,
)

support_content = dbc.Card(
    dbc.CardBody(
        [
            support_table,
            html.Br(),
            html.Button('Add Support', id='support-rows-button', n_clicks=0),

        ]
    ),
    className="mt-3",
)

# Properties for point_load Tab

point_load_table_data = {
    'Coordinate (m)': {
        'init': 0,
        'units': ' m',
        'type': 'numeric'
    },
    "Force (kN)": {
        'init': 0,
        'units': ' kN',
        'type': 'numeric'
    },
    "Angle (deg)": {
        'init': 90,
        'units': '',
        'type': 'numeric'
    },
}

point_load_table_init = {k: v['init']
                         for k, v in point_load_table_data.items()}

point_load_table = dash_table.DataTable(
    id='point-load-table',
    columns=[{
        'name': d,
        'id': d,
        'deletable': False,
        'renamable': False,
        'type': point_load_table_data[d]['type'],
        'format': Format(
            symbol=Symbol.yes,
            symbol_suffix=point_load_table_data[d]['units'])
    } for d in point_load_table_data.keys()],
    data=[point_load_table_init],
    editable=True,
    row_deletable=True,
)

point_load_content = dbc.Card(
    dbc.CardBody(
        [
            point_load_table,
            html.Br(),
            html.Button(
                'Add Point Load',
                id='point-load-rows-button',
                n_clicks=0),
        ]
    ),
    className="mt-3",
)

# Properties for point_torque Tab
point_torque_table_data = {
    'Coordinate (m)': {
        'init': 0,
        'units': ' m',
        'type': 'numeric'
    },
    "Torque (kN.m)": {
        'init': 0,
        'units': ' kN',
        'type': 'numeric'
    },
}

point_torque_table_init = {k: v['init']
                           for k, v in point_torque_table_data.items()}

point_torque_table = dash_table.DataTable(
    id='point-torque-table',
    columns=[{
        'name': d,
        'id': d,
        'deletable': False,
        'renamable': False,
        'type': point_torque_table_data[d]['type'],
        'format': Format(
            symbol=Symbol.yes,
            symbol_suffix=point_torque_table_data[d]['units'])
    } for d in point_torque_table_data.keys()],
    data=[point_torque_table_init],
    editable=True,
    row_deletable=True,
)

point_torque_content = dbc.Card(
    dbc.CardBody(
        [
            point_torque_table,
            html.Br(),
            html.Button(
                'Add Point Torque',
                id='point-torque-rows-button',
                n_clicks=0),
        ]
    ),
    className="mt-3",
)

# Properties for distributed_load Tab

distributed_load_table_data = {
    'Start x_coordinate (m)': {
        'init': 0,
        'units': ' m',
        'type': 'numeric'
    },
    'End x_coordinate (m)': {
        'init': 0,
        'units': ' m',
        'type': 'numeric'
    },
    'Start Load (kN/m)': {
        'init': 0,
        'units': ' kN/m',
        'type': 'numeric'
    },
    'End Load (kN/m)': {
        'init': 0,
        'units': ' kN/m',
        'type': 'numeric'
    },

}

distributed_load_table_init = {k: v['init']
                               for k, v in distributed_load_table_data.items()}

distributed_load_table = dash_table.DataTable(
    id='distributed-load-table',
    columns=[{
        'name': d,
        'id': d,
        'deletable': False,
        'renamable': False,
        'type': distributed_load_table_data[d]['type'],
        'format': Format(
            symbol=Symbol.yes,
            symbol_suffix=distributed_load_table_data[d]['units'])
    } for d in distributed_load_table_data.keys()],
    data=[distributed_load_table_init],
    editable=True,
    row_deletable=True,
)

distributed_load_content = dbc.Card(
    dbc.CardBody(
        [
            distributed_load_table,
            html.Br(),
            html.Button(
                'Add Distributed Load',
                id='distributed-load-rows-button',
                n_clicks=0),

        ]
    ),
    className="mt-3",
)

# Properties for query tab
query_table_data = {
    'Query coordinate (m)': 0,
}

query_table = dash_table.DataTable(
    id='query-table',
    columns=[{
        'name': i,
        'id': i,
        'deletable': False,
        'renamable': False,
        'type': 'numeric',
        'format': Format(
                symbol=Symbol.yes,
                symbol_suffix=' m')
    } for i in query_table_data.keys()],
    data=[],
    editable=True,
    row_deletable=True
)

query_content = dbc.Card(
    dbc.CardBody(
        [
            query_table,
            html.Br(),
            html.Button('Add Query', id='query-rows-button', n_clicks=0),

        ]
    ),
    className="mt-3",
)

# Assemble different input tabs
tabs = dbc.Tabs(
    [
        dbc.Tab(beam_content, label="Beam"),
        dbc.Tab(support_content, label="Supports"),
        dbc.Tab(point_load_content, label="Point Loads"),
        dbc.Tab(point_torque_content, label="Point Torques"),
        dbc.Tab(distributed_load_content, label="Distributed Load"),
        dbc.Tab(query_content, label="Query")
    ]
)

# Create a submit button
submit_button = dbc.Button(
    id='submit_button',
    n_clicks=0,
    children='Submit',
    color='primary',
    block=True
)

# Create a status bar/Alert
calc_status = dbc.Alert(
    children="No analysis has been run.",
    id="alert-fade",
    dismissable=True,
    is_open=True,
    color='danger',
)

# Assemble main application content
content_first_row = dbc.Row(
    [
        dbc.Col(
            [
                dbc.Card(
                    dbc.Spinner(dcc.Graph(id='graph_1')),
                ),
                html.Br(),
                tabs,
                html.Br(),
                submit_button

            ],
            md=6
        ),

        dbc.Col(
            dbc.Card(
                dbc.Spinner(dcc.Graph(id='graph_2'))
            ),
            md=6
        )

    ]
)


content = html.Div(
    [
        html.H2('Beam Calculator Proof of Concept', style=TEXT_STYLE),
        html.Hr(),
        calc_status,
        content_first_row,
    ],
    style=CONTENT_STYLE
)

# Initialise app
app = dash.Dash(__name__,external_stylesheets=[dbc.themes.MINTY])
server = app.server
app.layout = html.Div([sidebar, content])

# Main calculation, creates beam and analyses it.
# Returns plots and/or calculation status.
@app.callback(
    [Output('graph_1', 'figure'), Output('graph_2', 'figure'),
     Output('alert-fade', 'color'), Output('alert-fade', 'children')],
    [Input('submit_button', 'n_clicks')],
    [State('beam-table', 'data'), State('point-load-table', 'data'),
     State('point-torque-table', 'data'), State('query-table', 'data'),
     State('distributed-load-table', 'data'), State('support-table', 'data'),
     State('graph_1', 'figure'), State('graph_2', 'figure')])
def analyse_beam(click, beams, point_loads, point_torques, querys,
                 distributed_loads, supports, graph_1, graph_2):
    try:
        t1 = time.perf_counter()

        for row in beams:
            beam = Beam(*(float(a) for a in row.values()))

        if supports:
            for row in supports:
                if row['X'] in ['r', 'R']:
                    DOF_x = 1
                    kx = 0
                elif row['X'] in ['f', 'F']:
                    DOF_x = 0
                    kx = 0
                elif float(row['X']) > 0:
                    DOF_x = 0
                    kx = float(row['X'])
                else:
                    raise ValueError(
                        'input incorrect for x restraint of support')

                if row['Y'] in ['r', 'R']:
                    DOF_y = 1
                    ky = 0
                elif row['Y'] in ['f', 'F']:
                    DOF_y = 0
                    ky = 0
                elif float(row['Y']) > 0:
                    DOF_y = 0
                    ky = float(row['Y'])
                else:
                    raise ValueError(
                        'input incorrect for y restraint of support')

                if row['M'] in ['r', 'R']:
                    DOF_m = 1
                elif row['M'] in ['f', 'F']:
                    DOF_m = 0
                else:
                    raise ValueError(
                        'input incorrect for m restraint of support')

                beam.add_supports(Support(
                    float(row['Coordinate (m)']),
                    (
                        DOF_x,
                        DOF_y,
                        DOF_m
                    ),
                    ky=ky,
                    kx=kx,
                )
                )
        # TO DO: add capitals
        if point_loads:
            for row in point_loads:
                beam.add_loads(PointLoad(
                    float(row['Force (kN)']),
                    float(row['Coordinate (m)']),
                    float(row['Angle (deg)'])
                )
                )

        if point_torques:
            for row in point_torques:
                beam.add_loads(PointTorque(
                    float(row['Torque (kN.m)']),
                    float(row['Coordinate (m)']),
                )
                )

        if distributed_loads:
            for row in distributed_loads:
                if abs(float(row['Start x_coordinate (m)'])) > 0 or \
                        abs(float(row['End x_coordinate (m)'])) > 0:
                    beam.add_loads(TrapezoidalLoad(
                        force=(
                            float(row['Start Load (kN/m)']),
                            float(row['End Load (kN/m)'])
                        ),
                        span=(
                            float(row['Start x_coordinate (m)']),
                            float(row['End x_coordinate (m)'])
                        ))
                    )
        beam.analyse()

        if querys:
            for row in querys:
                beam.add_query_points(
                    float(row['Query coordinate (m)']),
                )

        graph_1 = beam.plot_beam_external()

        graph_2 = beam.plot_shear_force()

        t2 = time.perf_counter()
        t = t2 - t1
        dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        color = "success"
        message = f"calculation completed in {t:.2f} seconds, at {dt}"
    except BaseException:
        color = "danger"
        e = sys.exc_info()[1]
        message = f"Error with calculation. Please check inputs. \
            The following error was observed: {e}"
    if click == 0:
        color = "danger"
        message = "No analysis has been run."

    if type(graph_1)!=dict:
        graph_1 = graph_1.to_dict()
    if type(graph_2)!=dict:
        graph_2 = graph_2.to_dict()

    return graph_1, graph_2, color, message


# Add button to add row for supports
@app.callback(
    Output('support-table', 'data'),
    Input('support-rows-button', 'n_clicks'),
    State('support-table', 'data'),
    State('support-table', 'columns'))
def add_row2(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append(support_table_init)
    return rows

# Add button to add row for point loads
@app.callback(
    Output('point-load-table', 'data'),
    Input('point-load-rows-button', 'n_clicks'),
    State('point-load-table', 'data'),
    State('point-load-table', 'columns'))
def add_row3(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append(point_load_table_init)
    return rows

# Add button to add row for point torques
@app.callback(
    Output('point-torque-table', 'data'),
    Input('point-torque-rows-button', 'n_clicks'),
    State('point-torque-table', 'data'),
    State('point-torque-table', 'columns'))
def add_row4(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append(point_torque_table_init)
    return rows

# Add button to add row for distributed loads
@app.callback(
    Output('distributed-load-table', 'data'),
    Input('distributed-load-rows-button', 'n_clicks'),
    State('distributed-load-table', 'data'),
    State('distributed-load-table', 'columns'))
def add_row5(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append(distributed_load_table_init)
    return rows

# Add button to add row for querys
@app.callback(
    Output('query-table', 'data'),
    Input('query-rows-button', 'n_clicks'),
    State('query-table', 'data'),
    State('query-table', 'columns'))
def add_row6(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append(query_table_data)
    return rows


if __name__ == '__main__':
    app.run_server()
