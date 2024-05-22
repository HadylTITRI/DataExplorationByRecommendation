import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import os

# Initialize the app with a dark theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

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
    html.H1("StackExchange Data Analysis Dashboard", className="text-center my-4"),
    
    dbc.Row([
        dbc.Col([
            html.Label("Select StackExchange Site", className="font-weight-bold"),
            dcc.Dropdown(
                id='site-dropdown',
                options=[{'label': site, 'value': site} for site in site_list],
                value='math',
                className="mb-4"
            ),
        ], width=8),
        dbc.Col([
            dbc.Button("Collect Data", id='collect-button', color="primary", className="mb-4")
        ], width=4, className="d-flex align-items-center justify-content-end")
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Progress(id="progress-bar", striped=True, animated=True, className="mb-4")
        ])
    ]),

    dbc.Row([
        dbc.Col([
            html.Div(id='output-area', children=[])
        ])
    ]),

    html.Hr(),

    dbc.Row([
        dbc.Col([
            html.Label("Enter your question", className="font-weight-bold"),
            dcc.Textarea(id='user-question', className="mb-4", style={'width': '100%', 'height': '100px'}),
            dbc.Button("Get Recommendations", id='recommend-button', color="success", className="mb-4")
        ])
    ]),

    dbc.Row([
        dbc.Col([
            html.Div(id='recommendation-output', children=[])
        ])
    ])
])

@app.callback(
    [Output('progress-bar', 'value'),
     Output('progress-bar', 'color'),
     Output('output-area', 'children')],
    Input('collect-button', 'n_clicks'),
    State('site-dropdown', 'value'),
    prevent_initial_call=True
)
def collect_data(n_clicks, site):
    if n_clicks:
        progress = 0
        progress_steps = []
        messages = []
        
        # Step 1: Collect data
        error = run_notebook('APIdataExtraction.ipynb', f"site = '{site}'")
        if error:
            return progress, "danger", [html.Div(f"Error during data collection: {error}", style={'color': 'red'})]
        progress += 33
        progress_steps.append(progress)
        messages.append(html.Div("Data collection complete.", style={'color': 'green'}))
        
        # Step 2: Data preprocessing
        error = run_notebook('DataPreprocessing.ipynb')
        if error:
            return progress, "danger", [html.Div(f"Error during data preprocessing: {error}", style={'color': 'red'})]
        progress += 33
        progress_steps.append(progress)
        messages.append(html.Div("Data preprocessing complete.", style={'color': 'green'}))
        
        # Step 3: Clustering
        error = run_notebook('Clustering.ipynb')
        if error:
            return progress, "danger", [html.Div(f"Error during clustering: {error}", style={'color': 'red'})]
        progress = 100
        progress_steps.append(progress)
        messages.append(html.Div("Clustering complete.", style={'color': 'green'}))
        
        # Show the plot of clusters (assume the plot is saved as 'clusters_plot.png')
        if os.path.exists('clusters_plot.png'):
            img_html = html.Img(src='/assets/clusters_plot.png', style={'width': '100%', 'height': 'auto'})
            messages.append(img_html)

        return progress, "success", messages

    return 0, "info", []

@app.callback(
    Output('recommendation-output', 'children'),
    Input('recommend-button', 'n_clicks'),
    State('user-question', 'value'),
    prevent_initial_call=True
)
def get_recommendations(n_clicks, user_question):
    if n_clicks:
        if not user_question.strip():
            return [html.Div("Please enter a question.", style={'color': 'red'})]

        # Run the recommendation model notebook
        error = run_notebook('RecommendationModel.ipynb', f"user_question = '{user_question}'")
        if error:
            return [html.Div(f"Error during recommendation: {error}", style={'color': 'red'})]

        # Display recommendations
        if os.path.exists('recommendations.csv'):
            recommendations_df = pd.read_csv('recommendations.csv')
            return dbc.Table.from_dataframe(recommendations_df, striped=True, bordered=True, hover=True, dark=True)

        return [html.Div("No recommendations found.", style={'color': 'red'})]

    return []

if __name__ == '__main__':
    app.run_server(debug=True)
