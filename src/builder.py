import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

import datetime

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
                    month=6),
                order=1,
            ),
            summer=dict(
                start=dict(
                    day=21,
                    month=6),
                end=dict(
                    day=21,
                    month=9),
                order=2,
            ),
            fall=dict(
                start=dict(
                    day=22,
                    month=9),
                end=dict(
                    day=20,
                    month=12),
                order=3,
            ),
            winter=dict(
                start=dict(
                    day=21,
                    month=12),
                end=dict(
                    day=19,
                    month=3),
                order=4,
            )
        )

        self.tabs = dict(
            all_data=dict(
                name='All data',
                value='build_main_chart_area',
            ),
            season_data=dict(
                name='By Season',
                value='build_seasonal_area',
            )
        )

        self.season_charts = dict(
            all_data_by_season='build_all_data_seasonal_chart',
            yearly_data_by_season='build_yearly_data_seasonal_chart'
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

        # add callbacks
        self.add_main_content_callback()
        self.add_tabs_callback()
        self.add_seasonal_content_callback()
        # run development server
        self.app.run_server(debug=debug)

    def add_tabs_callback(self):
        @self.app.callback(Output('main-area', 'children'),
                           [Input('charts-tabs', 'value')])
        def render_content(tab):
            return getattr(self, self.tabs[tab]['value'])()

    def add_seasonal_content_callback(self):
        @self.app.callback(Output('seasonal-chart-area', 'children'),
                           [Input('seasonal-options', 'value'),
                            Input('seasonal-mode', 'value')])
        def render_seasonal_content(option, mode):
            return getattr(self, self.season_charts[option])(mode)

    def add_main_content_callback(self):
        @self.app.callback(Output('main-tab-content', 'children'),
                           [Input('resample-button', 'n_clicks')],
                           [State('resample-frequency', 'value'),
                            State('average-options', 'value')])
        def render_content(n_clicks, resample_freq, avg_by):
            self.df = self._original_df.resample(
                '{}{}'.format(resample_freq,avg_by)).mean()
            return self.build_chart_all_meters()

    def _get_season_dates_for_x(self, season, x):
        return (datetime.date(day=self.seasons[season]['start']['day'],
                              month=self.seasons[season]['start']['month'],
                              year=(x.year-1) if (season == 'winter' and \
                                                  x.month <= 3) else \
                                    x.year),
                datetime.date(day=self.seasons[season]['end']['day'],
                              month=self.seasons[season]['end']['month'],
                              year=(x.year+1) if (season == 'winter' and \
                                                  x.month == 12) else \
                                    x.year))

    def _x_in_season(self, season, x):
        x_date = datetime.date(day=x.day, month=x.month, year=x.year)
        s_date, e_date = self._get_season_dates_for_x(season, x)
        return (x_date >= s_date and x_date <= e_date)

    def group_by_season(self):
        return self.df.groupby(
            by=lambda x: [s
                          for s in list(self.seasons)
                          if self._x_in_season(s,x)][0])

    def group_by_year_and_season(self):
        return self.df.groupby(
            by=lambda x: ['{} {}'.format(s,x.year)
                          for s in list(self.seasons)
                          if self._x_in_season(s,x)][0])

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
            html.H2('Average by', className='subtitle',
                    style=dict(marginTop='1.5em')),
            html.Div([
                html.P(
                    dcc.Input(
                        id='resample-frequency',
                        type='number',
                        step='1',
                        value='1',
                        min=1,
                        style=dict(
                            marginBottom='.5em',
                            width='100%',
                        )
                    ),
                    className='control', style=dict(width='40%')),
                html.P(
                    dcc.Dropdown(id='average-options',
                        options=[
                            dict(label='Hour', value='H'),
                            dict(label='Day', value='D'),
                            dict(label='Week', value='W'),
                            dict(label='Month', value='M'),
                        ],
                        value = 'H',
                        style=dict(
                            marginBottom='.5em',
                            width='100%',
                        )
                    ),
                    className='control', style=dict(width='60%')),
            ], className='field is-grouped'),
            html.P(
                html.Button(id='resample-button', n_clicks=0,
                            children='Resample data',
                            className='button is-primary'),
                className='control'),
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
        return html.Div([
            dcc.Graph(
                figure=dict(
                    data=[self.build_chart_line(c) for c in cols],
                    layout=self.get_chart_layout()
                ),
                style=dict(marginTop='1.5em')
            )
        ])

    def build_chart_all_meters(self):
        return self.build_charts(self.feature_cols)

    def build_tabs(self):
        return dcc.Tabs(
            id='charts-tabs',
            value=list(self.tabs)[0],
            children=[
                dcc.Tab(label=self.tabs[t]['name'],
                        value=t)
                        for t in self.tabs
        ], style=dict(marginTop='2em'))

    def build_main_chart_area(self):
        return html.Div([
            self.build_side_panel(),
            html.Div([
                html.Div(id='main-tab-content')
            ], className='column')
        ], className='columns')

    def build_bar_layout(self, mode):
        return go.Layout(
            barmode=mode,
            legend=self.get_legend_layout(x_pos=.5),
            height=550
        )

    def _build_seasonal_chart(self, sort_f, s_df_f, mode):
        s_df = s_df_f().sum()[list(self.feature_cols)]
        sorted_cols=sorted(s_df.index, key=sort_f)
        s_df = s_df.reindex(sorted_cols)
        return html.Div([dcc.Graph(
            figure=go.Figure(
                data=[go.Bar(
                    x=[s.capitalize() for s in s_df.index],
                    y=s_df[c],
                    name=self.feature_cols[c]['legend'],
                    marker=dict(color=self.feature_cols[c]['color']))
                      for c in list(self.feature_cols)],
                layout=self.build_bar_layout(mode))),
        ])

    def build_all_data_seasonal_chart(self, mode):
        return self._build_seasonal_chart(lambda x:self.seasons[x]['order'],
                                          self.group_by_season,
                                          mode)

    def build_yearly_data_seasonal_chart(self, mode):
        return self._build_seasonal_chart(
            lambda x:(int(x.split()[1]), self.seasons[x.split()[0]]['order']),
            self.group_by_year_and_season,
            mode
        )

    def build_seasonal_sidebar(self):
        return html.Div([
            html.H2('Group by', className='subtitle',
                    style=dict(marginTop='1.5em')),
            dcc.RadioItems(
                id='seasonal-options',
                value='all_data_by_season',
                options=[
                    dict(
                        label='Season only',
                        value='all_data_by_season',
                    ),
                    dict(
                        label='Year and season',
                        value='yearly_data_by_season',
                    ),
                ]
            ),
            html.H2('Bar mode', className='subtitle',
                    style=dict(marginTop='1.5em')),
            dcc.RadioItems(
                id='seasonal-mode',
                value='group',
                options=[
                    dict(
                        label='Grouped',
                        value='group',
                    ),
                    dict(
                        label='Stacked',
                        value='stack',
                    ),
                ]
            ),
        ], className='column is-one-fifth')

    def build_seasonal_area(self):
        return html.Div([
            self.build_seasonal_sidebar(),
            html.Div(id='seasonal-chart-area', className='column')
        ], className='columns')

    def build_app_layout(self):
        return html.Div([
            html.Section([
                html.Div([
                    self.build_title(),
                    self.build_tabs(),
                    html.Div(id='main-area')
                ], className='container'),
            ], className='section'),
        ])

