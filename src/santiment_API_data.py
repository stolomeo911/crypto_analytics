import san
import requests
from pandas.io.json import json_normalize
import pandas as pd
import numpy as np
import os
from google.cloud import bigquery
import pandas as pd
import datetime
import datetime
import plotly.express as px
import plotly.graph_objects as go
import pytz
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
import ppscore as pps


def create_plotly_line_from_df_columns(df):
    fig = go.Figure()

    for column in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[column],
                                 name=column,
                                 line_shape='spline'))

    fig.update_layout(
        autosize=False,
        width=1000,
        height=600,
        plot_bgcolor="black",
        xaxis={'showgrid': False},
        yaxis={'showgrid': False})

    return fig


def create_heatmap_from_df_corr_matrix(df, date_filter):
    df_daily_changesL28D = df[df.index > date_filter]

    z = df_daily_changesL28D.corr().round(2).values

    x = df_daily_changesL28D.columns.to_list()
    y = df_daily_changesL28D.columns.to_list()

    fig2 = ff.create_annotated_heatmap(z, x, y)

    fig2.update_layout(
        autosize=False,
        width=600,
        height=600, )

    return fig2


def combine_plots_in_subplot(figs, row, cols, subplot_titles):
    subplot = make_subplots(
        rows=row, cols=cols,
        subplot_titles=subplot_titles,

        horizontal_spacing=0.05
    )

    i = 1
    layouts = []

    for fig in figs:
        if len(fig.data) == 1:
            subplot.add_trace(fig.data[0], row=row, col=i)
        else:
            for j in range(len(fig.data)):
                subplot.add_trace(fig.data[j], row=row, col=i)
        i = i + 1
    subplot.update_layout(autosize=False, height=600, width=5000)

    # subplot.layout.update(layouts)
    return subplot


def create_rolling_corrXY_from_df(df, columnX, columnY):
    df_XY = df[[columnX, columnY]]
    return df_XY.rolling(28).corr(df_XY[columnY])[columnX].dropna()


def create_heatmap_pp_score(df):
    z = pps.matrix(df).round(2).values

    x = df.columns.to_list()
    y = df.columns.to_list()

    fig2 = ff.create_annotated_heatmap(z, x, y)

    fig2.update_layout(
        autosize=False,
        width=600,
        height=600, )

    return fig2


def get_data_for_dash_from_santAPI(slugs, metric, output_column, num_days, rw, df_to_update, coin_comparisons):
    today = datetime.datetime.now().replace(tzinfo=pytz.utc)
    start_date = today - datetime.timedelta(num_days)

    date_format = "%Y-%m-%d"

    start_date_str = start_date.strftime(date_format)

    today_str = today.strftime(date_format)

    if "social_volume" not in metric and "top_holders_percent_of_total_supply" not in metric:
        tmp_df = san.get(metric + "/status",
                         from_date=start_date_str,
                         to_date=today_str,
                         interval="1d")
    elif "social_volume" in metric:
        metric1, arg = metric.split("-")
        tmp_df = san.get(
            metric1 + "/" + "status",
            from_date=start_date_str,
            to_date=today_str,
            interval="1d",
            social_volume_type=arg
        )
    elif "top_holders_percent_of_total_supply" in metric:
        metric1, arg = metric.split("-")

        tmp_df = san.get(metric1 + "/status",
                         number_of_holders = 100,
                         from_date=start_date_str,
                         to_date=today_str,
                         interval="1d")
    else:
        raise NotImplementedError

    df_timeseriesmetric = pd.DataFrame(columns=slugs, index=tmp_df.index)

    df_timeseriesmetric.loc[tmp_df.index, "status"] = tmp_df[output_column]

    for coin in slugs:
        print(coin)
        if  "social_volume" not in metric and "top_holders_percent_of_total_supply" not in metric:
            tmp_df = san.get(metric + "/" + coin,
                             from_date=start_date_str,
                             to_date=today_str,
                             interval="1d")
        elif "social_volume" in metric:
            metric1, arg = metric.split("-")
            try:
                tmp_df = san.get(
                    metric1 + "/" + coin,
                    from_date=start_date_str,
                    to_date=today_str,
                    interval="1d",
                    social_volume_type=arg
                )
            except:
                continue
        elif "top_holders_percent_of_total_supply" in metric:
            metric1, arg = metric.split("-")
            try:
                tmp_df = san.get(metric1 + "/" + coin,
                                 number_of_holders=100,
                                 from_date=start_date_str,
                                 to_date=today_str,
                                 interval="1d")
            except:
                continue
        else:
            raise NotImplementedError
        try:
            df_timeseriesmetric.loc[tmp_df.index, coin] = tmp_df[output_column]
        except:
            continue

    df_timeseriesmetric = df_timeseriesmetric.dropna(axis=1, how="all")

    df_daily_changes = df_timeseriesmetric.pct_change(1)
    df_daily_changes = df_daily_changes.dropna(axis=1, how="all")
    fig1 = create_plotly_line_from_df_columns(df_daily_changes)

    fig2 = create_heatmap_from_df_corr_matrix(df_daily_changes, today - datetime.timedelta(28))
    fig3 = create_heatmap_from_df_corr_matrix(df_daily_changes, today - datetime.timedelta(90))

    df_rolling_window = pd.DataFrame(columns=df_daily_changes.columns, index=df_daily_changes.iloc[rw:].index)
    coins = list(df_rolling_window.columns.values)
    coins.remove("status")

    for coin in coins:
        tmp_df = create_rolling_corrXY_from_df(df_daily_changes, "status", coin)

        df_rolling_window.loc[tmp_df.index, coin] = tmp_df.values

    fig4 = create_plotly_line_from_df_columns(df_rolling_window)

    figs = [fig1, fig2, fig3, fig4]

    subplot = combine_plots_in_subplot(figs, 1, 5, ["% Returns", "Corr Matrix L28D", "Corr Matrix L90D",
                                                 "Correlation vs Status Over Time"])

    for coin in coin_comparisons:
        df_for_update = pd.DataFrame(columns=["coin", "date", "metric", "value"])

        try:
            df_daily_changes_coin = df_daily_changes[coin]

            df_for_update["date"] = df_daily_changes_coin.index
            df_for_update["coin"] = coin

            df_for_update["metric"] = metric

            df_for_update["value"] = df_daily_changes_coin.values

            df_to_update = df_to_update.append(df_for_update)
        except:
            continue

    return [subplot, df_to_update]


def get_data_for_DASH_vsSingleMetric_RW(df, base_metric, rw):
    df_pivot = df.pivot(index="date", columns="metric", values="value")

    metric_list = list(df_pivot.columns.values)
    metric_list.remove(base_metric)

    df_rolling_window = pd.DataFrame(columns=metric_list, index=df_pivot.iloc[rw:].index)

    for metric in metric_list:
        tmp_df = create_rolling_corrXY_from_df(df_pivot, base_metric, metric)
        df_rolling_window.loc[tmp_df.index, metric] = tmp_df.values

    fig = create_plotly_line_from_df_columns(df_rolling_window)

    return fig

