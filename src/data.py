#!/usr/bin/python
from os import path

import pandas as pd
import numpy as np

#from pyramid.arima import auto_arima

#from statsmodels.graphics.tsaplots import plot_acf
#from statsmodels.graphics.tsaplots import plot_pacf

BASE_PATH = '/mnt/files/Documents/Ubiqum/Task3/2/data/'
DATA_FILE = 'household_power_consumption.txt'
#PARSED_DATA_FILE = 'full_data.csv'
PARSED_DATA_FILE = 'hourly.csv'
RESAMPLED_MONTH_DATA_FILE = 'resampled_month.csv'

#DATA_FILE_PATH = path.join(BASE_PATH, DATA_FILE)

BG_COLOR = '#283A54'
LEGEND_FONT_SIZE = 12

CONVERT_COLS = [
    ('Global_active_power', 'to_numeric'),
    ('Global_reactive_power', 'to_numeric'),
    ('Voltage', 'to_numeric'),
    ('Global_intensity', 'to_numeric'),
    ('Sub_metering_1', 'to_numeric'),
    ('Sub_metering_2', 'to_numeric'),
    ('Sub_metering_3', 'to_numeric')
]

def get_file_path(f):
    return path.join(BASE_PATH, f)

def load_data():
    return pd.read_csv(get_file_path(PARSED_DATA_FILE),
                       parse_dates=['Date_Time'],
                       infer_datetime_format=True, index_col = 'Date_Time')

def parse_raw_data():
    df = pd.read_csv(get_file_path(DATA_FILE), sep=';',
                     parse_dates=[['Date', 'Time']],
                     infer_datetime_format=True, index_col = 'Date_Time')
    # convert to numeric
    for (col, convert_f) in CONVERT_COLS:
        df[col] = getattr(pd, convert_f)(df[col], errors='coerce')

    # lower case columns
    df.columns = [c.lower() for c in df]
    # create new columns
    # create global_apparent_energy by summing active and reactive power
    df['global_apparent_power'] = (df['global_active_power'] +
                                   df['global_reactive_power']).values
    # 1.(global_active_power*1000/60 - sub_metering_1 - sub_metering_2 -
    # sub_metering_3) represents the active energy consumed every minute
    # (in watt hour) in the household by electrical equipment not measured in
    # sub-meterings 1, 2 and 3.
    df['not_sub_metering'] = (df.global_active_power
                              * (1000/60)
                              - df.sub_metering_1
                              - df.sub_metering_2
                              - df.sub_metering_3)
    df['total_sub_metering'] = (df.sub_metering_1
                                + df.sub_metering_2
                                + df.sub_metering_3)
    df['total_sub_no_sub_metering'] = (df.total_sub_metering
                                       + df.not_sub_metering)
    for c in df:
        df[c] = df[c].fillna(df[c].mean())
    return df

def load_resampled_data_by_month():
    return pd.read_csv(get_file_path(RESAMPLED_MONTH_DATA_FILE),
                       parse_dates=['Date_Time'],
                       infer_datetime_format=True, index_col = 'Date_Time')
