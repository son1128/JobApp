import streamlit as st
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from binance.client import Client 
import config
from datetime import datetime
import dateparser

st.set_page_config(layout="wide")

#title

st.title("Botsgrid")
st.markdown("""
By Sam and Saba

""")

# Expander Bar
expander_bar = st.beta_expander("Expand Me")
expander_bar.markdown("""
testing

could put settings here or data or something idk
""")

#---------------------------------#
# Page layout (continued)
## Divide page to 3 columns (col1 = sidebar, col2 and col3 = page contents)
col1 = st.sidebar
col2, col3 = st.beta_columns((2,1))

#---------------------------------#
# Sidebar + Main panel
col1.header('Input Options')

function = col1.selectbox('Select function', ('Gridbot', 'AI'))

if function == "Gridbot": #add gridbot only to here
    #streamlit.number_input(label, min_value=None, max_value=None, value=<streamlit.widgets.NoValue object>, step=None, format=None, key=None, help=None)
    lower_range = col1.number_input('Lower range', format='%g')
    upper_range = col1.number_input('Upper range', format='%g')
    grid_lines = col1.number_input('Grid lines', 3 , 100 , 10 , 1 )
    if lower_range > 0 and upper_range > 0 and grid_lines > 0: 
        percentstep = (((upper_range/lower_range) -1 )*100)/grid_lines
        col1.text("The average grid step percent is:")
        col1.markdown(percentstep)

## Sidebar - pull pairings list
client = Client(config.api_key, config.api_secret, tld='com')
exchange_info = client.get_exchange_info()
symbols = exchange_info['symbols']
#^ gives list of dictionarys with symbol
symbols_unsorted = []
for symbol in symbols:
    symbols_unsorted.append(symbol["symbol"])
#^ turns list of dictionarys into list


## Sidebar - Currency price unit
Pairing = col1.selectbox('Select pairing', (symbols_unsorted))

## Sidebar - Date slider
# start_date = col1.slider("When does it start?", value=datetime(2020, 1, 1, 9, 30), format="MM/DD/YY - hh:mm")

daterange = col1.date_input("Data range", [])
# col1.write(daterange)




# def data_grab():
#     # Data grab 
#     client = Client(config.api_key, config.api_secret, tld='com')
#     # ^ connecting to binance api

#     candlesticks = client.get_historical_klines(Pairing, Client.KLINE_INTERVAL_15MINUTE, "28 Feb 2021")
#     #Pairing comes from col1 selectbox

#         processed_candlesticks = []
#         for data in candlesticks:

#             candlestick = { 
#                 "time": data[0] / 1000, 
#                 #timestamp includes ms, want to remove
#                 "open": data[1],  
#                 "high": data[2],  
#                 "low": data[3], 
#                 "close": data[4] 
#             }
#         #transforming list of lists (array) into annotated dictionary
#             processed_candlesticks.append(candlestick)

#         return jsonify(processed_candlesticks)
#         #turn into json


candlesticks = []
csvformat = ['Date', 'Open', 'High', 'Low', 'Close', 'volume', 'closedtime', 'qvolume', 'trades', 'taker', 'taker2', 'day_num']

# I had to transform daterange[0] to milliseconds somehow for binance api, for some reason i could only get it to work converting it to a string, then back to datetime, then doing a timestamp transformation and then making it an integer
#starting by giving them default values so a chart loads in on startup
now = datetime.now()
timestamp = datetime.timestamp(now)
end = int(timestamp)*1000
print (end)
start = end - 80000000
print (start)
#now calculating the selected values if selected
if daterange :
    start = daterange[0].strftime('%b %d, %Y')
    date_object = datetime.strptime(start, '%b %d, %Y')
    start = datetime.timestamp(date_object)
    start=int(start)*1000
    print(start)

    end = daterange[1].strftime('%b %d, %Y')
    date_object = datetime.strptime(end, '%b %d, %Y')
    end = datetime.timestamp(date_object)
    end=int(end)*1000
    print(end)


#now fetching the data !
livedata = client.get_klines(symbol=Pairing, interval=Client.KLINE_INTERVAL_30MINUTE, startTime=start, endTime=end)
#livedata = client.get_klines(symbol=Pairing, interval=Client.KLINE_INTERVAL_30MINUTE)
#^allows startTime=  endTime=  and limit=(defaults to 500 but max 1000)



for data in livedata:
    datarow = { 
        "Date": data[0] / 1000, 
        #timestamp includes ms, want to remove
        "Open": data[1],  
        "High": data[2],  
        "Low": data[3], 
        "Close": data[4],
        "Volume": data[5],  
        "ClosedTime": data[6],  
        "QVolume": data[7], 
        "Trades": data[8],
        "Taker": data[9], 
        "Taker2": data[10],  
        "day_num": data[11], 
    }
    candlesticks.append(datarow)
    

# make a 1,2,3,4 sequence for the X axis
temp_list = []
for i in range(len(candlesticks)):
    temp_list.append(i)
    candlesticks[i]['day_num'] = temp_list[i]

#Convert data to panda dataframe
candlesticks = pd.DataFrame(candlesticks)
#convert data types from object to float/int/date
candlesticks = candlesticks.apply(pd.to_numeric, errors='ignore')
candlesticks['Date'] = candlesticks.apply(pd.to_datetime, errors='ignore')
# print(candlesticks.dtypes)



#at this point, everything above means the data is in the right format, a panda dataframe with the correct data types
#everything below is making graph from data


# Function to draw candlestick
def draw_candlestick(axis, data, color_up, color_down):
    
    # Check if stock closed higher or not
    if data['Close'] > data['Open']:
        color = color_up
    else:
        color = color_down

    # Plot the candle wick
    axis.plot([data['day_num'], data['day_num']], [data['Low'], data['High']], linewidth=1, color=color, solid_capstyle='round', zorder=2)
    
    # Draw the candle body
    rect = mpl.patches.Rectangle((data['day_num'] - 0.25, data['Open']), 0.6, (data['Close'] - data['Open']), facecolor=color, edgecolor=color, linewidth=1, zorder=3)

    # Add candle body to the axis
    axis.add_patch(rect)
    
    # Return modified axis
    return axis



# Function to draw all candlesticks
def draw_all_candlesticks(axis, data, color_up='white', color_down='black'):
  for day in range(data.shape[0]):
    axis = draw_candlestick(axis, data.iloc[day], color_up, color_down)
  return axis

# General plot parameters
mpl.rcParams['font.family'] = 'Futura'
mpl.rcParams['font.size'] = 14
mpl.rcParams['axes.linewidth'] = 0
mpl.rcParams['axes.facecolor'] = '#231F30'
#background
mpl.rcParams['xtick.major.size'] = 0
mpl.rcParams['xtick.major.pad'] = 10
mpl.rcParams['ytick.major.size'] = 0
mpl.rcParams['ytick.major.pad'] = 10

# Create figure and axes
fig = plt.figure(figsize=(10, 5), facecolor='white')
ax = fig.add_subplot(111)

# Colors for candlesticks
colors = ['#26A69A', '#EF5350']

# Grid lines
ax.grid(linestyle='-', linewidth=0.5, color='#2A2A3B', zorder=1)

# Draw candlesticks
ax = draw_all_candlesticks(ax, candlesticks, colors[0], colors[1])

# Set ticks to every 5th day
ax.set_xticks(list(candlesticks['day_num'])[::5])
ax.set_xticklabels(list(candlesticks['Date'].dt.strftime('%m-%d'))[::5])
plt.xticks(rotation=50)

# Set axis limits
ax.set_xlim(-1, candlesticks['day_num'].iloc[-1] + 1)

# drawing the upper and lower range limit lines
mpl.pyplot.axhline(y=upper_range, color='#DC143C', linestyle= 'dotted', linewidth=0.8, zorder=5)
mpl.pyplot.axhline(y=lower_range, color='#7FFF00', linestyle= 'dotted', linewidth=0.8, zorder=5)


fig
