import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

TABLE_PAGE_SIZE = 20

class AppBuilder(object):
    def __init__(self, app, df, title = '', subtitle = ''):
        # legends for the columns
        self.legends = {
            'sub_metering_1': 'Dishwasher, oven and microwave',
            'sub_metering_2': ('Washing-machine, tumble-drier, '
                               'refrigerator and one light'),
            'sub_metering_3': 'Water-heater and air-conditioner',
            'not_sub_metering': 'Other usage',
        }
        self.meters = ['sub_metering_1', 'sub_metering_2', 'sub_metering_3',
                       'not_sub_metering']

        # keep a copy of the original one for resampling purposes
        self._original_df = df.copy()
        self.df = df

        # assign attributes
        self.app = app
        self.title = title
        self.subtitle = subtitle

    @property
    def df_table(self):
        return self._df_table

    @df_table.setter
    def df_table(self, value):
        # create df_table, which we use for displaying the data_table
        # we need some work, considering tht date_time is the index and doesn't
        # show up in df.columns
        df_table = value.copy()
        df_table = df_table[self.meters]
        df_table.columns = [self.legends[c] for c in df_table]
        df_table['Date'] = df_table.index
        cols = df_table.columns
        cols = list(cols[-1:]) + list(cols[:-1])
        self._df_table = df_table[cols]

    @property
    def df(self):
        return self._df

    @df.setter
    def df(self, value):
        self._df = value
        self.df_table = value

    def run(self):
        # build the layout so we can add the callbacks
        self.app.layout = self.build_app_layout()
        self.add_table_updater_callback()
        self.add_chart_content_callback()

        # run development server
        self.app.run_server(debug=True)

    def add_chart_content_callback(self):
        @self.app.callback(Output('charts-content', 'children'),
                           [Input('average-options', 'value'),
                           Input('charts-tabs', 'value')])
        def render_content(avg_by, tab):
            print('''inside callback
                    avg_by: {}
                    chart_tab: {}
                  '''.format(avg_by, tab))
            self.df = self._original_df.resample(avg_by).mean()
            return getattr(self, tab)()

    def add_table_updater_callback(self):
        @self.app.callback(
            Output('datatable-paging', 'data'),
            [Input('datatable-paging', 'pagination_settings')])
        def table_updater(pagination_settings):
            return self.df_table.iloc[
                (
                    pagination_settings['current_page']*
                    pagination_settings['page_size']
                ):
                (
                    (pagination_settings['current_page'] + 1)*
                    pagination_settings['page_size']
                )
            ].to_dict('rows')

    def build_title(self):
        return html.Div([
            html.H1(
                self.title,
                className='title'
            ),
            html.P(
                self.subtitle,
                className='subtitle'
            )])

    def build_side_panel(self):
        return html.Div([
            html.Label('Average by'),
            dcc.RadioItems(id='average-options',
                options=[
                    {'label': 'Hour', 'value': 'H'},
                    {'label': 'Day', 'value': 'D'},
                    {'label': 'Week', 'value': 'W'},
                    {'label': 'Month', 'value': 'M'},
                    #{'label': 'Year', 'value': 'Y'}
                ], value = 'H'
            )
        ], className='column is-one-fifth')

    def get_chart_layout(self):
        return go.Layout(
            xaxis={'type': 'date', 'title': 'Date'},
            yaxis={'title': 'Energy consumption'},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend={'x': 0, 'y': 1},
            hovermode='closest')

    def build_chart_line(self, col):
        return go.Line(
            x = self.df.index,
            y = getattr(self.df, col),
            name = self.legends[col]
        )

    def build_charts(self, cols):
        return dcc.Graph(
            figure={
                'data': [self.build_chart_line(c) for c in cols],
                'layout': self.get_chart_layout()
            }
        )

    def build_chart_all_meters(self):
        return self.build_charts(self.meters)

    def build_chart_sub_metering_1(self):
        return self.build_charts(['sub_metering_1'])

    def build_chart_sub_metering_2(self):
        return self.build_charts(['sub_metering_2'])

    def build_chart_sub_metering_3(self):
        return self.build_charts(['sub_metering_3'])

    def build_chart_not_sub_metering(self):
        return self.build_charts(['not_sub_metering'])

    def build_graph_area(self):
        all_charts = 'build_chart_all_meters'
        return html.Div([
            dcc.Tabs(id='charts-tabs', value=all_charts, children=[
                dcc.Tab(label='All meters', value=all_charts),
                dcc.Tab(label='Dishwasher, oven and microwave',
                        value='build_chart_sub_metering_1'),
                dcc.Tab(label=('Washing-machine, tumble-drier, '
                               'refrigerator and one light'),
                        value='build_chart_sub_metering_2'),
                dcc.Tab(label='Water-heater and air-conditioner',
                        value='build_chart_sub_metering_3'),
                dcc.Tab(label='Other usage',
                        value='build_chart_not_sub_metering')
            ]),
            html.Div(id='charts-content')
        ], className='column')

    def build_data_table(self):
        return dash_table.DataTable(
            id='datatable-paging',
            columns=[{'name': c, 'id': c} for c in self.df_table.columns],
            pagination_settings={
                'current_page': 0,
                'page_size': TABLE_PAGE_SIZE
            },
            pagination_mode='be',
            css=[{
                'selector': '.dash-cell div.dash-cell-value',
                'rule': ('display: inline; white-space: inherit;'
                         'overflow: inherit; text-overflow: inherit;')
            }],
            style_cell={
                'whiteSpace': 'no-wrap',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'maxWidth': 0,
            },
        )

    def build_app_layout(self):
        return html.Div([
            html.Section([
                html.Div([
                    self.build_title(),
                    html.Div([
                        self.build_side_panel(),
                        self.build_graph_area(),
                    ],
                             className='columns',
                             style={
                                 'marginTop': '2em'
                             }),
                    self.build_data_table()
                ], className='container'),
            ], className='section')
        ])

