import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

import datetime

TABLE_PAGE_SIZE = 20

class AppBuilder(object):
    def __init__(self, app, df, title = '', subtitle = '', env = 'dev'):
        # environment
        self.env = env
        # legends for the columns
        self.feature_cols = dict(
            sub_metering_1=dict(
                legend='Dishwasher, oven and microwave',
                color='#FFCCCC'
            ),
            sub_metering_2=dict(
                legend=('Washing-machine, tumble-drier, '
                        'refrigerator and one light'),
                color='#7F7F7F'
            ),
            sub_metering_3=dict(
                legend='Water-heater and air-conditioner',
                color='#17BECF'
            ),
            not_sub_metering=dict(
                legend='Other usage',
                color='#B3FFB3'
            )
        )
        self.seasons = dict(
            spring=dict(
                start=dict(
                    day=20,
                    month=3),
                end=dict(
                    day=20,
                    month=6)),
            summer=dict(
                start=dict(
                    day=21,
                    month=6),
                end=dict(
                    day=21,
                    month=9)),
            fall=dict(
                start=dict(
                    day=22,
                    month=9),
                end=dict(
                    day=20,
                    month=12)),
            winter=dict(
                start=dict(
                    day=21,
                    month=12),
                end=dict(
                    day=19,
                    month=3))
        )

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
        debug = True if self.env is 'dev' else False
        # build the layout so we can add the callbacks
        self.app.layout = self.build_app_layout()
        #self.add_table_updater_callback()
        self.add_main_content_callback()
        # run development server
        self.app.run_server(debug=debug)

    def add_main_content_callback(self):
        @self.app.callback(Output('main-content', 'children'),
                           [Input('average-options', 'value'),
                           Input('charts-tabs', 'value')])
        def render_content(avg_by, tab):
            self.df = self._original_df.resample(avg_by).mean()
            return getattr(self, tab)()

    def group_by_season(self):
        def group_f(x):
            x_date = datetime.date(day=x.day, month=x.month, year=x.year)
            for s in self.seasons.keys():
                s_date = datetime.date(day=self.seasons[s]['start']['day'],
                                       month=self.seasons[s]['start']['month'],
                                       year=(x.year-1) if \
                                            (
                                                s == 'winter' and \
                                                x.month <= 3
                                            ) else \
                                            x.year)
                e_date = datetime.date(day=self.seasons[s]['end']['day'],
                                       month=self.seasons[s]['end']['month'],
                                       year=(x.year+1) if \
                                            (
                                                s == 'winter' and \
                                                x.month == 12
                                            )  else \
                                            x.year)
                if x_date >= s_date and x_date <= e_date:
                    return s
        return self.df.groupby(by=group_f)

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

    def get_legend_layout(self, x_pos=.55):
        return dict(
            x=x_pos,
            y=1,
            bgcolor='rgba(255,255,255,0)',
            font=dict(
                size=14
            )
        )

    def get_chart_layout(self):
        return go.Layout(
            height=650,
            xaxis=dict(
                type='date',
                title='Date',
                rangeselector=dict(
                    buttons=list([
                        dict(count=1,
                             label='1m',
                             step='month',
                             stepmode='backward'),
                        dict(count=6,
                             label='6m',
                             step='month',
                             stepmode='backward'),
                        dict(count=1,
                             label='1y',
                             step='year',
                             stepmode='backward'),
                        dict(step='all')
                    ])
                ),
                rangeslider=dict(
                    visible=True
                )
            ),
            yaxis=dict(title='Energy consumption'),
            margin=dict(l=40, b=40, t=10, r=10),
            legend=self.get_legend_layout(),
            hovermode='closest')

    def build_chart_line(self, col):
        return go.Scatter(
            x=self.df.index,
            y=getattr(self.df, col),
            name=self.feature_cols[col]['legend'],
            line=dict(color=self.feature_cols[col]['color'])
        )

    def build_charts(self, cols):
        return dcc.Graph(
            figure=dict(
                data=[self.build_chart_line(c) for c in cols],
                layout=self.get_chart_layout()
            )
        )

    def build_chart_all_meters(self):
        return self.build_charts(self.feature_cols)

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
        ], style=dict(marginTop='2em'))

    def build_main_chart_area(self):
        return html.Div([
            self.build_side_panel(),
            html.Div([
                html.Div(id='main-content')
            ], className='column')
        ], className='columns', style=dict(marginTop='1em'))

    def build_bar_layout(self):
        return go.Layout(
            barmode='group',
            legend=self.get_legend_layout(x_pos=.5)
        )

    def build_seasonal_area(self):
        s_df = self.group_by_season().mean()[list(self.feature_cols.keys())]
        return html.Div([
            html.Div([
                '',
            ], className='column is-one-fifth'),
            html.Div([dcc.Graph(
                figure=go.Figure(
                    data=[go.Bar(
                        x=[s.capitalize() for s in self.seasons.keys()],
                        y=s_df[c],
                        name=self.feature_cols[c]['legend'],
                        marker=dict(color=self.feature_cols[c]['color']))
                          for c in s_df],
                    layout=self.build_bar_layout())),
            ], className='column')
        ], className='columns')

    def build_app_layout(self):
        return html.Div([
            html.Section([
                html.Div([
                    self.build_title(),
                    self.build_tabs(),
                    self.build_main_chart_area()
                ], className='container'),
            ], className='section'),
            html.Section([
                html.Div([
                    html.H3('Seasonal chart', className='title'),
                    self.build_seasonal_area(),
                ], className='container')
            ], className='section')
        ])

