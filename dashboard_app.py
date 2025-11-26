import pandas as pd
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go

# Load datasets
DF_FR_PATH = 'data_desudo_france.csv'
DF_IT_PATH = 'data_desudo_italy.csv'

df_france = pd.read_csv(DF_FR_PATH)
df_italy = pd.read_csv(DF_IT_PATH)

# Combine datasets
df = pd.concat([df_france, df_italy], ignore_index=True)

# Preprocess dates
df['contractstartdate'] = pd.to_datetime(df['contractstartdate'], errors='coerce')
df['contractenddate'] = pd.to_datetime(df['contractenddate'], errors='coerce')
df['start_quarter'] = df['contractstartdate'].dt.to_period('Q')
df['month'] = df['contractstartdate'].dt.to_period('M')

# Fiscal KPIs
total_revenue = df['totalcapitalamount'].sum()
avg_revenue_per_dealer = df.groupby('dealerbpid')['totalcapitalamount'].sum().mean()
top_dealer_revenue = df.groupby('dealerbpid')['totalcapitalamount'].sum().max()
active_contracts = df[df['contract_status'].str.contains('LIVE', na=False)].shape[0]

# Initialize Dash app
app = Dash(__name__)
server = app.server  # for production hosting
app.title = "Dealer & Financial Dashboard"

app.layout = html.Div([
    html.H1('Dealer & Financial Dashboard', style={'textAlign': 'center'}),
    html.Div([
        html.H3('Fiscal KPIs'),
        html.Div([
            html.P(f"Total Revenue: €{total_revenue:,.2f}"),
            html.P(f"Average Revenue per Dealer: €{avg_revenue_per_dealer:,.2f}"),
            html.P(f"Top Dealer Revenue: €{top_dealer_revenue:,.2f}"),
            html.P(f"Active Contracts: {active_contracts}")
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(2, 1fr)', 'gap': '20px'})
    ], style={'padding': '20px', 'backgroundColor': '#f9f9f9'}),
    dcc.Tabs([
        dcc.Tab(label='Trends', children=[
            html.Div([
                html.Label('Date Range:'),
                dcc.DatePickerRange(
                    id='date-range',
                    start_date=df['contractstartdate'].min(),
                    end_date=df['contractstartdate'].max()
                ),
                html.Label('Fuel Type:'),
                dcc.Dropdown(id='fuel-filter', options=[{'label': ft, 'value': ft} for ft in df['fueltypecode'].dropna().unique()], multi=True),
                html.Label('Car Model:'),
                dcc.Dropdown(id='model-filter', options=[{'label': m, 'value': m} for m in df['modeldescription'].dropna().unique()], multi=True),
                dcc.Graph(id='trend-graph')
            ])
        ]),
        dcc.Tab(label='Variance', children=[
            html.Div([
                html.H3('Dealer-level Q4 vs Q1 Heatmap'),
                dcc.Graph(id='heatmap'),
                html.H3('Top Dealer Variance Table'),
                dash_table.DataTable(id='variance-table', style_table={'overflowX': 'auto'})
            ])
        ]),
        dcc.Tab(label='Car Model Analysis', children=[dcc.Graph(id='car-model-analysis')]),
        dcc.Tab(label='Revenue Analysis', children=[dcc.Graph(id='revenue-analysis')]),
        dcc.Tab(label='Seasonal Patterns', children=[
            html.Div([
                dcc.Graph(id='monthly-patterns'),
                dcc.Graph(id='quarterly-patterns')
            ])
        ])
    ])
])

# Callbacks
@app.callback(
    Output('trend-graph', 'figure'),
    [Input('date-range', 'start_date'), Input('date-range', 'end_date'), Input('fuel-filter', 'value'), Input('model-filter', 'value')]
)
def update_trend(start_date, end_date, fuel_types, models):
    dff = df.copy()
    if start_date and end_date:
        dff = dff[(dff['contractstartdate'] >= pd.to_datetime(start_date)) & (dff['contractstartdate'] <= pd.to_datetime(end_date))]
    if fuel_types:
        dff = dff[dff['fueltypecode'].isin(fuel_types)]
    if models:
        dff = dff[dff['modeldescription'].isin(models)]
    trend = dff.groupby(dff['contractstartdate'].dt.to_period('M'))['totalcapitalamount'].sum().reset_index()
    trend['contractstartdate'] = trend['contractstartdate'].astype(str)
    return px.line(trend, x='contractstartdate', y='totalcapitalamount', title='Financial Trends Over Time')

@app.callback(Output('heatmap', 'figure'), Input('heatmap', 'id'))
def display_heatmap(_):
    heatmap_data = df.groupby(['dealerbpid', 'start_quarter'])['totalcapitalamount'].sum().unstack(fill_value=0)
    heatmap_focus = heatmap_data[[q for q in heatmap_data.columns if str(q).endswith('Q1') or str(q).endswith('Q4')]]
    fig = go.Figure(data=go.Heatmap(z=heatmap_focus.values, x=[str(c) for c in heatmap_focus.columns], y=heatmap_focus.index, colorscale='Viridis'))
    fig.update_layout(title='Dealer-level Q4 vs Q1 Heatmap')
    return fig

@app.callback([Output('variance-table', 'data'), Output('variance-table', 'columns')], Input('variance-table', 'id'))
def display_variance(_):
    heatmap_data = df.groupby(['dealerbpid', 'start_quarter'])['totalcapitalamount'].sum().unstack(fill_value=0)
    heatmap_focus = heatmap_data[[q for q in heatmap_data.columns if str(q).endswith('Q1') or str(q).endswith('Q4')]]
    variance_df = heatmap_focus.copy()
    variance_df['variance'] = variance_df.max(axis=1) - variance_df.min(axis=1)
    top_variance = variance_df.sort_values('variance', ascending=False).head(10).reset_index()
    columns = [{'name': col, 'id': col} for col in top_variance.columns]
    return top_variance.to_dict('records'), columns

@app.callback(Output('car-model-analysis', 'figure'), Input('car-model-analysis', 'id'))
def display_car_model(_):
    car_model_analysis = df.groupby(['modeldescription', 'fueltypecode'])['totalcapitalamount'].sum().reset_index()
    return px.bar(car_model_analysis, x='modeldescription', y='totalcapitalamount', color='fueltypecode', title='Car Model-Level Analysis by Fuel Type')

@app.callback(Output('revenue-analysis', 'figure'), Input('revenue-analysis', 'id'))
def display_revenue(_):
    revenue_analysis = df.groupby('dealerbpid')['totalcapitalamount'].sum().reset_index()
    return px.bar(revenue_analysis.sort_values('totalcapitalamount', ascending=False), x='dealerbpid', y='totalcapitalamount', title='Revenue Analysis by Dealer')

@app.callback(Output('monthly-patterns', 'figure'), Input('monthly-patterns', 'id'))
def display_monthly(_):
    monthly = df.groupby('month')['totalcapitalamount'].sum().reset_index()
    monthly['month'] = monthly['month'].astype(str)
    return px.bar(monthly, x='month', y='totalcapitalamount', title='Seasonal Patterns (Monthly Revenue)')

@app.callback(Output('quarterly-patterns', 'figure'), Input('quarterly-patterns', 'id'))
def display_quarterly(_):
    quarterly = df.groupby('start_quarter')['totalcapitalamount'].sum().reset_index()
    quarterly['start_quarter'] = quarterly['start_quarter'].astype(str)
    return px.bar(quarterly, x='start_quarter', y='totalcapitalamount', title='Seasonal Patterns (Quarterly Revenue)')

if __name__ == '__main__':
    app.run_server(debug=True)
