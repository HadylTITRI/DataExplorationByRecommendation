import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import os
import random
import pymongo
import zmq.asyncio
import asyncio
import threading

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Initialize the app with a Bootstrap theme and FontAwesome icons
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY, "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css"])

# List of StackExchange sites
site_list = [
    "3dprinting", "academia", "amateur-radio", "android", "anime", "apple",
    # Add other sites...
]

# Generate a random color for each button
def generate_color():
    colors = ['primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark']
    return random.choice(colors)

# Create buttons for each site
site_buttons = [
    dbc.Button(site, id={'type': 'site-button', 'index': site}, color=generate_color(), className="mb-2 mr-2", style={'margin-right': '5px', 'margin-bottom': '5px'})
    for site in site_list
]

def run_notebook(notebook_path, parameters=None, progress_update_callback=None):
    with open(notebook_path, encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)
    
    ep = ExecutePreprocessor(timeout=6000000, kernel_name='python3')
    
    if parameters:
        param_cell = nbformat.v4.new_code_cell(parameters)
        nb.cells.insert(0, param_cell)

    try:
        ep.preprocess(nb, {'metadata': {'path': './'}})
        if progress_update_callback:
            progress_update_callback(100)
    except Exception as e:
        return str(e)
    
    return None

# Main layout with navigation
app.layout = dbc.Container([
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.Button("Main Interface", id="main-interface-button", color="primary")),
            dbc.NavItem(dbc.Button("Data Display", id="data-display-button", color="secondary"))
        ],
        brand="Dashboard Navigation",
        color="dark",
        dark=True,
        className="mb-4"
    ),
    html.Div(id='page-content')
], fluid=True)

# Main Interface Layout
main_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("StackExchange Data Exploration Engine", className="text-center my-4 font-weight-bold", style={'color': 'white', 'font-family': 'DejaVu Sans Mono, monospace', 'font-size': '32px'}),
            html.A(html.I(className="fab fa-github fa-2x"), href="https://github.com/HadylTITRI/DataExplorationByRecommendation", className="text-center d-block mb-4", style={'color': 'white'}),
        ], align='center', style={'background-color': '#2c3e50', 'margin':'12px','padding': '16x', 'border-radius': '15px', 'box-shadow': '0 4px 8px rgba(0, 0, 0, 0.1)'} )
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Label([html.I(className="fas fa-globe"), " Select StackExchange Site"], className="font-weight-bold", style={'color': 'white', 'font-family': 'DejaVu Sans Mono, monospace','font-weight': 'bold','font-size':'18px', 'margin':'8px' }),
                    html.Div(site_buttons, className="mb-4", style={'column-count': 5,'font-family': 'DejaVu Sans Mono, monospace', 'column-gap': '20px','font-weight': 'bold'}),
                    html.Div(id='selected-site', style={'color': 'black'}),
                    dbc.Button([html.I(className="fas fa-download"), " Collect Data"], id='collect-button', color="primary", className="mb-4", style={'font-family': 'DejaVu Sans Mono, monospace','width': '100%','font-weight': 'bold'}),
                    dbc.Progress(id="progress-bar-1", striped=True, animated=True, className="mb-4", style={'height': '20px'}),
                    dbc.Progress(id="progress-bar-2", striped=True, animated=True, className="mb-4", style={'height': '20px'}),
                    dbc.Progress(id="progress-bar-3", striped=True, animated=True, className="mb-4", style={'height': '20px'}),
                    html.Div(id='output-area', children=[])
                ])
            ], className="mb-4 shadow-sm", style={'background-color': '#2c3e50', 'border-radius': '15px', 'box-shadow': '0 4px 8px rgba(0, 0, 0, 0.1)', 'padding': '15px'})
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Label([html.I(className="fas fa-question-circle"), " Enter your question"], className="font-weight-bold", style={'color': 'black', 'font-family': 'DejaVu Sans Mono, monospace','font-weight': 'bold'}),
                    dcc.Textarea(id='user-question', className="mb-4", style={'width': '100%', 'height': '120px', 'border-radius': '5px', 'padding': '10px','font-family': 'DejaVu Sans Mono, monospace', 'box-shadow': '0 4px 8px rgba(0, 0, 0, 0.1)'}),
                    dbc.Button([html.I(className="fas fa-lightbulb"), " Get Recommendations"], id='recommend-button', color="success", className="mb-4", style={'font-family': 'DejaVu Sans Mono, monospace','width': '100%'}),
                    html.Div(id='recommendation-output', children=[
                    html.Div(id='recommendation-list')
                    ])
                ])
            ], className="mb-4 shadow-sm", style={'height': '100%', 'border-radius': '15px', 'box-shadow': '0 4px 8px rgba(0, 0, 0, 0.1)'})
        ], width=6)
    ])
], fluid=True)

# Data Display Layout
data_display_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Data Display Interface", className="text-center my-4 font-weight-bold", style={'color': 'black', 'font-family': 'DejaVu Sans Mono, monospace', 'font-size': '32px'}),
        ], align='center', style={'background-color': '#ecf0f1', 'margin':'12px','padding': '16x', 'border-radius': '15px', 'box-shadow': '0 4px 8px rgba(0, 0, 0, 0.1)'} )
    ]),
    dbc.Row([
        dbc.Col([
            # Placeholders for data display elements
            html.Div(id='dataframe-display'),
            dbc.Button("Load MongoDB Schema", id="load-schema-button", color="info", className="mb-4"),
            html.Div(id='mongodb-schema-display')
        ], width=12)
    ])
], fluid=True)

# Callback for navigating between interfaces
@app.callback(
    Output('page-content', 'children'),
    [Input('main-interface-button', 'n_clicks'), Input('data-display-button', 'n_clicks')]
)
def display_page(main_click, data_click):
    ctx = dash.callback_context
    if not ctx.triggered:
        return main_layout
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == 'main-interface-button':
        return main_layout
    elif button_id == 'data-display-button':
        return data_display_layout

# Callbacks for main interface (unchanged)
@app.callback(
    Output('selected-site', 'children'),
    Input({'type': 'site-button', 'index': dash.dependencies.ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def update_selected_site(n_clicks):
    ctx = dash.callback_context

    if not ctx.triggered:
        return "No site selected."
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    site = eval(button_id)['index']
    
    return f"Selected site: {site}"

@app.callback(
    [Output('progress-bar-1', 'value'),
     Output('progress-bar-1', 'color'),
     Output('progress-bar-2', 'value'),
     Output('progress-bar-2', 'color'),
     Output('progress-bar-3', 'value'),
     Output('progress-bar-3', 'color'),
     Output('output-area', 'children')],
    Input('collect-button', 'n_clicks'),
    State('selected-site', 'children'),
    prevent_initial_call=True
)
def collect_data(n_clicks, selected_site_text):
    if n_clicks and selected_site_text:
        site = selected_site_text.split(": ")[1]
        
        progress_values = [0, 0, 0]
        colors = ["info", "info", "info"]

        def update_progress(index, value):
            progress_values[index] = value

        messages = []

        def run_notebook_thread(notebook, index):
            error = run_notebook(notebook, f"site = '{site}'", lambda value: update_progress(index, value))
            if error:
                colors[index] = "danger"
                messages.append(html.Div(f"Error during {notebook}: {error}", style={'color': 'red'}))
            else:
                colors[index] = "success"
                messages.append(html.Div(f"{notebook} complete.", style={'color': 'white'}))

        # Run notebooks in threads
        threads = [
            threading.Thread(target=run_notebook_thread, args=('APIdataExtraction.ipynb', 0)),
            threading.Thread(target=run_notebook_thread, args=('DataPreprocessing.ipynb', 1)),
            threading.Thread(target=run_notebook_thread, args=('Clustering.ipynb', 2)),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        return progress_values[0], colors[0], progress_values[1], colors[1], progress_values[2], colors[2], messages

    return 0, "info", 0, "info", 0, "info", []

@app.callback(
    Output('recommendation-output', 'children'),
    Input('recommend-button', 'n_clicks'),
    State('user-question', 'value'),
    prevent_initial_call=True
)
def get_recommendations(n_clicks, user_question):
    if n_clicks and isinstance(user_question, str):
        if not user_question.strip():
            return [html.Div("Please enter a question.", style={'color': 'red'})]
            
        # Run the recommendation model notebook
        error = run_notebook('RecommendationModel.ipynb', f"user_question ='{user_question}'")
        
        if error:
            return [html.Div(f"Error during recommendation: {error}", style={'color': 'red'})]
        
        # Display recommendations
        if os.path.exists('recommendations.csv') and os.path.getsize('recommendations.csv') > 0:
            recommendations_df = pd.read_csv('recommendations.csv')
            list_html = dbc.Table.from_dataframe(recommendations_df, striped=True, bordered=True, hover=True, className="mt-4")
            return [list_html]

        return [html.Div("No recommendations found.", style={'color': 'red'})]

    return []

# Callback for loading and displaying data in the Data Display Interface
@app.callback(
    Output('dataframe-display', 'children'),
    Input('data-display-button', 'n_clicks')
)
def display_data(n_clicks):
    if n_clicks:
        # Ensure the notebook runs and the data is available
        error = run_notebook('RecommendationModel.ipynb')
        
        if error:
            return [html.Div(f"Error during notebook execution: {error}", style={'color': 'red'})]

        # Load the data
        if os.path.exists('dataframe.csv') and os.path.getsize('dataframe.csv') > 0:
            df = pd.read_csv('dataframe.csv')
            table = dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df.columns],
                style_table={'overflowX': 'auto'},
                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                style_cell={'textAlign': 'left', 'padding': '5px'},
            )
            return table
        else:
            return html.Div("No data available.", style={'color': 'red'})

    return html.Div()

# Callback for loading MongoDB schema
@app.callback(
    Output('mongodb-schema-display', 'children'),
    Input('load-schema-button', 'n_clicks')
)
def load_mongodb_schema(n_clicks):
    if n_clicks:
        try:
            # Connect to MongoDB
            client = pymongo.MongoClient("mongodb://localhost:27017/")
            db = client["your_database_name"]
            
            schema = []
            for collection_name in db.list_collection_names():
                collection = db[collection_name]
                sample_doc = collection.find_one()
                if sample_doc:
                    schema.append(html.H5(f"Collection: {collection_name}"))
                    schema.append(dash_table.DataTable(
                        data=[{"Field": k, "Type": type(v).__name__} for k, v in sample_doc.items()],
                        columns=[{"name": "Field", "id": "Field"}, {"name": "Type", "id": "Type"}],
                        style_table={'overflowX': 'auto'},
                        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                        style_cell={'textAlign': 'left', 'padding': '5px'},
                    ))
                    schema.append(html.Hr())
            return schema
        except Exception as e:
            return html.Div(f"Error: {e}", style={'color': 'red'})
    
    return html.Div("Click the button to load MongoDB schema.")

if __name__ == '__main__':
    app.run_server(debug=True)
