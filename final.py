"""
Colin Terilli
Section 7

https://uber-nyc-april.streamlit.app/ 
[DEPLOY]
Handled files by creating a folder for data which I pathed in the final program 
with a constant. Dependency is solved through the requirements.txt file which 
was uploaded to github and contains the required libraries needed to run the
program. Deployment issues were with the requirements.txt file as the file
did not run originally without them. 

uber-tlc-foil-response 

This program will display a streamlit website that shows statitics and analysis from
the April 2014 dataset. Displays include statitics, graphs, and maps. 

Used with Claude Opus 5.5
"""

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import pydeck as pdk

# Folder name
DATA_FOLDER = "Data/"

#CSV file name
APR_CSV = "uber-raw-data-apr14.csv"

#[DICT_DRIVEN]
# dictionary which keys are the base code and the values is another dictionary 
# which keys are color and name
# Example: 'B02512' maps to dictionary which give color '[230,159, 0]' (orange)
# and name 'Unter'
BASES = {
    'B02512':{'color': [230, 159, 0], 'name': 'Unter'},    # orange
    'B02598': {'color': [0, 114, 178], 'name': 'Hinter'},    # blue
    'B02617': {'color': [0, 158, 115], 'name': 'Weiter'},    # bluish green
    'B02682': {'color': [213, 94, 0], 'name': 'Schmecken'},     # vermillion
    'B02764': {'color': [204, 121, 167], 'name': 'Danach-NY'},  # reddish purple
    'B02765': {'color': [0, 128, 0], 'name': 'Grun'},           # green
    'B02835': {'color': [86, 180, 233], 'name': 'Driest'},   # sky blue
    'B02836': {'color': [0, 0, 0], 'name': 'Drinnen'},        # black
    }

@st.cache_data
def get_data():
    """
    Function will read CSV file and turn into dataframe, rewrite the Date/Time columns
    and add a base name and color column. 
    Inputs: none
    Outputs: APR (dataframe)
    """
    #[FILE_IO]
    # reads the april csv file and puts into a data frame named APR
    # add columns for name and color to the dataframe

    APR = pd.read_csv(DATA_FOLDER + APR_CSV)

    #[STR_CLEAN]
    # clean the date/time column to the pd.date_time format
    # tells pd where each part of the date sits in text
    # example: 4/1/2014 0:11:00 becomes 2014-04-01 00:11:00
    APR['Date/Time'] = pd.to_datetime(APR['Date/Time'], format='%m/%d/%Y %H:%M:%S')
    APR['name'] = APR['Base'].map(lambda b: BASES[b]['name'])
    APR['color'] = APR['Base'].map(lambda b: BASES[b]['color'])
    return APR

#--------------------------------------
def get_bases(df, d=None, key=None):
    """
    Gets user's selected bases through streamlit multiselect function
    Input: dataframe (APR), default setting ("all" or none), key (default = none)
    Output: Dataframe with selected bases and the select_bases list
    """
    #[AI_REWRITE]
    # Function was originally in main and only multiselect.
    # I rewrote it as its own function and added the default setting to it
    # I then added the if statement to check for the "d" setting (all or none)
    # then I had it return the df with selected bases and the selected bases list
    # later AI suggested I add the key part to it, which I did 

    #[REUSE_FUNC]
    # gets list of bases that the user wants for certain display (Scatter map, heatmap, graph)
    # Example get_bases(APR, d="all") will display a multiselect on streamlit
    # that defaults to all already selected. The user can select bases to show/not show

    #[LIST_COMP]
    # Creates a list of base names by looping through the BASES dictionary for base names
    # Example B02512':{'color': [230, 159, 0], 'name': 'Unter'} becomes 'Unter'
    base_options = [BASES[base]['name'] for base in BASES]
    if d == "all":
        d = base_options
    select_bases = st.multiselect("Select Bases", base_options, default=d, key=key)
    return df[df['name'].isin(select_bases)], select_bases

#------------------------------------------------
def hour_label(h):
    """
    Turns hours into AM PM format
    Input: hour
    Output: hour string (## 'AM') or (## 'PM')
    """
    return f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}"


@st.cache_data
def get_info():
    """
    Gets multiple statisics and df.
    Input: none
    Output: dictionary of (total, base, base_count, base_share, day, day_count, weekday, 
    weekday_avg, busy_hour, busy_hour_count, quiet_hour, quiet_hour_count, by_hour, by_weekday
    """
    df = get_data()

    base_counts = df['name'].value_counts() # number of pickups per base
    hour_counts = df["Date/Time"].dt.hour.value_counts() # number of pickups by the hour
    day_counts = df['Date/Time'].dt.date.value_counts().sort_index() # number of pickups by day


    # creates a pd series where dates are values
    # then converts the series to pandas date time values
    # then uses dt.day_name to turn dates into day names 
    weekdays = pd.to_datetime(pd.Series(day_counts.index)).dt.day_name().values 
    weekday_avg = day_counts.groupby(weekdays).mean()

    return {
        'total': len(df),
        'base': base_counts.idxmax(),
        'base_count': base_counts.max(),
        'base_share': base_counts.max() / len(df),
        'day': day_counts.idxmax(),
        'day_count': day_counts.max(),
        'weekday': weekday_avg.idxmax(),
        'weekday_avg': weekday_avg.max(),
        'busy_hour': hour_counts.idxmax(),
        'busy_hour_count': hour_counts.max(),
        'quiet_hour': hour_counts.idxmin(),
        'quiet_hour_count': hour_counts.min(),
        'by_hour': hour_counts,
        'by_weekday': weekday_avg,
    }

def time_bar_chart(f):
    """
    Creates 2 bar charts displayed one at time selected by radio by user. 
    1.) bar chart for total pickups by hour,
    2.) bar chart for average pickups by day of week.
    Inputs: dictionary (must contain keys 'by_hour' 'by_weekday')
    Outputs: 2 bar charts for most common hours and most common day (name)
    """
    choice = st.radio("Show pickups by", ["Hour of day", "Day of week"], horizontal=True, key="bar")

    if choice == "Hour of day":
        data = f['by_hour'].sort_index() # 0, 1, 2 ... 23 in order
        labels = [hour_label(h) for h in data.index] # 0 -> "12 AM"
        ylabel = "Total pickups in April"
    else:
        order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        data = f['by_weekday'].reindex(order) # put days in order by name
        labels = [day[:3] for day in order] # "Monday" -> "Mon"
        ylabel = "Average pickups per day"

    # busiest bar in orange, the rest in blue
    colors = ['#d55e00' if v == data.max() else '#0072b2' for v in data.values]

    fig, ax = plt.subplots(figsize=(10, 3.5)) 
    ax.bar(labels, data.values, color=colors)
    ax.set_title(f"Uber pickups by {choice.lower()}, April 2014", loc='left')
    ax.set_xlabel(choice)
    ax.set_ylabel(ylabel)
    if choice == "Hour of day":
        ax.tick_params(axis='x', rotation=45)     # 24 labels need room
    st.pyplot(fig)

    if choice == "Day of week":
        st.caption("Averages, not totals: April 2014 had five Tuesdays and Wednesdays "
                   "but only four of every other weekday, so totals would favor those two days.")
    else:
        st.caption("Each bar adds up every pickup in that hour across all 30 days of April.")


def overview():
    """
    Displays overview layout on streamlit
    Inputs: (none)
    Outputs: 2 rows + 3 columns of quick data/fact, and an interactive barchart
    """
    info = get_info()
    st.subheader("April 2014 at a glance")

    row1 = st.columns(3) # row 1, 3 columns
    row1[0].metric("Total pickups", f"{info['total']:,}")
    row1[0].caption("Every Uber pickup in NYC that month")
    row1[1].metric("Busiest base", info['base']) 
    row1[1].caption(f"{info['base_count']:,} pickups ({info['base_share']:.0%} of all)")
    row1[2].metric("Busiest single day", info['day'].strftime('%a, %b %d'))
    row1[2].caption(f"{info['day_count']:,} pickups")

    row2 = st.columns(3)
    row2[0].metric("Busiest day of the week", info['weekday'])
    row2[0].caption(f"{info['weekday_avg']:,.0f} pickups on an average {info['weekday']}")
    row2[1].metric("Busiest hour", hour_label(info['busy_hour']))
    row2[1].caption(f"{info['busy_hour_count']:,} pickups across the month")
    row2[2].metric("Quietest hour", hour_label(info['quiet_hour']))
    row2[2].caption(f"{info['quiet_hour_count']:,} pickups across the month") 

    time_bar_chart(info)

#------------------------------------------------
def line_chart(df, names):
    """
    Displays line chart of bases. Y axis is pickups and x axis in date/time.
    Users can select how it is displayed (hour, day, or week)
    Inputs: APR dataframe, names list
    Outputs: line chart 
    """
    if df.empty:
        st.info("No pickups to show. Select at least one base that has pickups in this time frame.")
        return 
    # Choose how to group
    left, right = st.columns(2)
    group_options = {"Hour": "h", "Day": "D", "Week": "W"}
    group_by = left.selectbox("Group by", list(group_options))

    # Choose the date range
    first = df['Date/Time'].min().date()
    last = df['Date/Time'].max().date()
    dates = right.date_input("Between", (first, last), min_value=first, max_value=last)
    if len(dates) != 2:
        return

    start = pd.Timestamp(dates[0])
    end = pd.Timestamp(dates[1]) + pd.Timedelta(days=1)
    df = df[(df['Date/Time'] >= start) & (df['Date/Time'] < end)]

    # count pickups per time
    counts = df.groupby([pd.Grouper(key='Date/Time', freq=group_options[group_by]), 'name']).size().unstack(fill_value=0)

    # Matplotlib takes colors 1 - 0
    colors = {b['name']: [c / 255 for c in b['color']] for b in BASES.values()}

    fig, ax = plt.subplots()
    for name in counts.columns:
        ax.plot(counts.index, counts[name], label=name, color=colors[name])
    ax.set_title(f"Uber pick ups per {group_by.lower()} by base, {dates[0]} - {dates[1]}", loc='left')
    ax.set_xlabel("Date")
    ax.set_ylabel("Pickups")
    ax.legend()
    fig.autofmt_xdate()  # tilt the dates so they don't overlap
    st.pyplot(fig)

    missing = [n for n in names if n not in df['name'].values]
    if missing:
        st.write("No pickups in this time frame for: " + ", ".join(missing))

#---------------------------------------

def scatterplotlay(df, view):
    """
    Displays a scatter plot over New York City based on user choice of base(s)
    Inputs: User choice dataframe
    Outputs: Map of pickups colored by base
    """
    layer = pdk.Layer(
        "ScatterplotLayer",
        df,
        get_position=["Lon", "Lat"],
        get_fill_color="color",
        get_radius=20,
        radius_min_pixels=1,
        opacity=0.4
        )
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view, map_style="light"))

def base_table(df, names):
    """
    Displays a table of bases selected by user. Column 1 is base name, 
    column 2 is color, column 3 total number of pickups
    Input: user selected dataframe, base names
    Output: n (number of valid selected bases) x 3 table
    """
    if df.empty:
        st.write("None of the selected bases have pickups in this time frame.")
        return
    table = df.groupby('name').agg(Color=('color', 'first'), 
                                   Pickups=('name', 'size')).reset_index()
    table.columns = ['Name', 'Color', 'Pickups']
    table['Color'] = table['Color'].map(lambda c: '#%02x%02x%02x' % tuple(c))
    st.dataframe(table.style.map(lambda c: f"background-color: {c}; color: {c}", subset=['Color']), hide_index=True)

    missing = [n for n in names if n not in table['Name'].values]
    if missing:
        st.write("No pickups in this time frame for: " + ", ".join(missing))


#------------------------------------------------------------------------------------------------------------------
def heatmap(df, view, names):
    """
    Displays a heatmap based on user selected bases. User can select certain date, time, or all times. 
    Inputs: user selected dataframe, view setting, names list
    Outputs: heat map of New York based on pickups (red to white/yellow) 
    """
    if df.empty:
        st.write("None of the selected bases have pickups in this time frame.")
        return

    dates = sorted(df['Date/Time'].dt.date.unique())
    day = st.select_slider("Date", ["All month"] + dates)
    hour = st.select_slider("Hour of day", ["All day"] + list(range(24)))

    if day != "All month":
        df = df[df['Date/Time'].dt.date == day]
    if hour != "All day":
        df = df[df['Date/Time'].dt.hour == hour]

    
    layer = pdk.Layer(
        "HeatmapLayer",
        df,
        get_position=["Lon", "Lat"],
        radius_pixels=30,
        opacity=0.6
    )
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view, map_style="light"))

    missing = [n for n in names if n not in df['name'].values]
    if missing:
        st.write("No pickups in this time frame for: " + ", ".join(missing))

def main():
    st.set_page_config(page_title="NYC Uber Pickups", layout="wide")

    st.title("Uber Pickups in New York City")
    st.caption("April 2014 · Source: FiveThirtyEight, from NYC Taxi & Limousine Commission records")
    st.write("Uber's NYC drivers were licensed through several 'bases'. "
             "This app looks at which bases were busiest, and when and where people got picked up.")
    st.write("Bases are licensing entities, not separate service areas")

    APR = get_data()

    overview()
    st.divider()

    mode = st.radio("Explore", ["Pickups over time", "Pickups by base", "Heatmap"], horizontal=True)

    view = pdk.ViewState(latitude=40.73, longitude=-73.94, zoom=10, pitch=0)

    if mode == "Pickups over time":
        st.subheader("Which base has the most pickups each day?")
        st.caption("Pick bases, how to group the time, and a date range.")
        selected, names = get_bases(APR, "all", key="graph")
        line_chart(selected, names)

    if mode == "Pickups by base":
        st.subheader("Where are the pickup locations for a base?")
        st.caption("Each dot is one pickup. Choose one or two bases at a time to compare them clearly.")
        selected, names = get_bases(APR, ["Hinter", "Schmecken"], key="scatter")
        scatterplotlay(selected, view)
        base_table(selected, names)

    if mode == "Heatmap":
        st.subheader("Which areas of the city are busiest?")
        st.caption("Red areas had more pickups. Colors rescale as you zoom. Slide to select specific date or hour")
        selected, names = get_bases(APR, "all", key="heat")
        heatmap(selected, view, names)

main()
