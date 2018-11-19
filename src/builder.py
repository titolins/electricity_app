import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

TABLE_PAGE_SIZE = 20

class AppBuilder(object):
    def __init__(self, app, df, title = '', subtitle = ''):
        # legends for the columns
        self.legends = dict(
            sub_metering_1='Dishwasher, oven and microwave',
            sub_metering_2=('Washing-machine, tumble-drier, '
                            'refrigerator and one light'),
            sub_metering_3='Water-heater and air-conditioner',
            not_sub_metering='Other usage',
        )
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
    def df(self):
        return self._df

    @df.setter
    def df(self, value):
        self._df = value

    def run(self):
        # build the layout so we can add the callbacks
        self.app.layout = self.build_app_layout()
        #self.add_table_updater_callback()
        self.add_main_content_callback()

        # run development server
        self.app.run_server(debug=True)

    def add_main_content_callback(self):
        @self.app.callback(Output('main-content', 'children'),
                           [Input('average-options', 'value'),
                           Input('charts-tabs', 'value')])
        def render_content(avg_by, tab):
            self.df = self._original_df.resample(avg_by).mean()
            return getattr(self, tab)()

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
                    dict(label='Hour', value='H'),
                    dict(label='Day', value='D'),
                    dict(label='Week', value='W'),
                    dict(label='Month', value='M'),
                    #dict(label='Year', value='Y')
                ], value = 'H'
            )
        ], className='column is-one-fifth')

    def get_chart_layout(self):
        return go.Layout(
            xaxis=dict(type='date',title='Date'),
            yaxis=dict(title='Energy consumption'),
            margin=dict(l=40, b=40, t=10, r=10),
            legend=dict(x=0,y=1),
            hovermode='closest')

    def build_chart_line(self, col):
        return go.Line(
            x = self.df.index,
            y = getattr(self.df, col),
            name = self.legends[col]
        )

    def build_charts(self, cols):
        return dcc.Graph(
            figure=dict(
                data=[self.build_chart_line(c) for c in cols],
                layout=self.get_chart_layout()
            )
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

    def build_tabs(self):
        all_charts = 'build_chart_all_meters'
        return dcc.Tabs(id='charts-tabs', value=all_charts, children=[
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
        ])

    def build_main_area(self):
        return html.Div([
            self.build_side_panel(),
            html.Div([
                self.build_tabs(),
                html.Div(id='main-content')
            ], className='column')
        ], className='columns', style=dict(marginTop='2em'))

    def build_app_layout(self):
        return html.Div([
            html.Section([
                html.Div([
                    self.build_title(),
                    self.build_main_area()
                ], className='container'),
            ], className='section')
        ])

