import sys
import os
import base64
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
from indeterminatebeam.units import IMPERIAL_UNITS, METRIC_UNITS, UNIT_KEYS, UNIT_VALUES
from indeterminatebeam.data_validation import (
    assert_number,
    assert_positive_number,
    assert_strictly_positive_number,
    assert_length,
    assert_list_contents,
    assert_contents,
)

from dash_extensions import Download
from dash.exceptions import PreventUpdate
from plotly.io import to_html
import plotly.graph_objects as go

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
* [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JesseBonanno/IndeterminateBeam/blob/main/docs/examples/simple_demo.ipynb)
   The Python based Jupyter Notebook examples
* [![Article](https://img.shields.io/badge/Article-Complete-green.svg)](https://github.com/JesseBonanno/IndeterminateBeam/blob/main/IndeterminateBeam_Article.pdf)
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



def create_table(id_, table, init, row_deletable = True):
    if init:
        data = [init]
    # used to initialise no data for the query table
    else:
        data = []

    table = dash_table.DataTable(
        id=id_,
        columns=[{
            'name': d,
            'id': d,
            'deletable': False,
            'renamable': False,
            'type': table[d]['type'],
            'format': Format(
                symbol=Symbol.yes,
                symbol_suffix=table[d]['units'])
        } for d in table.keys()],
        data=data,
        editable=True,
        row_deletable=row_deletable,
    )
    return table


def create_content(instruction_name, instructions, table, button_label="", button_id="", add_button = True):
    if add_button:
        _ = [
            table,
            html.Br(),
            html.Button(button_label, id=button_id, n_clicks=0),
            dbc.Collapse(
                dbc.Card(dbc.CardBody(instructions)),
                id=instruction_name,
            ),
        ]
    else:
        _ = [
            table,
            html.Br(),
            dbc.Collapse(
                dbc.Card(dbc.CardBody(instructions)),
                id=instruction_name,
            ),
        ]

    card = dbc.Card(
        dbc.CardBody(_),
        className="mt-3",
    )

    return card

            
# Properties for Beam Tab

beam_table_data = {
    'Length': {
        'init': 5,
        'units': ' m',
        'type': 'numeric'
    },
    "Young's Modulus": {
        'init': 200 * 10**9,
        'units': ' Pa',
        'type': 'numeric'
    },
    "Second Moment of Area": {
        'init': 9.05 * 10**-6,
        'units': ' m4',
        'type': 'numeric'
    },
    "Cross-Sectional Area": {
        'init': 0.23,
        'units': ' m2',
        'type': 'numeric'
    },
}

beam_table_init = {k: v['init'] for k, v in beam_table_data.items()}

beam_table = create_table('beam-table', beam_table_data, beam_table_init, row_deletable=False)

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

beam_content = create_content('beam_instructions', beam_instructions, beam_table)


# Properties for (Advanced) Support Tab
# Just do as a table but let inputs be
# R - Restraint, F- Free, or number for spring, Spring not an option for m.

support_table_data = {
    'Coordinate': {
        'init': 0,
        'units': ' m',
        'type': 'numeric'
    },
    "X": {
        'init': 'R',
        'units': ' N/m',
        'type': 'any'
    },
    "Y": {
        'init': 'R',
        'units': ' N/m',
        'type': 'any'
    },
    "M": {
        'init': 'R',
        'units': ' N/m',
        'type': 'any',
    }
}


support_table_init = {k: v['init'] for k, v in support_table_data.items()}

support_table = create_table('support-table', support_table_data, support_table_init)

support_instructions = dcc.Markdown('''

            ###### **Instructions:**

            1. Specify the coodinate location of the support
            2. For each direction specify one of the following:
               * f or F - Indicates a free support
               * r or R - Indicates a rigid support
               * n - Indicates a stiffness of n (default unit N/m)
                 (where n is (generally) a positive number)

            ''')

support_content = create_content('support_instructions', support_instructions, support_table, "Add Support", 'support-rows-button')

# Basic support

basic_support_table_data = {
    'Coordinate': {
        'init': 0,
        'type': 'numeric',
        'presentation': 'input',
    },
    "Support": {
        'init': 'fixed',
        'type': 'any',
        'presentation': 'dropdown',
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
                {'label': 'Fixed', 'value': 'fixed'},
                {'label': 'Pinned', 'value': 'pinned'},
                {'label': 'Roller', 'value': 'roller'},
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
    'Coordinate': {
        'init': 0,
        'units': ' m',
        'type': 'numeric'
    },
    "Force": {
        'init': 0,
        'units': ' N',
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

point_load_table = create_table('point-load-table', point_load_table_data, point_load_table_init)

point_load_instructions = dcc.Markdown('''

            ###### **Instructions:**

            1. Specify the coodinate location of the point load.
            2. Specify the force (default units N)
            3. Specify the load angle where:
               * A positive force with an angle of 0 points horizontally to the right.
               * A positive force with an angle of 90 points vertically in the
                 positive y direction chosen in the options tab (default downwards).

            ''')

point_load_content = create_content('point_load_instructions', point_load_instructions, point_load_table, 'Add Point Load', 'point-load-rows-button')

# Properties for point_torque Tab
point_torque_table_data = {
    'Coordinate': {
        'init': 0,
        'units': ' m',
        'type': 'numeric'
    },
    "Torque": {
        'init': 0,
        'units': ' N.m',
        'type': 'numeric'
    },
}

point_torque_table_init = {k: v['init']
                           for k, v in point_torque_table_data.items()}

point_torque_table = create_table('point-torque-table', point_torque_table_data, point_load_table_init)

point_torque_instructions = dcc.Markdown('''

            ###### **Instructions:**

            1. Specify the coodinate location of the point torque.
            2. Specify the moment (default units N.m)

            Note: A positive moment indicates an anti-clockwise moment direction.

            ''')

point_torque_content = create_content('point_torque_instructions', point_torque_instructions, point_torque_table, 'Add Point Torque', 'point-torque-rows-button')

# Properties for distributed_load Tab

distributed_load_table_data = {
    'Start Coordinate': {
        'init': 0,
        'units': ' m',
        'type': 'numeric'
    },
    'End Coordinate': {
        'init': 0,
        'units': ' m',
        'type': 'numeric'
    },
    'Start Load': {
        'init': 0,
        'units': ' N/m',
        'type': 'numeric'
    },
    'End Load': {
        'init': 0,
        'units': ' N/m',
        'type': 'numeric'
    },

}

distributed_load_table_init = {k: v['init']
                               for k, v in distributed_load_table_data.items()}

distributed_load_table = create_table('distributed-load-table', distributed_load_table_data, distributed_load_table_init)

distributed_load_instructions = dcc.Markdown('''

            ###### **Instructions:**

            1. Specify the start and end locations of the distributed load.
            2. Specify the start and end loads (default units N/m)

            Note: A positive load acts in the positive y direction chosen
            in the options tab (default downwards).

            ''')

distributed_load_content = create_content(
    'distributed_load_instructions',
    distributed_load_instructions,
    distributed_load_table,
    'Add Distributed Load',
    'distributed-load-rows-button'
    )

# Properties for query tab
query_table_init = {
    'Query coordinate': 0
}

query_table_data = {
    'Query coordinate': {
        'init': 0,
        'units': ' m',
        'type': 'numeric'
    },
}

query_table = create_table('query-table',query_table_data, None)

query_instructions = dcc.Markdown('''

            ###### **Instructions:**

            1. Specify a point of interest to have values annotated on graph.

            ''')

query_content = create_content('query_instructions', query_instructions, query_table, 'Add Query', 'query-rows-button')

# Properties for results section
results_columns = [
    {"name": "", "id": "val"},
    {"name": 'Normal Force', "id": "NF"},
    {"name": 'Shear Force', "id": "SF"},
    {"name": 'Bending Moment', "id": "BM"},
    {"name": 'Deflection', "id": "D"},
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

#button to reset options
#
reset_setting_button = dbc.Col(
    [
        dbc.Button(
            "Reset Options",
            id="reset-options-button",
            className="mb-3",
            color="info",
            n_clicks=0,
            block=True,
        ),
    ],
    width=12
)

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

def create_option(label, id_, options=[],default=None):
    option = dbc.FormGroup(
        [
            dbc.Label(label, html_for=id_, width=3),
            dbc.Col(
                dbc.RadioItems(
                    id=id_,
                    options=[{'label':a, 'value':a.lower()} for a in options],
                    value=default,
                    inline=True,
                ),
                width=8,
            ),
        ],
        row=True,
    )
    return option


option_support_input = create_option(
    'Support Mode',
    "option_support_input",
    ['Basic', 'Advanced'],
    'basic'
)

option_default_support = create_option(
    'Default Support Type',
    'option_default_support',
    ['Fixed', 'Pinned', 'Roller'],
    'fixed'
)

option_positive_direction_y = create_option(
    'Positive y direction',
    'option_positive_direction_y',
    ['Up', 'Down'],
    'down'
)
option_result_table = create_option(
    'Result Table',
    'option_result_table',
    ['Hide', 'Show'],
    'show'
)

option_data_point = dbc.FormGroup(
    [
        dbc.Label("Graph Data Points", html_for="option_data_points", width=3),
        dbc.Col(
            dcc.Slider(
                id='option_data_points',
                min=50,
                max=500,
                value=50,
                step=50,
                marks={
                    50: {'label': '50'},
                    250: {'label': '250'},
                    500: {'label': '500'}
                },
                included=True,
            ),
            width=8,
        ),
    ],
    row=True,
)

# unit option implementation
default_units = {}

default_units['SI'] = {
    'length': 'm',
    'force': 'N',
    'moment': 'N.m',
    'distributed': 'N/m',
    'stiffness': 'N/m',
    'A': 'm2',
    'E': 'Pa',
    'I': 'm4',
    'deflection': 'm',
}

default_units['metric'] = {
    'length': 'm',
    'force': 'kN',
    'moment': 'kN.m',
    'distributed': 'kN/m',
    'stiffness': 'kN/mm',
    'A': 'mm2',
    'E': 'MPa',
    'I': 'mm4',
    'deflection': 'mm',
}

default_units['imperial'] = {
    'length': 'ft',
    'force': 'kip',
    'moment': 'kip.ft',
    'distributed': 'kip/ft',
    'stiffness': 'kip/ft',
    'A': 'in2',
    'E': 'kip/in2',
    'I': 'in4',
    'deflection': 'in',    
}

def unit_option_formgroup(group='SI',label='length',units=('m'),default ='m'):
    """Define formgroup for a single unit option"""
    
    assert_contents(group, ("SI","metric","imperial"), "group")
    assert_contents(label, UNIT_KEYS, "label")
    assert_list_contents(units, UNIT_VALUES[label], "units")
    assert_contents(default, units, "default")

    id_ = group + "_" + label
    options = [{'label':a, 'value':a} for a in units]

    _ = dbc.FormGroup(
        [
            dbc.Label(label, html_for=id_, width=3),
            dbc.Col(
                dbc.RadioItems(
                    id=id_,
                    options=options,
                    value=default,
                    inline=True,
                ),
                width=8,
            ),
        ],
        row=True,
    )
    
    return _

# create a simplified method to write the SI_editor
SI_editor = []
group = "SI"
for label in UNIT_KEYS:
    units = [a for a in METRIC_UNITS[label].keys()]
    SI_editor.append(
        unit_option_formgroup(group, label, [default_units[group][label]], default_units[group][label])
    )

metric_editor = []
group = "metric"
for label in UNIT_KEYS:
    units = [a for a in METRIC_UNITS[label].keys()]
    id_ = group + "_" + label
    metric_editor.append(
        unit_option_formgroup(group, label, units, default_units[group][label])
    )

imperial_editor = []
group = "imperial"
for label in UNIT_KEYS:
    units = [a for a in IMPERIAL_UNITS[label].keys()]
    id_ = group + "_" + label
    imperial_editor.append(
        unit_option_formgroup(group, label, units, default_units[group][label])
    )

#option to change units for inputs and outputs
option_units = dbc.FormGroup(
    [
        dbc.Label("Units", html_for='option_units', width=3),
        dbc.Col(
            [
                dbc.RadioItems(
                    id='option_units',
                    options=[
                        {'label': 'SI', 'value': 'SI'},
                        {'label': 'Metric (Custom)', 'value': 'metric'},
                        {'label': 'Imperial (Custom)', 'value': 'imperial'},
                    ],
                    value='SI',
                    inline=True,
                ),
            ],
            width=8,
        ),
    ],
    row=True,
)

option_general_tab = dbc.Form([
    html.Br(),
    option_result_table,
    option_support_input,
    option_default_support,
    option_positive_direction_y,
    option_data_point,
])

option_unit_tab = dbc.Form([
    html.Br(),
    option_units,
    dbc.Tab(
        [
            dbc.Collapse(
                SI_editor,
                id='SI-editor',
                is_open = True,
            ),
            dbc.Collapse(
                metric_editor,
                id='metric-editor',
                is_open=False
            ),
            dbc.Collapse(
                imperial_editor,
                id='imperial-editor',
                is_open=False
            ),
        ],
        #label="Supports",
    ),
])

option_content = dbc.Card(
    dbc.CardBody(
        [
            dbc.Tabs([
                dbc.Tab(option_general_tab, label="General Options"),
                dbc.Tab(option_unit_tab, label="Unit Options"),
            ]),
            html.Br(),
            reset_setting_button,
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
                    id='advanced-support',
                    is_open = False,
                ),
                dbc.Collapse(
                    basic_support_content,
                    id='basic-support',
                    is_open=True

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

report_upload_section = dbc.Row(
    [
        dbc.Label("Work from Report", width=3),
        html.Div([
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files'),
                ]),
                style={
                    'width': '150%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '5px'
                },
                # Allow multiple files to be uploaded
                multiple=False
            ),
        ])
    ]
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
                        dbc.Col(
                            report_upload_section,
                            width=12
                        )
                    ),
                    html.Br(),
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
                                [
                                    dbc.Button(
                                        "Clear Beam",
                                        id="clear-inputs-button",
                                        className="mb-3",
                                        color="info",
                                        n_clicks=0,
                                        block=True,
                                    ),
                                ],
                                width=4
                            ),
                        ],
                    ),
                    dbc.Row(
                        dbc.Col(
                            dbc.Spinner(submit_button),
                            width=12
                        )
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
        html.H2(
            'IndeterminateBeam Calculator',
            style={
                'textAlign': 'center',
                'color': '#191970',
                'padding': '40px 0px 0px 0px',
            }
        ),
        html.Hr(),
        calc_status,
        dcc.Store(id='input-json', storage_type='local'),
        html.Div(id='dummy-div', style=dict(display='none')),
        content_first_row,
        html.Hr(),
        copyright_
    ],
    style=CONTENT_STYLE
)

# Initialise app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.MINTY],
    external_scripts=['https://cdn.jsdelivr.net/gh/JesseBonanno/IndeterminateBeam/assets/gtag.js']
)

server = app.server
app.layout = html.Div([sidebar, content])


# add tab title
app.title = "IndeterminateBeam"

# # update units store
# unit_callback_input = [Input('SI_'+a,'value') for a in METRIC_UNITS.keys()]
# unit_callback_input += [Input('metric_'+a,'value') for a in METRIC_UNITS.keys()]
# unit_callback_input += [Input('imperial_'+a,'value') for a in IMPERIAL_UNITS.keys()]

# @app.callback(
#     Output('json-units', 'data'),
#     [Input('submit_button', 'n_clicks')]+
#     unit_callback_input,  
# )
# def unit_options_setup(
#     n,
#     SI_length,
#     SI_force,
#     SI_moment,
#     SI_distributed,
#     SI_stiffness,
#     SI_A,
#     SI_E,
#     SI_I,
#     SI_deflection,
#     metric_length,
#     metric_force,
#     metric_moment,
#     metric_distributed,
#     metric_stiffness,
#     metric_A,
#     metric_E,
#     metric_I,
#     metric_deflection,
#     imperial_length,
#     imperial_force,
#     imperial_moment,
#     imperial_distributed,
#     imperial_stiffness,
#     imperial_A,
#     imperial_E,
#     imperial_I,
#     imperial_deflection,
#     ):

#     units = {}

#     units['SI'] = {
#         'length':SI_length,
#         'force':SI_force,
#         'moment':SI_moment,
#         'distributed':SI_distributed,
#         'stiffness':SI_stiffness,
#         'A':SI_A,
#         'E':SI_E,
#         'I':SI_I,
#         'deflection':SI_deflection,
#     }

#     units['metric'] = {
#         'length':metric_length,
#         'force':metric_force,
#         'moment':metric_moment,
#         'distributed':metric_distributed,
#         'stiffness':metric_stiffness,
#         'A':metric_A,
#         'E':metric_E,
#         'I':metric_I,
#         'deflection':metric_deflection,
#     }

#     units['imperial'] = {
#         'length':imperial_length,
#         'force':imperial_force,
#         'moment':imperial_moment,
#         'distributed':imperial_distributed,
#         'stiffness':imperial_stiffness,
#         'A':imperial_A,
#         'E':imperial_E,
#         'I':imperial_I,
#         'deflection':imperial_deflection,
#         }

#     return json.dumps(units)

# ANALYSIS
unit_callback_state = [State('SI_'+a,'value') for a in METRIC_UNITS.keys()]
unit_callback_state += [State('metric_'+a,'value') for a in METRIC_UNITS.keys()]
unit_callback_state += [State('imperial_'+a,'value') for a in IMPERIAL_UNITS.keys()]

@app.callback(
    [
        Output('graph_1', 'figure'),
        Output('graph_2', 'figure'),
        Output('alert-fade', 'color'),
        Output('alert-fade', 'children'),
        Output('alert-fade', 'is_open'),
        Output('results-table', 'data'),
        Output('input-json', 'data'),
        Output('submit_button', 'disabled'),
    ],
    [
        Input('submit_button', 'n_clicks'),
        Input('dummy-div', 'children'),
    ],
    [
        State('beam-table', 'data'),
        State('point-load-table', 'data'),
        State('point-torque-table', 'data'),
        State('query-table', 'data'),
        State('distributed-load-table', 'data'),
        State('support-table', 'data'),
        State('basic-support-table', 'data'),
        State('graph_1', 'figure'),
        State('graph_2', 'figure'),
        State('input-json', 'data'),
        State('option_support_input', 'value'),
        State('option_default_support','value'),
        State('option_positive_direction_y', 'value'),
        State('option_data_points', 'value'),
        State('option_result_table', 'value'),
        State('option_units', 'value'),
    ] + unit_callback_state
    )
def analyse_beam(
        click,
        dummy_div,
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
        option_support,
        option_default_support,
        positive_y_direction,
        data_points,
        option_result_table,
        option_units,
        SI_length,
        SI_force,
        SI_moment,
        SI_distributed,
        SI_stiffness,
        SI_A,
        SI_E,
        SI_I,
        SI_deflection,
        metric_length,
        metric_force,
        metric_moment,
        metric_distributed,
        metric_stiffness,
        metric_A,
        metric_E,
        metric_I,
        metric_deflection,
        imperial_length,
        imperial_force,
        imperial_moment,
        imperial_distributed,
        imperial_stiffness,
        imperial_A,
        imperial_E,
        imperial_I,
        imperial_deflection,
        ):

    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # if an update was raised by button, and that was by a additional row, dont run.
    if dummy_div is False and button_id == 'dummy-div':
        raise PreventUpdate

    t1 = time.perf_counter()

    units = {}

    units['SI'] = {
        'length':SI_length,
        'force':SI_force,
        'moment':SI_moment,
        'distributed':SI_distributed,
        'stiffness':SI_stiffness,
        'A':SI_A,
        'E':SI_E,
        'I':SI_I,
        'deflection':SI_deflection,
    }

    units['metric'] = {
        'length':metric_length,
        'force':metric_force,
        'moment':metric_moment,
        'distributed':metric_distributed,
        'stiffness':metric_stiffness,
        'A':metric_A,
        'E':metric_E,
        'I':metric_I,
        'deflection':metric_deflection,
    }

    units['imperial'] = {
        'length':imperial_length,
        'force':imperial_force,
        'moment':imperial_moment,
        'distributed':imperial_distributed,
        'stiffness':imperial_stiffness,
        'A':imperial_A,
        'E':imperial_E,
        'I':imperial_I,
        'deflection':imperial_deflection,
        }

    # jsonify all inputs
    input_json = json.dumps(
        {
            'beam': beams,
            'advanced_supports': advanced_supports,
            'basic_supports': basic_supports,
            'point_loads': point_loads,
            'point_torques': point_torques,
            'distributed_loads': distributed_loads,
            'querys': querys,
            'adv_sup': option_support,
            'default_support':option_default_support,
            'y': positive_y_direction,
            'data_points': data_points,
            'option_units': option_units,
            'result_table': option_result_table,
            'unit_dictionary': units,
        }
    )

    for i, s in enumerate(basic_supports):
        sup = s.pop('Support')
        if sup == 'fixed':
            s['X'] = 'R'
            s['Y'] = 'R'
            s['M'] = 'R'
        elif sup == 'pinned':
            s['X'] = 'R'
            s['Y'] = 'R'
            s['M'] = 'F'
        elif sup == 'roller':
            s['X'] = 'F'
            s['Y'] = 'R'
            s['M'] = 'F'
        basic_supports[i] = s

    if option_support == 'advanced':
        supports = advanced_supports
    else:
        supports = basic_supports

    # if all inputs the same as stored inputs then
    # no need to calculate again.
    # if clicks 0 then inputs are set to prev input
    # hence they will be the same but will need to run the
    # analysis to show the results.
    if input_json == prev_input and click > 0:
        raise PreventUpdate

    # try:

    if positive_y_direction == 'up':
        d_ = 1
    else:
        d_ = -1

    for row in beams:
        beam = Beam(*(float(a) for a in row.values()))

    beam._DATA_POINTS = data_points


    beam.update_units('length', units[option_units]['length'])
    beam.update_units('force', units[option_units]['force'])
    beam.update_units('moment', units[option_units]['moment'])
    beam.update_units('distributed', units[option_units]['distributed'])
    beam.update_units('stiffness', units[option_units]['stiffness'])
    beam.update_units('A', units[option_units]['A'])
    beam.update_units('E', units[option_units]['E'])
    beam.update_units('I', units[option_units]['I'])
    beam.update_units('deflection', units[option_units]['deflection'])

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
                    float(row['Coordinate']),
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
                        float(row['Start Load']),
                        float(row['End Load'])
                    ),
                    span=(
                        float(row['Start Coordinate']),
                        float(row['End Coordinate'])
                    ),
                    angle=(d_ * 90)
                )
            )

    if point_loads:
        for row in point_loads:
            beam.add_loads(
                PointLoad(
                    float(row['Force']),
                    float(row['Coordinate']),
                    d_ * float(row['Angle (deg)'])
                )
            )

    if point_torques:
        for row in point_torques:
            beam.add_loads(
                PointTorque(
                    float(row['Torque']),
                    float(row['Coordinate']),
                )
            )

    beam.analyse()

    if querys:
        for row in querys:
            beam.add_query_points(
                float(row['Query coordinate']),
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
            'NF (' + units[option_units]['force'] +')': f'{beam.get_normal_force(return_max=True):.3f}',
            'SF (' + units[option_units]['force'] +')': f'{beam.get_shear_force(return_max=True):.3f}',
            'BM (' + units[option_units]['moment'] +')': f'{beam.get_bending_moment(return_max=True):.3f}',
            'D (' + units[option_units]['deflection'] +')': f'{beam.get_deflection(return_max=True):.3f}',
        },
        {
            'val': 'Min',
            'NF (' + units[option_units]['force'] +')': f'{beam.get_normal_force(return_min=True):.3f}',
            'SF (' + units[option_units]['force'] +')': f'{beam.get_shear_force(return_min=True):.3f}',
            'BM (' + units[option_units]['moment'] +')': f'{beam.get_bending_moment(return_min=True):.3f}',
            'D (' + units[option_units]['deflection'] +')': f'{beam.get_deflection(return_min=True):.3f}',
        },
    ]

    if querys:
        for row in querys:
            x_ = row['Query coordinate']
            u_ = units[option_units]['length']
            results_data.append(
                {
                    'val': f'x = {x_} {u_}',
                    'NF (' + units[option_units]['force'] +')': f'{beam.get_normal_force(x_):.3f}',
                    'SF (' + units[option_units]['force'] +')': f'{beam.get_shear_force(x_):.3f}',
                    'BM (' + units[option_units]['moment'] +')': f'{beam.get_bending_moment(x_):.3f}',
                    'D (' + units[option_units]['deflection'] +')': f'{beam.get_deflection(x_):.3f}',
                },
            )

    t2 = time.perf_counter()
    t = t2 - t1
    dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    color = "success"
    message = f"Calculation completed in {t:.2f} seconds, at {dt}"

    # except BaseException:
    #     color = "danger"
    #     e = sys.exc_info()[1]
    #     message = f"Error with calculation. Please check inputs. \
    #         The following error was observed: {e}"
    #     results_data = [
    #         {'type': 'Normal Force', 'max': 0, 'min': 0},
    #         {'type': 'Shear Force', 'max': 0, 'min': 0},
    #         {'type': 'Bending Moment', 'max': 0, 'min': 0},
    #         {'type': 'Deflection', 'max': 0, 'min': 0},
    #     ]
    # if click == 0 and button_id == 'dummy-div':
    #     color = "danger"
    #     message = "No analysis has been run."
    return graph_1, graph_2, color, message, True, results_data, input_json, False


# ADD ROWS AND RESTORE DATA AND CLEAR DATA
# (ANYTHING TABLE RELATED)
# update units store
unit_output = [Output('SI_'+a,'value') for a in METRIC_UNITS.keys()]
unit_output += [Output('metric_'+a,'value') for a in METRIC_UNITS.keys()]
unit_output += [Output('imperial_'+a,'value') for a in IMPERIAL_UNITS.keys()]

unit_state = [State('SI_'+a,'value') for a in METRIC_UNITS.keys()]
unit_state += [State('metric_'+a,'value') for a in METRIC_UNITS.keys()]
unit_state += [State('imperial_'+a,'value') for a in IMPERIAL_UNITS.keys()]
    
@app.callback(
    [
        Output('beam-table', 'data'),
        Output('support-table', 'data'),
        Output('basic-support-table', 'data'),
        Output('point-load-table', 'data'),
        Output('point-torque-table', 'data'),
        Output('distributed-load-table', 'data'),
        Output('query-table', 'data'),
        Output('option_support_input', 'value'),
        Output('option_default_support','value'),
        Output('option_positive_direction_y', 'value'),
        Output('option_result_table', 'value'),
        Output('option_data_points', 'value'),
        Output('option_units', 'value'),
        Output('dummy-div','children'),
    ] + unit_output,
    [
        Input('support-rows-button', 'n_clicks'),
        Input('basic-support-rows-button', 'n_clicks'),
        Input('point-load-rows-button', 'n_clicks'),
        Input('point-torque-rows-button', 'n_clicks'),
        Input('distributed-load-rows-button', 'n_clicks'),
        Input('query-rows-button', 'n_clicks'),
        Input('clear-inputs-button', 'n_clicks'),
        Input('reset-options-button', 'n_clicks'),
        Input('upload-data', 'contents'),
    ],
    [
        State('beam-table', 'data'),
        State('support-table', 'data'),
        State('basic-support-table', 'data'),
        State('point-load-table', 'data'),
        State('point-torque-table', 'data'),
        State('distributed-load-table', 'data'),
        State('query-table', 'data'),
        State('option_support_input', 'value'),
        State('option_default_support','value'),
        State('option_positive_direction_y', 'value'),
        State('option_result_table', 'value'),
        State('option_data_points', 'value'),
        State('option_units','value'),
        State('input-json', 'data'),
    ] + unit_state,
)
def update_tables(
    support_table_clicks,
    basic_support_table_clicks,
    point_load_table_clicks,
    point_torque_table_clicks,
    distributed_load_table_clicks,
    query_table_clicks,
    clear_inputs_clicks,
    reset_settings_clicks,
    upload_data,
    beam_table_rows,
    advanced_support_table_rows,
    basic_support_table_rows,
    point_load_table_rows,
    point_torque_table_rows,
    distributed_load_table_rows,
    query_table_rows,
    option_support_input,
    option_default_support,
    option_positive_direction_y,
    option_result_table,
    option_data_points,
    option_units,
    input_json_data,
    SI_length,
    SI_force,
    SI_moment,
    SI_distributed,
    SI_stiffness,
    SI_A,
    SI_E,
    SI_I,
    SI_deflection,
    metric_length,
    metric_force,
    metric_moment,
    metric_distributed,
    metric_stiffness,
    metric_A,
    metric_E,
    metric_I,
    metric_deflection,
    imperial_length,
    imperial_force,
    imperial_moment,
    imperial_distributed,
    imperial_stiffness,
    imperial_A,
    imperial_E,
    imperial_I,
    imperial_deflection,
    ):
    #solution summary:
    # in order to automatically update tables to previously stored information
    # it is necessary to use the same function to add table rows and to add the past information
    # as graphs are produced from clicking analysis, a dummy variable was created that triggers
    # an analysis run. In order to make the model not run every time a row is added, the value is set to
    # FALSE which makes the analysis not run as per the analysis function. As the data in the function
    # can remain FALSE or TRUE while data is changed and analysis is re run, a check on the trigger context
    # is also needed in the analysis function.
    # Also, as data is now always automatically added from previous, it is useful to be able to clear data
    # so a clear inputs button and functionality was added.
    if not input_json_data:
        raise PreventUpdate

    units = {}

    units['SI'] = {
        'length':SI_length,
        'force':SI_force,
        'moment':SI_moment,
        'distributed':SI_distributed,
        'stiffness':SI_stiffness,
        'A':SI_A,
        'E':SI_E,
        'I':SI_I,
        'deflection':SI_deflection,
    }

    units['metric'] = {
        'length':metric_length,
        'force':metric_force,
        'moment':metric_moment,
        'distributed':metric_distributed,
        'stiffness':metric_stiffness,
        'A':metric_A,
        'E':metric_E,
        'I':metric_I,
        'deflection':metric_deflection,
    }

    units['imperial'] = {
        'length':imperial_length,
        'force':imperial_force,
        'moment':imperial_moment,
        'distributed':imperial_distributed,
        'stiffness':imperial_stiffness,
        'A':imperial_A,
        'E':imperial_E,
        'I':imperial_I,
        'deflection':imperial_deflection,
        }

    units_values =[]
    for a in units.keys():
        units_values += [a for a in units[a].values()]

    ctx = dash.callback_context
    dummy_div = False

    # website just started or triggered by uploading report
    if not ctx.triggered or ctx.triggered[0]['prop_id'].split('.')[0] == 'upload-data':
        # website just started with no saved data
        if not input_json_data:
            return [
                beam_table_rows,
                advanced_support_table_rows,
                basic_support_table_rows,
                point_load_table_rows,
                point_torque_table_rows,
                distributed_load_table_rows,
                query_table_rows,
                option_support_input,
                option_default_support,
                option_positive_direction_y,
                option_result_table,
                option_data_points,
                option_units,
                dummy_div,
            ] + units_values

        # report uploaded
        elif ctx.triggered[0]['prop_id'].split('.')[0] == 'upload-data':
            data = upload_data.encode("utf8").split(b";base64,")[1]
            data = base64.b64decode(data)
            data = data.decode('utf-8')
            data = data.split('--')[1]
            data.replace('null', 'True')
            data.replace('None', 'True')
            data = json.loads(data)
            
        #website started with saved data
        else:
            data = json.loads(input_json_data)

        dummy_div = True

        beam_table_rows = data['beam']
        basic_support_table_rows =data['basic_supports']
        advanced_support_table_rows = data['advanced_supports']
        point_load_table_rows = data['point_loads']
        point_torque_table_rows = data['point_torques']
        distributed_load_table_rows = data['distributed_loads']
        query_table_rows = data['querys']
        option_support_input = data['adv_sup']
        option_default_support = data['default_support']
        option_positive_direction_y = data['y']
        option_result_table = data['result_table']
        option_data_points = data['data_points']
        option_units = data['option_units']
        units = data['unit_dictionary']

        units_values = []
        for a in units.keys():
            units_values += [b for b in units[a].values()]

        return [
            beam_table_rows,
            advanced_support_table_rows,
            basic_support_table_rows,
            point_load_table_rows,
            point_torque_table_rows,
            distributed_load_table_rows,
            query_table_rows,
            option_support_input,
            option_default_support,
            option_positive_direction_y,
            option_result_table,
            option_data_points,
            option_units,
            dummy_div,
        ] + units_values

    # triggered by adding in new row to table
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'support-rows-button':
        advanced_support_table_rows.append(support_table_init)
    elif button_id == 'basic-support-rows-button':

        bs_table_data = {
            'Coordinate': {
                'init': 0,
            },
            "Support": {
                'init': option_default_support,
            }
        }

        bs_table_init = {
            k: v['init'] for k, v in bs_table_data.items()
        }

        basic_support_table_rows.append(bs_table_init)

    elif button_id == 'point-load-rows-button':
        point_load_table_rows.append(point_load_table_init)

    elif button_id == 'point-torque-rows-button':
        point_torque_table_rows.append(point_torque_table_init)
    elif button_id == 'distributed-load-rows-button':
       distributed_load_table_rows.append(distributed_load_table_init)
    elif button_id == 'query-rows-button':
       query_table_rows.append(query_table_init)

    # clear inputs but save options
    elif button_id == 'clear-inputs-button':
        return [
            [beam_table_init],
            [support_table_init],
            [basic_support_table_init],
            [point_load_table_init],
            [point_torque_table_init],
            [distributed_load_table_init],
            [],
            option_support_input,
            option_default_support,
            option_positive_direction_y,
            option_result_table,
            option_data_points,
            option_units,
            True,
        ] + units_values

    # clear options
    elif button_id == 'reset-options-button':
        #use default unit properties 
        units_values =[]
        for a in default_units.keys():
            units_values += [b for b in default_units[a].values()]

        return [
            beam_table_rows,
            advanced_support_table_rows,
            basic_support_table_rows,
            point_load_table_rows,
            point_torque_table_rows,
            distributed_load_table_rows,
            query_table_rows,
            'basic',
            'fixed',
            'down',
            'show',
            50,
            "SI",
            True,
        ] + units_values

    return [
        beam_table_rows,
        advanced_support_table_rows,
        basic_support_table_rows,
        point_load_table_rows,
        point_torque_table_rows,
        distributed_load_table_rows,
        query_table_rows,
        option_support_input,
        option_default_support,
        option_positive_direction_y,
        option_result_table,
        option_data_points,
        option_units,
        dummy_div
    ] + units_values

# options - support mode
@app.callback(
    [Output('advanced-support', 'is_open'),
     Output('basic-support', 'is_open')],
    Input('option_support_input', 'value')
)
def support_setup(mode):
    if mode == 'basic':
        return False, True
    return True, False

# options - units mode
@app.callback(
    [
        Output('SI-editor', 'is_open'),
        Output('metric-editor', 'is_open'),
        Output('imperial-editor', 'is_open')
    ],
    Input('option_units', 'value')
)
def support_setup(mode):
    if mode == 'SI':
        return True, False, False
    elif mode == 'metric':
        return False, True, False
    else:
        return False, False, True

# option - result data (to be query data in future really)
@app.callback(
    Output('results-collapse', 'is_open'),
    Input('option_result_table', 'value')
)
def results_setup(mode):
    if mode == 'hide':
        return False
    return True


#instructions open
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

# if any of the unit values change update the table columns
unit_input = [Input('SI_'+a,'value') for a in METRIC_UNITS.keys()]
unit_input += [Input('metric_'+a,'value') for a in METRIC_UNITS.keys()]
unit_input += [Input('imperial_'+a,'value') for a in IMPERIAL_UNITS.keys()]
    
@app.callback(
    [
        Output('beam-table', 'columns'),
        Output('support-table', 'columns'),
        Output('basic-support-table','columns'),
        Output('point-load-table', 'columns'),
        Output('point-torque-table', 'columns'),
        Output('distributed-load-table', 'columns'),
        Output('query-table', 'columns'),
        Output('results-table', 'columns'),
    ],
    [
        Input('option_units', 'value'),
    ] + unit_input,
    State('input-json', 'data'),
)
def update_tables(
    option_units,
    SI_length,
    SI_force,
    SI_moment,
    SI_distributed,
    SI_stiffness,
    SI_A,
    SI_E,
    SI_I,
    SI_deflection,
    metric_length,
    metric_force,
    metric_moment,
    metric_distributed,
    metric_stiffness,
    metric_A,
    metric_E,
    metric_I,
    metric_deflection,
    imperial_length,
    imperial_force,
    imperial_moment,
    imperial_distributed,
    imperial_stiffness,
    imperial_A,
    imperial_E,
    imperial_I,
    imperial_deflection,
    input_json_data,
    ):
    if not input_json_data:
        raise PreventUpdate
    units = {}

    units['SI'] = {
        'length':SI_length,
        'force':SI_force,
        'moment':SI_moment,
        'distributed':SI_distributed,
        'stiffness':SI_stiffness,
        'A':SI_A,
        'E':SI_E,
        'I':SI_I,
        'deflection':SI_deflection,
    }

    units['metric'] = {
        'length':metric_length,
        'force':metric_force,
        'moment':metric_moment,
        'distributed':metric_distributed,
        'stiffness':metric_stiffness,
        'A':metric_A,
        'E':metric_E,
        'I':metric_I,
        'deflection':metric_deflection,
    }

    units['imperial'] = {
        'length':imperial_length,
        'force':imperial_force,
        'moment':imperial_moment,
        'distributed':imperial_distributed,
        'stiffness':imperial_stiffness,
        'A':imperial_A,
        'E':imperial_E,
        'I':imperial_I,
        'deflection':imperial_deflection,
        }

    #update table default propertie
    beam_table_data['Length']['units'] = ' '+units[option_units]['length']
    beam_table_data["Young's Modulus"]['units'] = ' ' +units[option_units]['E']
    beam_table_data['Second Moment of Area']['units'] = ' '+units[option_units]['I']
    beam_table_data['Cross-Sectional Area']['units'] = ' '+units[option_units]['A']

    beam_table_columns = [
        {
            'name': d,
            'id': d,
            'deletable': False,
            'renamable': False,
            'type': beam_table_data[d]['type'],
            'format': Format(
                symbol=Symbol.yes,
                symbol_suffix=beam_table_data[d]['units'])
        } for d in beam_table_data.keys()]

    support_table_data['Coordinate']['units'] = ' '+units[option_units]['length']
    support_table_data['X']['units'] = ' '+units[option_units]['stiffness']
    support_table_data['Y']['units'] = ' '+units[option_units]['stiffness']
    support_table_data['M']['units'] = ' '+units[option_units]['stiffness']

    support_table_columns =[
        {
            'name': d,
            'id': d,
            'deletable': False,
            'renamable': False,
            'type': support_table_data[d]['type'],
            'format': Format(
                symbol=Symbol.yes,
                symbol_suffix=support_table_data[d]['units'])
        } for d in support_table_data.keys()]

    basic_support_table_columns =[
        {
            'name': 'Coordinate',
            'id': 'Coordinate',
            'deletable': False,
            'renamable': False,
            'type': 'numeric',
            'presentation': 'input',
            'format': Format(
                symbol=Symbol.yes,
                symbol_suffix=' '+units[option_units]['length'])
        },
        {
            'name': 'Support',
            'id': 'Support',
            'deletable': False,
            'renamable': False,
            'type': 'any',
            'presentation': 'dropdown',
        },
    ]

    support_table_columns =[
        {
            'name': d,
            'id': d,
            'deletable': False,
            'renamable': False,
            'type': support_table_data[d]['type'],
            'format': Format(
                symbol=Symbol.yes,
                symbol_suffix=support_table_data[d]['units'])
        } for d in support_table_data.keys()
    ]


    # Properties for point_load Tab
    point_load_table_data['Coordinate']['units'] = ' '+units[option_units]['length']
    point_load_table_data['Force']['units'] = ' '+units[option_units]['force']

    point_load_table_columns= [
        {
            'name': d,
            'id': d,
            'deletable': False,
            'renamable': False,
            'type': point_load_table_data[d]['type'],
            'format': Format(
                symbol=Symbol.yes,
                symbol_suffix=point_load_table_data[d]['units'])
        } for d in point_load_table_data.keys()
    ]

    point_torque_table_data['Coordinate']['units'] = ' '+units[option_units]['length']
    point_torque_table_data['Torque']['units'] = ' '+units[option_units]['moment']

    point_torque_table_columns=[{
            'name': d,
            'id': d,
            'deletable': False,
            'renamable': False,
            'type': point_torque_table_data[d]['type'],
            'format': Format(
                symbol=Symbol.yes,
                symbol_suffix=point_torque_table_data[d]['units'])
        } for d in point_torque_table_data.keys()
    ]
    
    # Properties for distributed_load Tab
    distributed_load_table_data['Start Coordinate']['units'] = ' '+units[option_units]['length']
    distributed_load_table_data['End Coordinate']['units'] = ' '+units[option_units]['length']
    distributed_load_table_data['Start Load']['units'] = ' '+units[option_units]['distributed']
    distributed_load_table_data['End Load']['units'] = ' '+units[option_units]['distributed']

    distributed_load_table_columns=[{
            'name': d,
            'id': d,
            'deletable': False,
            'renamable': False,
            'type': distributed_load_table_data[d]['type'],
            'format': Format(
                symbol=Symbol.yes,
                symbol_suffix=distributed_load_table_data[d]['units'])
        } for d in distributed_load_table_data.keys()
    ]

    # Properties for query tab
    query_table_columns= [
        {
            'name': i,
            'id': i,
            'deletable': False,
            'renamable': False,
            'type': 'numeric',
            'format': Format(
                symbol=Symbol.yes,
                symbol_suffix=' '+units[option_units]['length'])
        } for i in query_table_init.keys()
    ]

    results_table_columns = [
        {"name": "", "id": "val"},
        {"name": f"Normal Force ({units[option_units]['force']})", "id": 'NF (' + units[option_units]['force'] +')'},
        {"name": f"Shear Force ({units[option_units]['force']})", "id": 'SF (' + units[option_units]['force'] +')'},
        {"name": f"Bending Moment ({units[option_units]['moment']})", "id": 'BM (' + units[option_units]['moment'] +')'},
        {"name": f"Deflection ({units[option_units]['deflection']})", "id": 'D (' + units[option_units]['deflection'] +')'},
    ]

    return [
        beam_table_columns,
        support_table_columns,
        basic_support_table_columns,
        point_load_table_columns,
        point_torque_table_columns,
        distributed_load_table_columns,
        query_table_columns,
        results_table_columns,
    ]

# Generate Report
@app.callback(
    Output("report", "data"),
    Input('report-button', 'n_clicks'),
    [State("graph_1", "figure"),
     State("graph_2", "figure"),
     State('results-table', 'data'),
     State('input-json','data')]
)
def report(n, graph_1, graph_2, results, input_json):
    
    if not json:
        raise PreventUpdate

    unit_information = json.loads(input_json)
    option_units = unit_information['option_units']
    units = unit_information['unit_dictionary']

    date = datetime.now().strftime("%d/%m/%Y")
    #if the botton has been clicked.
    beam_data = "<!--" + input_json + "-->"

    if n > 0:
        # for each row in the results table,
        # write html table row
        table = [f"""<tr>
                <td class="tg-baqh">{a['val']}</td>
                <td class="tg-baqh">{a['NF (' + units[option_units]['force'] +')']}</td>
                <td class="tg-baqh">{a['SF (' + units[option_units]['force'] +')']}</td>
                <td class="tg-baqh">{a['BM (' + units[option_units]['moment'] +')']}</td>
                <td class="tg-baqh">{a['D (' + units[option_units]['deflection'] +')']}</td>
                </tr>
                """ for a in results]

        # join all the strings for each table row
        table = ''.join(table)

        #help graph 2 fit better on the second page.
        graph_2 = go.Figure(graph_2)
        graph_2.update_layout(height=950)

        # report to consist of graph_1, table and graph_2, and date generated tag
        # cant remember why to_html properties are set the way they are set.
        # table format appropriated from an online generator.
        # added page-break-after:always for formatting when print to pdf
        content = [
            "<!DOCTYPE html><html>",
            beam_data,
            to_html(fig=graph_1, full_html=False, include_plotlyjs='cdn'),
            """
            <style type="text/css">
            .tg  {border-collapse:collapse;border-spacing:0;margin:20px;page-break-after:always}
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
            """+ 
            f"""<tr>
                <th class="tg-5gn2"></th>
                <th class="tg-uqo3">Normal Force {units[option_units]['force']}</th>
                <th class="tg-uqo3">Shear Force {units[option_units]['force']}</th>
                <th class="tg-uqo3">Bending Moment {units[option_units]['moment']}</th>
                <th class="tg-uqo3">Deflection {units[option_units]['deflection']}</th>
            </tr>""" + table + """</tbody>
            </table>
            """,
            to_html(fig=graph_2, full_html=False, include_plotlyjs='cdn'),
            f'<i>Report generated at https://indeterminate-beam.herokuapp.com/ {__version__} on {date}</i>',
            "</html>"
        ]

        content = "<br>".join(content)

        filename = "IndeterminateBeam_Report_"+ datetime.now().strftime("%d/%m/%Y") + ".html"

        return dict(content=content, filename=filename)


if __name__ == '__main__':
    app.run_server(debug=True)
