# -*- coding: utf-8 -*-
import dash

from data import load_data, load_resampled_data_by_month
from builder import AppBuilder

external_stylesheets = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
    'https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.2/css/bulma.min.css'
]

def build():
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets,
                    meta_tags=[
                    {
                        'name':'viewport',
                        'content':'width=device-width, initial-scale=1'
                    },
    ])
    app.config['suppress_callback_exceptions'] = True
    df = load_data()
    return AppBuilder(
        app,
        df,
        'Task 3.2 - Ubiqum',
        'Energy consumption')

if __name__ == '__main__':
    build().run()
