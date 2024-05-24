import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import os
import random
import zmq.asyncio
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# Initialize the app with a Bootstrap theme and FontAwesome icons
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY, "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css"])

# List of StackExchange sites
site_list = [
    "3dprinting", "academia", "amateur-radio", "android", "anime", "apple",
    "askubuntu", "astronomy", "aviation", "beer", "bicycles", "biology",
    "bitcoin", "blender", "boardgames", "bricks", "buddhism", "chemistry",
    "chinese", "christianity", "civicrm", "codegolf", "codereview",
    "coffee", "cogsci", "communitybuilding", "computer-graphics", 
    "computer-science", "cooking", "craftcms", "crafts", "crypto", "cs50",
    "cseducators", "datascience", "dba", "devops", "diy", "drupal",
    "dsp", "earthscience", "ebooks", "economics", "electronics",
    "elementaryos", "ell", "emacs", "engineering", "english", "ethereum",
    "expatriates", "expressionengine", "fitness", "freelancing", "french",
    "gamedev", "gaming", "gardening", "genealogy", "german", "gis",
    "graphicdesign", "ham", "hinduism", "hsm", "history", "homebrew",
    "home-improvement", "iot", "islam", "italian", "japanese", "joomla",
    "judaism", "korean", "latin", "law", "linguistics", "literature",
    "magento", "martialarts", "math", "matheducators", "mathematica",
    "mechanics", "meta", "monero", "money", "movies", "music",
    "mythology", "networkengineering", "opendata", "opensource", "parenting",
    "patents", "philosophy", "photo", "physics", "pm", "poker", "politics",
    "portuguese", "productivity", "programmers", "quant", "raspberrypi",
    "retrocomputing", "reverseengineering", "robotics", "rpg", "russian",
    "salesforce", "scifi", "scicomp", "security", "serverfault", "sharepoint",
    "skeptics", "smarthome", "softwarerecs", "sound", "space", "spanish",
    "sports", "sqa", "stackapps", "stackoverflow", "startups", "stats",
    "superuser", "sustainability", "tex", "travel", "tridion", "unix",
    "ux", "vi", "video", "webapps", "webmasters", "woodworking", "wordpress",
    "workplace", "worldbuilding", "writing"
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

def run_notebook(notebook_path, parameters=None):
    with open(notebook_path, encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)
    
    ep = ExecutePreprocessor(timeout=6000000, kernel_name='python3')
    
    if parameters:
        param_cell = nbformat.v4.new_code_cell(parameters)
        nb.cells.insert(0, param_cell)
    
    try:
        ep.preprocess(nb, {'metadata': {'path': './'}})
    except Exception as e:
        return str(e)
    
    return None

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("StackExchange Data Exploration Engine", className="text-center my-4 font-weight-bold", style={'color': 'white', 'font-family': 'DejaVu Sans Mono, monospace', 'font-size': '32px'}),
            html.A(html.I(className="fab fa-github fa-2x"), href="https://github.com/HadylTITRI/DataExplorationByRecommendation", className="text-center d-block mb-4", style={'color': 'white'}),
        ], align='center', style={'background-color': '#2c3e50', 'margin':'12px','padding': '16x', 'border-radius': '15px', 'box-shadow': '0 4px 8px rgba(0, 0, 0, 0.1)'})
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Label([html.I(className="fas fa-globe"), " Select StackExchange Site"], className="font-weight-bold", style={'color': 'white', 'font-family': 'DejaVu Sans Mono, monospace','font-weight': 'bold','font-size':'18px', 'margin':'8px' }),
                    html.Div(site_buttons, className="mb-4", style={'column-count': 5,'font-family': 'DejaVu Sans Mono, monospace', 'column-gap': '20px','font-weight': 'bold'}),
                    html.Div(id='selected-site', style={'color': 'black'}),
                    dbc.Button([html.I(className="fas fa-download"), " Collect Data"], id='collect-button', color="primary", className="mb-4", style={'font-family': 'DejaVu Sans Mono, monospace','width': '100%','font-weight': 'bold'}),
                    dbc.Progress(id="progress-bar", striped=True, animated=True, className="mb-4", style={'height': '20px'}),
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
    [Output('progress-bar', 'value'),
     Output('progress-bar', 'color'),
     Output('output-area', 'children')],
    Input('collect-button', 'n_clicks'),
    State('selected-site', 'children'),
    prevent_initial_call=True
)
def collect_data(n_clicks, selected_site_text):
    if n_clicks and selected_site_text:
        site = selected_site_text.split(": ")[1]
        progress = 0
        progress_steps = []
        messages = []
        
        # Step 1: Collect data
        error = run_notebook('APIdataExtraction.ipynb', f"site = '{site}'")
        if error:
            return progress, "danger", [html.Div(f"Error during data collection: {error}", style={'color': 'red'})]
        progress += 33
        progress_steps.append(progress)
        messages.append(html.Div("Data collection complete.", style={'color': 'white'}))
        
        # Step 2: Data preprocessing
        error = run_notebook('DataPreprocessing.ipynb')
        if error:
            return progress, "danger", [html.Div(f"Error during data preprocessing: {error}", style={'color': 'red'})]
        progress += 33
        progress_steps.append(progress)
        messages.append(html.Div("Data preprocessing complete.", style={'color': 'white'}))
        
        # Step 3: Clustering
        error = run_notebook('Clustering.ipynb')
        if error:
            return progress, "danger", [html.Div(f"Error during clustering: {error}", style={'color': 'red'})]
        progress = 100
        progress_steps.append(progress)
        messages.append(html.Div("Clustering complete.", style={'color': 'white'}))

        return progress, "success", messages

    return 0, "info", []

@app.callback(
    Output('recommendation-output', 'children'),
    Input('recommend-button', 'n_clicks'),
    State('user-question', 'value'),
    prevent_initial_call=True
)
def get_recommendations(n_clicks, user_question):
    if n_clicks and isinstance(user_question, str) :
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

if __name__ == '__main__':
    app.run_server(debug=True)
