from Status2.Crypto_Analytics.src.santiment_API_data import *
from Status2.Crypto_Analytics.src.Utilities import *
import dash
import dash_html_components as html
import dash_core_components as dcc
import pathlib


Config = Configuration(str(pathlib.Path(__file__).parent.absolute()) + "\config.ini")
Config.log_config(Config.get_config())


santimet_slugs = Config.getlist("COIN", "coins.main")
coin_comparisons = Config.getlist("COIN", "coins.metric_comparisons")

list_metrics = Config.getlist("METRICS", "metrics.main")
list_output_columns = Config.getlist("METRICS", "metrics.column_output")

list_metrics_comparisons = Config.getlist("METRICS", "metrics.comparisons")

list_metrics_header = Config.getlist("METRICS", "metrics.header")

metrics = dict(zip(list_metrics,list_output_columns))
metric_comparison = list_metrics_comparisons
metrics_header = dict(zip(list_metrics, list_metrics_header))

app = dash.Dash()


i = 0

children = []
df_to_update = pd.DataFrame(columns=["date", "metric", "value"])

for metric in metrics.keys():
    print(metric)
    [figs, df_to_update] = get_data_for_dash_from_santAPI(santimet_slugs, metric,
                                                          metrics[metric], 90, 28, df_to_update, coin_comparisons)

    new_child = html.Div([
            html.Div([
                html.Div([
                    html.Div(metrics_header[metric], style={'color': 'blue', 'font-size':'300%'}),
                    dcc.Graph(id='g1'+ str(i), figure=figs)
                ], className="six columns"),

                ], className="row" + str(i))

                ])

    i = i + 1

    children.append(new_child)


for coin in coin_comparisons:
    figs_coin_comparisons = []
    df_to_update_coin = df_to_update[df_to_update.coin == coin]
    i = i + 1
    metric_comparison_list = []
    for metric in metric_comparison:
        print(metric)
        try:
            fig = get_data_for_DASH_vsSingleMetric_RW(df_to_update_coin, metric, 28)
            figs_coin_comparisons.append(fig)
            metric_comparison_list.append(metrics_header[metric])
        except:
            continue

    figs = combine_plots_in_subplot(figs_coin_comparisons, 1, len(metric_comparison_list), metric_comparison_list)
    new_child = html.Div([
            html.Div([
                html.Div([
                    html.Div(coin.capitalize() + " Metric Correlation vs Other Metrics",
                             style={'color': 'blue', 'font-size' : '300%'}),
                    dcc.Graph(id='g1' + str(i), figure=figs)
                ], className="six columns"),

                ], className="row" + str(i))

                ])

    children.append(new_child)

    #df_to_update_coin = df_to_update_coin.pivot(index="date", columns="metric", values="value")

    #fig = create_heatmap_pp_score(df_to_update_coin)

    #new_child2 = html.Div([
    #        html.Div([
    #            html.Div([
    #                html.Div("PP Score Matrix Status", style={'color': 'blue', 'font-size' : '300%'}),
    #                dcc.Graph(id='g1pps' + str(i), figure=fig)
    #            ], className="six columns"),
    #
    #            ], className="rowg1pps")
    #
    #            ])

    #children.append(new_child2)

app.layout = html.Div(children=children)


if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)