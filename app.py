import sys
import os
import json
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table
from dash_table.Format import Format, Scheme, Sign, Symbol
from indeterminatebeam.indeterminatebeam import (
    Beam, Support
)
from indeterminatebeam.loading import (
    PointLoad,
    TrapezoidalLoad,
    PointTorque
)
from datetime import datetime
import time
from indeterminatebeam.version import __version__
from dash_extensions import Download
from dash.exceptions import PreventUpdate
from plotly.io import to_html


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
about = dcc.Markdown(f'''

This webpage is a graphical user interface (GUI) for the opensource \
`IndeterminateBeam` Python package created using Dash.

For more, you can view the following:

* [![Python Package](https://img.shields.io/badge/version-{__version__}-blue.svg)](https://github.com/JesseBonanno/IndeterminateBeam)
   The Python package
* [![Package Documentation](https://readthedocs.org/projects/indeterminatebeam/badge/?version=main)](https://indeterminatebeam.readthedocs.io/en/main/?badge=main)
   The package documentation
* [![Sign Conventions](https://readthedocs.org/projects/indeterminatebeam/badge/?version=main)](https://indeterminatebeam.readthedocs.io/en/main/theory.html#sign-convention)
   The sign conventions used
* [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JesseBonanno/IndeterminateBeam/blob/main/indeterminatebeam/simple_demo.ipynb)
   The Python based Jupyter Notebook examples
* [![Article](https://img.shields.io/badge/Article-Submitted-orange.svg)](https://github.com/JesseBonanno/IndeterminateBeam/blob/main/paper.md)
   The JOSE article concerning this package

Note: As the Python package calculations are purely analytical calculation \
times can be relatively slow.
''')

# the content for the sidebar
sidebar_content = html.Div(
    [
        about
    ]
)


sidebar = html.Div(
    [
        html.H2('About', style=TEXT_STYLE),
        html.Hr(),
        sidebar_content
    ],
    style=SIDEBAR_STYLE,
)

# Copyright content for footer
copyright_ = dbc.Row(
    [
        dbc.Col(
            dcc.Markdown("[![License](https://img.shields.io/badge/license-MIT-lightgreen.svg)](https://github.com/JesseBonanno/IndeterminateBeam/blob/main/LICENSE.txt)")),
        dbc.Col(
            dcc.Markdown("Copyright (c) 2020, Jesse Bonanno")),
        dbc.Col(
            dcc.Markdown("Contact: JesseBonanno@gmail.com")),
    ])


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
    persistence=True,
    persistence_type='session'
)

beam_instructions = dcc.Markdown('''

            ###### **Instructions:**

            1. Specify the length of the beam
            2. Specify the beam sectional properties as indicated for:
               * Young's Modulus (E)
               * Second Moment of Area (I)
               * Cross-sectional Area (A)  

            Note: E and I will only affect the deflection unless a spring in the y direction is specified  
            in which case they will also affect the load distribution. Where a spring in the x direction  
            is specified E and A will affect the load distribution for the horizontal loads only.   
            ''')

beam_content = dbc.Card(
    dbc.CardBody(
        [
            beam_table,
            html.Br(),
            dbc.Collapse(
                dbc.Card(dbc.CardBody(beam_instructions)),
                id="beam_instructions",
            ),
        ]
    ),
    className="mt-3",
)

# Properties for (Advanced) Support Tab
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

support_instructions = dcc.Markdown('''

            ###### **Instructions:**

            1. Specify the coodinate location of the support
            2. For each direction specify one of the following:
               * f or F - Indicates a free support
               * r or R - Indicates a rigid support
               * n - Indicates a spring stiffness of n kN /mm   
                 (where n is (generally) a positive number)

            ''')

support_content = dbc.Card(
    dbc.CardBody(
        [
            support_table,
            html.Br(),
            html.Button('Add Support', id='support-rows-button', n_clicks=0),
            dbc.Collapse(
                [
                    html.Br(),
                    dbc.Card(dbc.CardBody(support_instructions))
                ],
                id="support_instructions",
            ),
        ]
    ),
    className="mt-3",
)

# Basic support

basic_support_table_data = {
    'Coordinate (m)': {
        'init': 0,
        'type': 'numeric',
        'presentation': 'input'
    },
    "Support": {
        'init': 'Fixed',
        'type': 'any',
        'presentation': 'dropdown'
    }
}


basic_support_table_init = {k: v['init']
                            for k, v in basic_support_table_data.items()}

basic_support_table = dash_table.DataTable(
    id='basic-support-table',
    columns=[{
        'name': d,
        'id': d,
        'deletable': False,
        'renamable': False,
        'type': basic_support_table_data[d]['type'],
        'presentation': basic_support_table_data[d]['presentation'],
    } for d in basic_support_table_data.keys()],
    data=[basic_support_table_init],
    editable=True,
    row_deletable=True,
    dropdown={
        "Support": {
            'options': [
                {'label': 'Fixed', 'value': 'Fixed'},
                {'label': 'Pinned', 'value': 'Pinned'},
                {'label': 'Roller', 'value': 'Roller'},
            ]
        }
    },
    # dropdowns arent visible unless you add the code below.
    # solution taken from https://github.com/plotly/dash-table/issues/221 
    # - reesehopkins commented on 29 Sep 2020
    css=[{"selector": ".Select-menu-outer", "rule": "display: block !important"}],
)

basic_support_instructions = dcc.Markdown('''

            ###### **Instructions:**

            1. Specify the coodinate location of the support  
            2. For each direction specify the conventional 
               support type from the dropdown.  

            ''')

basic_support_content = dbc.Card(
    dbc.CardBody(
        [
            basic_support_table,
            html.Br(),
            html.Button(
                'Add Support',
                id='basic-support-rows-button',
                n_clicks=0),
            dbc.Collapse(
                [
                    html.Br(),
                    dbc.Card(
                        dbc.CardBody(basic_support_instructions))],
                id="basic_support_instructions",
            ),
        ]),
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

point_load_instructions = dcc.Markdown('''

            ###### **Instructions:**

            1. Specify the coodinate location of the point load.  
            2. Specify the force applied in kN.
            3. Specify the load angle where:  
               * A positive force with an angle of 0 points horizontally to the right.  
               * A positive force with an angle of 90 points vertically in the   
                 positive y direction chosen in the options tab (default downwards).  

            ''')

point_load_content = dbc.Card(
    dbc.CardBody(
        [
            point_load_table,
            html.Br(),
            html.Button(
                'Add Point Load',
                id='point-load-rows-button',
                n_clicks=0),
            dbc.Collapse(
                [
                    html.Br(),
                    dbc.Card(dbc.CardBody(point_load_instructions))
                ],
                id="point_load_instructions",
            ),
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

point_torque_instructions = dcc.Markdown('''

            ###### **Instructions:**

            1. Specify the coodinate location of the point torque.  
            2. Specify the moment applied in kN.m.  

            Note: A positive moment indicates an anti-clockwise moment direction.  

            ''')

point_torque_content = dbc.Card(
    dbc.CardBody(
        [
            point_torque_table,
            html.Br(),
            html.Button(
                'Add Point Torque',
                id='point-torque-rows-button',
                n_clicks=0),
            dbc.Collapse(
                [
                    html.Br(),
                    dbc.Card(dbc.CardBody(point_torque_instructions))
                ],
                id="point_torque_instructions",
            ),
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

distributed_load_instructions = dcc.Markdown('''

            ###### **Instructions:**

            1. Specify the start and end locations of the distributed load.  
            2. Specify the start and end loads in kN/m.  

            Note: A positive load acts in the positive y direction chosen  
            in the options tab (default downwards).

            ''')

distributed_load_content = dbc.Card(
    dbc.CardBody(
        [
            distributed_load_table,
            html.Br(),
            html.Button(
                'Add Distributed Load',
                id='distributed-load-rows-button',
                n_clicks=0),
            html.Br(),
            dbc.Collapse(
                [
                    html.Br(),
                    dbc.Card(dbc.CardBody(distributed_load_instructions))
                ],
                id="distributed_load_instructions",
            ),

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

query_instructions = dcc.Markdown('''

            ###### **Instructions:**

            1. Specify a point of interest to have values annotated on graph.

            ''')

query_content = dbc.Card(
    dbc.CardBody(
        [
            query_table,
            html.Br(),
            html.Button('Add Query', id='query-rows-button', n_clicks=0),
            dbc.Collapse(
                [
                    html.Br(),
                    dbc.Card(dbc.CardBody(query_instructions))
                ],
                id="query_instructions",
            ),

        ]
    ),
    className="mt-3",
)

# Properties for results section
results_columns = [
    {"name": "", "id": "val"},
    {"name": 'Normal Force (kN)', "id": "NF"},
    {"name": 'Shear Force (kN)', "id": "SF"},
    {"name": 'Bending Moment (kN.m)', "id": "BM"},
    {"name": 'Deflection (mm)', "id": "D"},
]


results_data = [
    {'val': 'Max', 'NF': 0, 'SF': 0, 'BM': 0, 'D': 0},
    {'val': 'Min', 'NF': 0, 'SF': 0, 'BM': 0, 'D': 0}
]


results_table = dash_table.DataTable(
    id='results-table',
    columns=results_columns,
    data=results_data,
    merge_duplicate_headers=True,
    editable=False,
    row_deletable=False,
    style_cell={'textAlign': 'center'},
)

results_content = dbc.Collapse(
    [
        dbc.Card(
            dbc.CardBody(
                [
                    results_table,
                ]
            ),
            className="mt-3",
        ),
    ],
    id='results-collapse'
)

# Options
option_instructions = dcc.Markdown('''

            ###### **Instructions:**

            Toggle options as desired.

            1. Results Table:
               - Choose to show or hide the table that summarises the maximum  
               and minimum effects determined over the beam  
            2. Support Input:
               - Choose mode to use for support input where:  
                  - Basic: Provides a dropdown for conventional supports  
                  - Advanced: Allows for custom support configurations, as well  
                  as spring supports  
            3. Positive y direction:
               - Choose the positive y direction.  
               - Note: The python package conventionally takes `UP` as being the  
               direction for positive forces, as indicated in the package   
               documentaion. Due to popular request the option to change the  
               positive direction for y forces to be downwards has been allowed.  
               This is actually achieved by reversing the angle direction  
               of loading behind the scenes, (multiplying by negative 1)  
               which can be revealed by hoverlabels.  
            4. Data points:
               - Number of increments used for plotting graphs, higher number  
               results in longer calculation speeds.
            ''')

option_support_input = dbc.FormGroup(
    [
        dbc.Label("Support Mode", html_for="option_support_input", width=3),
        dbc.Col(
            dbc.RadioItems(
                id="option_support_input",
                options=[
                    {'label': 'Basic', 'value': 'basic'},
                    {'label': 'Advanced', 'value': 'advanced'},
                ],
                value='basic',
                inline=True,
            ),
            width=8,
        ),
    ],
    row=True,
)


option_positive_direction_y = dbc.FormGroup(
    [
        dbc.Label("Positive y direction", html_for='option_positive_direction_y', width=3),
        dbc.Col(
            dbc.RadioItems(
                id='option_positive_direction_y',
                options=[
                    {'label': 'Up', 'value': 'up'},
                    {'label': 'Down', 'value': 'down'},
                ],
                value='down',
                inline=True,
            ),
            width=8,
        ),
    ],
    row=True,
)


option_result_table = dbc.FormGroup(
    [
        dbc.Label("Result Table", html_for="option-result-table", width=3),
        dbc.Col(
            dbc.RadioItems(
                id="option-result-table",
                options=[
                    {'label': 'Hide', 'value': 'hide'},
                    {'label': 'Show', 'value': 'show'},
                ],
                value='hide',
                inline=True,
            ),
            width=8,
        ),
    ],
    row=True,
)

option_data_point = dbc.FormGroup(
    [
        dbc.Label("Graph Data Points", html_for="option_data_points", width=3),
        dbc.Col(
            dcc.Slider(
                id='option_data_points',
                min=100,
                max=1000,
                value=100,
                step=100,
                marks={
                    100: {'label': '100'},
                    500: {'label': '500'},
                    1000: {'label': '1000'}
                },
                included=True
            ),
            width=8,
        ),
    ],
    row=True,
)

option_combined = dbc.Form([
    option_result_table,
    option_support_input,
    option_positive_direction_y,
    option_data_point,

])

option_content = dbc.Card(
    dbc.CardBody(
        [
            option_combined,
            html.Br(),
            dbc.Collapse(
                [
                    html.Br(),
                    dbc.Card(dbc.CardBody(option_instructions))
                ],
                id="option_instructions",
            ),

        ]
    ),
    className="mt-3",
)

# Assemble different input tabs
tabs = dbc.Tabs(
    [
        dbc.Tab(beam_content, label="Beam"),
        dbc.Tab(
            [
                dbc.Collapse(
                    support_content,
                    id='advanced-support'
                ),
                dbc.Collapse(
                    basic_support_content,
                    id='basic-support'
                ),
            ],
            label="Supports",
        ),
        dbc.Tab(point_load_content, label="Point Loads"),
        dbc.Tab(point_torque_content, label="Point Torques"),
        dbc.Tab(distributed_load_content, label="Distributed Load"),
        dbc.Tab(query_content, label="Query"),
        dbc.Tab(option_content, label='Options')
    ]
)

# Create a submit button
submit_button = dbc.Button(
    id='submit_button',
    n_clicks=0,
    children='Analyse',
    color='primary',
    block=True,
    disabled=False,
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
content_first_row = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Row(
                        dbc.Col(
                            [
                                dbc.Card(
                                    dbc.Spinner(dcc.Graph(id='graph_1')),
                                ),
                                html.Br(),
                                tabs,
                                html.Br(),
                            ],
                            width=12,
                        )
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(
                                    "Toggle Instructions",
                                    id="instruction-button",
                                    className="mb-3",
                                    color="info",
                                    n_clicks=0,
                                    block=True,
                                ),
                                width=4
                            ),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        "Generate Report",
                                        id="report-button",
                                        className="mb-3",
                                        color="info",
                                        n_clicks=0,
                                        block=True,
                                    ),
                                    Download(id='report'),
                                ],
                                width=4
                            ),
                            dbc.Col(
                                dbc.Spinner(submit_button),
                                width=4
                            )
                        ]
                    ),
                    html.Br(),
                ],
                width={"size": 5.5, "offset": 0},
                style={'padding': '5px'}
            ),
            dbc.Col(
                [
                    dbc.Card(
                        dbc.Spinner(dcc.Graph(id='graph_2'))
                    ),
                    results_content,
                ],
                width={"size": 5.8, "offset": 0},
                style={'padding': '5px'}
            )
        ]
    )
)


content = html.Div(
    [
        html.H2('Beam Calculator', style=TEXT_STYLE),
        html.Hr(),
        calc_status,
        content_first_row,
        html.Div(id='hidden-input', style=dict(display='none')),
        html.Hr(),
        copyright_
    ],
    style=CONTENT_STYLE
)

# Initialise app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])
server = app.server
app.layout = html.Div([sidebar, content])

# options - support mode


@app.callback(
    [Output('advanced-support', 'is_open'),
     Output('basic-support', 'is_open')],
    Input('option_support_input', 'value')
)
def support_setup(mode):
    if mode == 'basic':
        return False, True
    else:
        return True, False

# option - result data (to be query data in future really)


@app.callback(
    Output('results-collapse', 'is_open'),
    Input('option-result-table', 'value')
)
def results_setup(mode):
    if mode == 'hide':
        return False
    else:
        return True

# option - positive y direction

# Main callback - assembles entire beam and analyses base on inputs.


@app.callback(
    [Output('graph_1', 'figure'), Output('graph_2', 'figure'),
     Output('alert-fade', 'color'), Output('alert-fade', 'children'),
     Output('alert-fade', 'is_open'), Output('results-table', 'data'),
     Output('hidden-input', 'children'), Output('submit_button', 'disabled')],
    [Input('submit_button', 'n_clicks')],
    [State('beam-table', 'data'), State('point-load-table', 'data'),
     State('point-torque-table', 'data'), State('query-table', 'data'),
     State('distributed-load-table', 'data'), State('support-table', 'data'),
     State('basic-support-table', 'data'),
     State('graph_1', 'figure'), State('graph_2', 'figure'),
     State('hidden-input', 'children'), State('advanced-support', 'is_open'),
     State('option_positive_direction_y', 'value'),
     State('option_data_points', 'value')])
def analyse_beam(
        click,
        beams,
        point_loads,
        point_torques,
        querys,
        distributed_loads,
        advanced_supports,
        basic_supports,
        graph_1,
        graph_2,
        prev_input,
        advanced_support_open,
        positive_y_direction,
        data_points):

    t1 = time.perf_counter()

    if advanced_support_open:
        supports = advanced_supports
    else:
        for i, s in enumerate(basic_supports):
            sup = s.pop('Support')
            if sup == 'Fixed':
                s['X'] = 'R'
                s['Y'] = 'R'
                s['M'] = 'R'
            elif sup == 'Pinned':
                s['X'] = 'R'
                s['Y'] = 'R'
                s['M'] = 'F'
            elif sup == 'Roller':
                s['X'] = 'F'
                s['Y'] = 'R'
                s['M'] = 'F'
            basic_supports[i] = s
        supports = basic_supports

    input_json = json.dumps(
        {
            'beam': beams,
            'supports': supports,
            'point_loads': point_loads,
            'point_torques': point_torques,
            'distributed_loads': distributed_loads,
            'querys': querys,
            'y': positive_y_direction,
            'data_points': data_points,
        }
    )

    if input_json == prev_input:
        raise PreventUpdate

    try:

        if positive_y_direction == 'up':
            d_ = 1
        else:
            d_ = -1

        for row in beams:
            beam = Beam(*(float(a) for a in row.values()))

        beam._DATA_POINTS = data_points

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

                beam.add_supports(
                    Support(
                        float(row['Coordinate (m)']),
                        (
                            DOF_x,
                            DOF_y,
                            DOF_m
                        ),
                        ky=ky,
                        kx=kx,
                    ),
                )
        # TO DO: add capitals

        if distributed_loads:
            for row in distributed_loads:
                beam.add_loads(
                    TrapezoidalLoad(
                        force=(
                            float(row['Start Load (kN/m)']),
                            float(row['End Load (kN/m)'])
                        ),
                        span=(
                            float(row['Start x_coordinate (m)']),
                            float(row['End x_coordinate (m)'])
                        ),
                        angle=(d_ * 90)
                    )
                )

        if point_loads:
            for row in point_loads:
                beam.add_loads(
                    PointLoad(
                        float(row['Force (kN)']),
                        float(row['Coordinate (m)']),
                        d_ * float(row['Angle (deg)'])
                    )
                )

        if point_torques:
            for row in point_torques:
                beam.add_loads(
                    PointTorque(
                        float(row['Torque (kN.m)']),
                        float(row['Coordinate (m)']),
                    )
                )

        beam.analyse()

        if querys:
            for row in querys:
                beam.add_query_points(
                    float(row['Query coordinate (m)']),
                )

        graph_1 = beam.plot_beam_external()

        graph_2 = beam.plot_beam_internal()

        # results data is actually adding to the calc time significantly.
        # Might be worth trying to find a more efficient method,
        # for example getting max, min and x values all in one go could mean
        # dont need to generate vectors multiple times, can save time.

        results_data = [
            {
                'val': 'Max',
                'NF': beam.get_normal_force(return_max=True),
                'SF': beam.get_shear_force(return_max=True),
                'BM': beam.get_bending_moment(return_max=True),
                'D': beam.get_deflection(return_max=True)
            },
            {
                'val': 'Min',
                'NF': beam.get_normal_force(return_min=True),
                'SF': beam.get_shear_force(return_min=True),
                'BM': beam.get_bending_moment(return_min=True),
                'D': beam.get_deflection(return_min=True)
            },
        ]

        if querys:
            for row in querys:
                x_ = row['Query coordinate (m)']
                results_data.append(
                    {
                        'val': f'x = {x_} m',
                        'NF': beam.get_normal_force(x_)[0],
                        'SF': beam.get_shear_force(x_)[0],
                        'BM': beam.get_bending_moment(x_)[0],
                        'D': beam.get_deflection(x_)[0],
                    },
                )

        t2 = time.perf_counter()
        t = t2 - t1
        dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        color = "success"
        message = f"Calculation completed in {t:.2f} seconds, at {dt}"

    except BaseException:
        color = "danger"
        e = sys.exc_info()[1]
        message = f"Error with calculation. Please check inputs. \
            The following error was observed: {e}"
        results_data = [
            {'type': 'Normal Force', 'max': 0, 'min': 0},
            {'type': 'Shear Force', 'max': 0, 'min': 0},
            {'type': 'Bending Moment', 'max': 0, 'min': 0},
            {'type': 'Deflection', 'max': 0, 'min': 0},
        ]
    if click == 0:
        color = "danger"
        message = "No analysis has been run."
    return graph_1, graph_2, color, message, True, results_data, input_json, False


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


@app.callback(
    Output('basic-support-table', 'data'),
    Input('basic-support-rows-button', 'n_clicks'),
    State('basic-support-table', 'data'),
    State('basic-support-table', 'columns'))
def add_row2b(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append(basic_support_table_init)
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


@app.callback(
    [Output("beam_instructions", "is_open"),
     Output("support_instructions", "is_open"),
     Output("basic_support_instructions", "is_open"),
     Output("point_load_instructions", "is_open"),
     Output("point_torque_instructions", "is_open"),
     Output("distributed_load_instructions", "is_open"),
     Output("query_instructions", "is_open"),
     Output("option_instructions", "is_open")],
    Input("instruction-button", "n_clicks"),
    State("beam_instructions", "is_open"),
)
def toggle_collapse(n, is_open):
    if n:
        a = not is_open
    else:
        a = is_open
    return a, a, a, a, a, a, a, a


@app.callback(
    Output("report", "data"),
    Input('report-button', 'n_clicks'),
    [State("graph_1", "figure"),
     State("graph_2", "figure"),
     State('results-table', 'data')]
)
def report(n, graph_1, graph_2, results):
    date = datetime.now().strftime("%d/%m/%Y")
    if n > 0:
        table = [f"""<tr>
                <td class="tg-baqh">{a['val']}</td>
                <td class="tg-baqh">{a['NF']}</td>
                <td class="tg-baqh">{a['SF']}</td>
                <td class="tg-baqh">{a['BM']}</td>
                <td class="tg-baqh">{a['D']}</td>
                </tr>
                """ for a in results]

        table = ''.join(table)

        content = [
            to_html(fig=graph_1, full_html=False, include_plotlyjs='cdn'),
            """
            <style type="text/css">
            .tg  {border-collapse:collapse;border-spacing:0;margin:120px}
            .tg td{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
            overflow:hidden;padding:10px 20px;word-break:normal;}
            .tg th{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
            font-weight:normal;overflow:hidden;padding:10px 20px;word-break:normal;}
            .tg .tg-5gn2{background-color:#efefef;font-family:Arial, Helvetica, sans-serif !important;;font-size:12px;text-align:center;
            vertical-align:middle}
            .tg .tg-uqo3{background-color:#efefef;text-align:center;vertical-align:top}
            .tg .tg-baqh{text-align:center;vertical-align:top}
            </style>
            <table class="tg">
            <thead>
            <tr>
                <th class="tg-5gn2"></th>
                <th class="tg-uqo3">Normal Force (kN)</th>
                <th class="tg-uqo3">Shear Force (kN)</th>
                <th class="tg-uqo3">Bending Moment (kN.m)</th>
                <th class="tg-uqo3">Deflection (mm)</th>
            </tr>""" + table + """</tbody>
            </table>
            """,
            to_html(fig=graph_2, full_html=False, include_plotlyjs='cdn'),
            f'Report generated at https://indeterminate-beam.herokuapp.com/ on {date} </br>'
        ]

        content = "<br>".join(content)

        return dict(content=content, filename="Report.html")


if __name__ == '__main__':
    app.run_server()
