import requests
import json
from datetime import date, timedelta, datetime
import warnings
import altair as alt
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning, module="altair")

# POLYGON API KEY NEEDED
POLYGON_API_KEY = 'YOUR POLYGON.IO API KEY HERE'

# GOOGLE API KEY OPTIONAL
GOOGLE_API_KEY = None

# Select Stock to check, MUST BE VALID TICKER
ticker = 'AAPL'

# Choose start and end date
start_date = '2023-06-01'
to_date = date.today()

# Changes entered dates to datetime type
if not isinstance(start_date, date):
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

if not isinstance(to_date, date):
    to_date = datetime.strptime(to_date, '%Y-%m-%d').date()


end_date = to_date - timedelta(days=1)
delta = end_date - start_date
days = []

# Removes all holidays and weekends from days selected
for i in range(delta.days + 1):
    day = start_date + timedelta(days=i)
    if day.weekday() not in [5, 6] and day not in (date(2023, 1, 2), date(2023, 1, 16), date(2023, 2, 20),
                                                  date(2023, 4, 7), date(2023, 5, 29), date(2023, 6, 19),
                                                  date(2023, 7, 4), date(2023, 9, 4), date(2023, 11, 23),
                                                  date(2023, 12, 25)):
        days.append(str(day))

# Function to get information from Polygon.io API
def stocks_data(start_date):
    time_multiple = '1'
    time_span = 'day'

    stock_ticker = f'https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{time_multiple}/{time_span}/{start_date}/{to_date}' \
               f'?adjusted=true&sort=asc&limit=120&apiKey={POLYGON_API_KEY}'

    stock_info = requests.get(stock_ticker)

    stock_dict = json.loads(stock_info.content)
    return stock_dict


# Gets information of stock data
def stock_details():
    stock_ticker_details = f'https://api.polygon.io/v3/reference/tickers/{ticker}?apiKey={POLYGON_API_KEY}'
    stock_ticker_details_req = requests.get(stock_ticker_details)
    st_details = json.loads(stock_ticker_details_req.content)
    return st_details


st_details = stock_details()
open_price = []
close_price = []
high = []
low = []

# Calls API for days in the time range
# If the results doesn't equal the number of days then it will continue to call the API to have the total number of days
while len(days) > len(open_price):

    if open_price == None:
        stock_dict = stocks_data(start_date)
    else:
        stock_dict = stocks_data(days[len(open_price)])
    for each in stock_dict['results']:
        open_price.append(each['o'])
        close_price.append(each['c'])
        high.append(each['h'])
        low.append(each['l'])


# Function to create candlestick chart and save it to a html file
def candlestick():
    # Puts stock information into pandas dataframe, open high low close and dates
    df = pd.DataFrame({'open': open_price, 'close': close_price, 'high': high, 'low': low, 'date': days[:len(open_price)]})

    open_close_color = alt.condition(
        "datum.open <= datum.close",
        alt.value("#06982d"),
        alt.value("#ae1325")
    )

    base = alt.Chart(df).encode(
        alt.X('date:T')
            .axis(format='%m/%d', labelAngle=-45)
            .title('Dates'),
        color=open_close_color
    ).properties(
        width=1500,
        height=700
    )

    rule = base.mark_rule().encode(
        alt.Y('low:Q')
            .title('Price')
            .scale(zero=False),
        alt.Y2('high:Q')
    )

    bar = base.mark_bar().encode(
        alt.Y('open:Q'),
        alt.Y2('close:Q')
    )

    # Combine candlestick elements
    chart = rule + bar
    chart = chart.properties(
        title=f'Candlestick chart of {ticker} from {start_date} to {end_date}'
    )
    html_file = f'{ticker}_candle_stick.html'

    chart.save(html_file)
    return html_file


html_file = candlestick()

# Reads the html file
with open(html_file, 'r', encoding='utf-8') as file:
    html_content = file.read()

# adds title to the web page
new_content = html_content.replace('<head>', f'<head><title>{st_details["results"]["name"]} Page</title>')


try:
    new_content = new_content.replace('</title>', f'</title>\n'
                                                  f'<link rel="icon" '
                                                  f'href="{st_details["results"]["branding"]["icon_url"]}?apiKey={POLYGON_API_KEY}"'
                                                  f'type="image/{st_details["results"]["name"]}-icon">')

    new_content_stock_info = new_content.replace(f'<body>', f'<body><h1>{st_details["results"]["name"]} Stock Information:</h1>\n'
                                                         f'<h3>Ticker: {ticker}</h3>\n'
                                                         f'<p>Homepage: <a href={st_details["results"]["homepage_url"]}>'
                                                        f'<img src={st_details["results"]["branding"]["icon_url"]}?apiKey={POLYGON_API_KEY}'
                                                        f' width="50" height="50">'
                                                        f'</a></p>\n'
                                                         f'<p>Phone Number: <a href="tel:{st_details["results"]["phone_number"]}">{st_details["results"]["phone_number"]}</a></p>\n'
                                                         )

    # Checks if Google API Key exists, if it does it will display Google Maps location of address on file
    if GOOGLE_API_KEY == None:
        new_content_stock_info = new_content_stock_info.replace('<div id="vis"></div>',f'Address: {" ".join([value for key, value in st_details["results"]["address"].items()])}\n'
                                                                                       f'<div id="vis"></div>')
    else:
        new_content_stock_info = new_content_stock_info.replace('<div id="vis"></div>',
                                                                f'<iframe width="300"'
                                                                f'height="175"'
                                                                f'frameborder="0"'
                                                                f'style="border:0"'
                                                                f'src="https://www.google.com/maps/embed/v1/place?key={GOOGLE_API_KEY}&q={" ".join([value for key, value in st_details["results"]["address"].items()])}"'
                                                                f'allowfullscrean>'
                                                                f'</iframe>\n'
                                                                f'<div id="vis"></div>')

    new_content_stock_info = new_content_stock_info.replace('</body>', f'\n'
                                                                         f'<p>Description: {st_details["results"]["description"]}</p>\n'
                                                                       f'</body>')
except:
    new_content_stock_info = new_content.replace(f'<body>',
                                                 f'<body><h1>{st_details["results"]["name"]} Stock Information:</h1>\n'
                                                 f'<h3>Ticker: {ticker}</h3>\n')

# Write the updated content back to the HTML file
with open(html_file, 'w', encoding='utf-8') as file_write:
    file_write.write(new_content_stock_info)
