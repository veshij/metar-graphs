import csv
from metar import Metar
import datetime
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.palettes import Plasma11 as palette
from bokeh.io import show
from bokeh.layouts import column
import pandas as pd


def main():
    df = get_dataset()
    df['year'] = df['date'].dt.year
    df['dayofyear'] = pd.to_datetime(df['date'].dt.dayofyear-1, unit='D', origin=str(2021))

    # pick max per day
    df = df.groupby([pd.Grouper(freq="1d", key="date")]).max()

    window = 7
    df['wind_avg'] = df.iloc[:, 0].rolling(window=window).mean()
    df['wind_gustavg'] = df.iloc[:, 1].rolling(window=window).mean()
    df['gust_factor'] = df.iloc[:, 2].rolling(window=window).mean()

    print(df)
    show(column(
        make_plot(df, "wind_avg", "average winds"),
        make_plot(df, "wind_gustavg", "gusts"),
        make_plot(df, "gust_factor", "gust factor"),
    ))


def get_dataset():
    data = {'date': [],
            'wind_speed': [], 'wind_gusts': [], 'gusts': []}

    # https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=SQL&data=all&year1=2000&month1=1&day1=1&year2=2021&month2=6&day2=25&tz=Etc%2FUTC&format=onlycomma&latlon=no&elev=no&missing=M&trace=T&direct=no&report_type=1&report_type=2
    with open("metar.csv", "r") as fh:
        reader = csv.reader(fh)
        # skip header
        next(reader)

        for row in reader:
            # 2021-06-24 13:55
            datetime_object = datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M")

            try:
                metar_data = Metar.Metar(row[-1])
            except:
                continue

            wind_speed = 0
            if metar_data.wind_speed:
                wind_speed = metar_data.wind_speed.value(units="KT")
            wind_gusts = wind_speed
            if metar_data.wind_gust:
                wind_gusts = metar_data.wind_gust.value(units="KT")

            # mostly parse issues
            if wind_speed > 40 or wind_gusts > 40:
                continue

            data["date"].append(datetime_object)
            data["wind_speed"].append(wind_speed)
            data["wind_gusts"].append(wind_gusts)
            data["gusts"].append(wind_gusts-wind_speed)

    return pd.DataFrame(data=data)


def make_plot(dataset, column, title):
    plot = figure(height=800, width=1024, x_axis_type="datetime")
    plot.title.text = f"KSQL METAR: {title}"

    colors = iter(palette)
    for year in (2015, 2016, 2017, 2018, 2019, 2020, 2021):
        source = ColumnDataSource(dataset[dataset['year'] == year])
        width = 1
        if year == 2021:
            width = 2
        plot.line(x="dayofyear", y=column, source=source,
                  color=next(colors), width=width, legend_label=f"{year}, KT.")

    plot.legend.location = "top_left"
    plot.legend.click_policy = "hide"

    return plot


if __name__ == "__main__":
    main()
