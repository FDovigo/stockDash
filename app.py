import gunicorn

import datetime as dt
import yfinance as yf
import requests
from PIL import Image
from io import BytesIO

import pandas as pd
import pandas_datareader.data as web

import plotly.express as px
import plotly.graph_objects as go

import dash_bootstrap_components as dbc
from dash import dash, dcc, html
from dash.dependencies import Input, Output


yf.pdr_override()


app = dash.Dash(__name__, external_stylesheets = [dbc.themes.LUX])
server = app.server


##====================================================================================================##
#Varibles and Code Functions
##====================================================================================================##

#Variables
archive = "https://raw.githubusercontent.com/FDovigo/stockDash/de8be9054bc27e114218634759d1aeec57833951/IBrX100.csv"
image = "https://raw.githubusercontent.com/FDovigo/imageRepository/main/logocinza.jpg"
response = requests.get(image)
img = Image.open(BytesIO(response.content)),

long = 180
mid = 60
short = 12

lSample = 24
mSample = 12
sSample = 6

presentDate = dt.date(2022, 12, 30)
pastDate = presentDate - dt.timedelta(long)



#Code Functions
def ReadArchive(archive):
    data = pd.read_csv(archive)
    data = data['Ticker'].tolist()
    return data

def DownloadData(data, pastDate, presentDate):
    stockValue = web.get_data_yahoo(data, start = pastDate, end = presentDate)['Adj Close']
    return stockValue

def ReturnCalc(stockValue):
    returnCalc = pd.DataFrame()
    for value in stockValue:
        returnCalc[value] = (stockValue[value] / stockValue[value].shift(1))
    return returnCalc

def StockListCreator(sampleSize):
    counter = 1
    stockList = list()

    while counter <= sampleSize:
        stockList.append('stockDay' + str(counter))
        counter += 1
    
    return stockList

def StockDctCreator(returnCalc, stockList, sampleSize):
    firstFactor = 1
    secondFactor = -sampleSize
    stockDct = {}

    for day in stockList:
        stockDct[day] = returnCalc.copy()[firstFactor: secondFactor]
        firstFactor += 1
        secondFactor += 1
    
    return stockDct

def DctSharpCalc(stockList, stockDct):
    stockDctMean = {}
    for day in stockList:
        stockDctMean[day] = stockDct[day].prod() - 1

    stockDctSD = {}
    for day in stockList:
        stockDctSD[day] = stockDct[day].std()

    stockDctSharp = {}
    for day in stockList:
        stockDctSharp[day] = stockDctMean[day] / stockDctSD[day]
    
    return stockDctSharp

def DctSharpSum (stockList, stockDctSharp):
    stockSum = pd.DataFrame()
    stockFinal = pd.DataFrame()

    for day in stockList:

        if stockSum.empty:
            stockSum = stockDctSharp[day]
        
        else:
            stockSum = stockSum + stockDctSharp[day]
    
    stockFinal = stockSum

    return stockFinal

def StockOrder (stockSharpSum, sampleSize):
    stockOrdered = stockSharpSum
    stockOrdered = stockOrdered.sort_values(ascending = False)
    stockOrdered = stockOrdered.index[0:sampleSize]
    return stockOrdered

def FilterStockReturn (frame, filter, size):
    filterStockReturn = pd.DataFrame()
    filterStockReturn = frame[filter]
    filterStockReturn = filterStockReturn[:size]
    return filterStockReturn

def RevenueCalc(presentDate, bestStocks):
    
    bestStocks = bestStocks.tolist()
    
    rcFutureDate = presentDate + dt.timedelta(30)

    rcStockValue = DownloadData(data = bestStocks, pastDate = presentDate, presentDate = rcFutureDate)
    rcStockReturn = ReturnCalc(stockValue = rcStockValue)

    rcResult = rcStockReturn.prod()
    rcResultMean = rcResult.mean()

    return rcResultMean

def ShowInDash(lStockValue, lStockReturn, sBestStocks):

    stockInDash = pd.DataFrame()
    stockInDash = lStockValue[sBestStocks].iloc[-1]
    
    figInDash = (lStockReturn[sBestStocks] - 1) * 100

    return stockInDash, figInDash



#Composity Code Functions (for stock filtering and portfolio)

#Long Term and Wider Filter
def LongStockFilter(archive, presentDate, pastDate, lSample):

    #função basica
    data = ReadArchive(archive = archive)
    lStockValue = DownloadData(data = data, pastDate = pastDate, presentDate = presentDate)
    lStockReturn = ReturnCalc(stockValue = lStockValue)

    #modelando os dados em dicionário e realizando cálculos
    lDayList = StockListCreator(sampleSize = lSample)
    lStockDct = StockDctCreator(returnCalc = lStockReturn, stockList = lDayList,  sampleSize = lSample)
    lStockDctSharp = DctSharpCalc(stockList = lDayList, stockDct = lStockDct)
    lSharpSum = DctSharpSum(stockList = lDayList, stockDctSharp= lStockDctSharp)

    #filtrando as ações
    lBestStocks = StockOrder(stockSharpSum = lSharpSum, sampleSize = lSample)

    return lStockValue, lStockReturn, lBestStocks

#Medium Term and Narrow Filter
def MidStockFilter(lStockReturn, lBestStocks, mSample, mid):
    
    #função basica
    mStockReturn = FilterStockReturn(frame = lStockReturn, filter = lBestStocks, size = mid)

    #modelando os dados em dicionário e realizando cálculos
    mDayList = StockListCreator(sampleSize = mSample)
    mStockDct = StockDctCreator(returnCalc = mStockReturn, stockList = mDayList,  sampleSize = mSample)
    mStockDctSharp = DctSharpCalc(stockList = mDayList, stockDct = mStockDct)
    mSharpSum = DctSharpSum(stockList = mDayList, stockDctSharp= mStockDctSharp)

    #filtrando as ações
    mBestStocks = StockOrder(stockSharpSum = mSharpSum, sampleSize = mSample)

    return mBestStocks

#Short Term and Last Filter
def ShortStockFilter(lStockReturn, mBestStocks, sSample, short):

    #função basica
    sStockReturn = FilterStockReturn(frame = lStockReturn, filter = mBestStocks, size = short)

    #modelando os dados em dicionário e realizando cálculos
    sDayList = StockListCreator(sampleSize = sSample)
    sStockDct = StockDctCreator(returnCalc = sStockReturn, stockList = sDayList,  sampleSize = sSample)
    sStockDctSharp = DctSharpCalc(stockList = sDayList, stockDct = sStockDct)
    sSharpSum = DctSharpSum(stockList = sDayList, stockDctSharp= sStockDctSharp)

    #filtrando as ações
    sBestStocks = StockOrder(stockSharpSum = sSharpSum, sampleSize = sSample)
    print(sBestStocks)

    return sBestStocks

#Composite Function for Back Testing
def BackTest(archive, chosenDate, lSample, mSample, sSample, long, mid, short, nIteraction):

    iteraction = 0
    sumRevenue = 1

    while iteraction < nIteraction:

        btPresentDate = chosenDate + dt.timedelta(30 * iteraction)
        btPastDate = btPresentDate - dt.timedelta(long)

        lStockValue, lStockReturn, lBestStocks = LongStockFilter(archive, btPresentDate, btPastDate, lSample)
        mBestStocks = MidStockFilter(lStockReturn, lBestStocks, mSample, mid)
        sBestStocks = ShortStockFilter(lStockReturn, mBestStocks, sSample, short)

        revenue = RevenueCalc(presentDate = btPresentDate, bestStocks = sBestStocks)
        sumRevenue = sumRevenue * revenue

        iteraction += 1
    
    sumRevenue = (sumRevenue - 1)*100

    return sumRevenue

def FigureBuild(figInDash, stock):

    fig = px.area(figInDash[str(stock)], range_y = [-20, 30])
    fig.update_layout(
        template = "simple_white",
        #autosize = True,
        margin = go.layout.Margin(l = 25, r = 25, t = 15, b = 15),
        yaxis_title = None,
        xaxis_title = None,
        showlegend = False,
    )
    fig.update_xaxes(
        rangebreaks = [dict(bounds = ["sat", "mon"])],
        tickformat = "%b %y"
    )
    fig.update_yaxes(
        showgrid=True,
        griddash = "dot",
        gridcolor = "#808080",
        showticklabels = False,
    )
    fig.add_shape(
    type="line", line_color="black", line_width=1, opacity=1,
    x0=0, x1=1, xref="paper", y0=0, y1=0, yref="y"
    )

    return fig





##====================================================================================================##
#Stock Portfolio and Backtest Codes(based on Long, Medium and Short Term functions)
##====================================================================================================##

# #Stock Portfolio
# lStockValue, lStockReturn, lBestStocks = LongStockFilter(archive, presentDate, pastDate, lSample)
# mBestStocks = MidStockFilter(lStockReturn, lBestStocks, mSample, mid)
# sBestStocks = ShortStockFilter(lStockReturn, mBestStocks, sSample, short)

# #BackTest (need to automize Date and Interaction selection)
# chosenDate = dt.date(2021, 12, 30)
# nIteraction = 0
# BackTestRevenue = BackTest(archive, chosenDate, lSample, mSample, sSample, long, mid, short, nIteraction)
# print('BackTest, com início em ' + str(chosenDate) + ' e ' + str(nIteraction) + ' Iterações, resultou em: '+str(round(BackTestRevenue,2)) + '%')

# #Dash
# stockInDash, figInDash = ShowInDash(lStockValue, lStockReturn, sBestStocks)





##====================================================================================================##
#Web Layout
##====================================================================================================##


app.layout = dbc.Container(children=[
    
    dbc.Row([ 

        dbc.Col([

            html.H1("Sharpy", className = "Heading 1", 
                    style = {"margin-top": "20px", "margin-left": "20px"}),

            html.H4("By FinancEEL", className = "text-info",
                    style = {"margin-left": "20px"}),
                    
            html.Hr(),

            html.H4("Informe a Data Inicial da Carteira", className = "text-primary",
                    style = {"margin-top": "60px", "text-align":"center"}),

            html.Div([            
                dcc.DatePickerSingle(
                    id = "date-select",
                    min_date_allowed = '2019-12-31',
                    max_date_allowed = '2022-12-31',
                    date = '2022-12-31',
                    display_format = "MMM D, YY",
                    day_size = 45,
                    style = {"border": "0px solid black", "margin-top": "40px"},
                ),
            ], style = {"display" : "flex", "justifyContent" : "center"}),


            dbc.Row([

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(id = "stock1", className = "text-body-secondary", style = {"text-align":"center"}),
                            html.H2(id = "value1", className = "text-dark-emphasis", style = {"text-align":"center"}),
                        ])
                    ],  color = "light", outline = True, 
                        style = {"margin-top": "80px",
                                "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                "color": "#FFFFFF"})
                ], md = 3),

                dbc.Col([
                    dbc.Card([ 
                        dbc.CardBody([
                            html.H4(id = "stock2", className = "text-body-secondary", style = {"text-align":"center"}),
                            html.H2(id = "value2", className = "text-dark-emphasis", style = {"text-align":"center"}),
                        ])
                    ],  color = "light", outline = True, 
                        style = {"margin-top": "80px",
                                "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                "color": "#FFFFFF"})
                ], md = 3),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(id = "stock3", className = "text-body-secondary", style = {"text-align":"center"}),
                            html.H2(id = "value3", className = "text-dark-emphasis", style = {"text-align":"center"}),
                        ])
                    ],  color = "light", outline = True, 
                        style = {"margin-top": "80px",
                                "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                "color": "#FFFFFF"})
                ], md = 3), 
            ], style = {"justify-content": "space-evenly"}),

            dbc.Row([

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(id = "stock4", className = "text-body-secondary", style = {"text-align":"center"}),
                            html.H2(id = "value4", className = "text-dark-emphasis", style = {"text-align":"center"}),
                        ])
                    ],  color = "light", outline = True, 
                        style = {"margin-top": "80px",
                                 "resize": "both",
                                "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                "color": "#FFFFFF"})
                ], md = 3),

                dbc.Col([
                    dbc.Card([ 
                        dbc.CardBody([
                            html.H4(id = "stock5", className = "text-body-secondary", style = {"text-align":"center"}),
                            html.H2(id = "value5", className = "text-dark-emphasis", style = {"text-align":"center"}),
                        ])
                    ],  color = "light", outline = True, 
                        style = {"margin-top": "80px",
                                "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                "color": "#FFFFFF"})
                ], md = 3),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(id = "stock6", className = "text-body-secondary", style = {"text-align":"center"}),
                            html.H2(id = "value6", className = "text-dark-emphasis", style = {"text-align":"center"}),
                        ])
                    ],  color = "light", outline = True, 
                        style = {"margin-top": "80px",
                                "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                "color": "#FFFFFF"})
                ], md = 3), 
            ], style = {"justify-content": "space-evenly"}),

            html.Div([
                html.Img(src = image, height = 160),
            ], style = {"display" : "flex", "justifyContent" : "center", "margin-top": "120px","margin-bottom": "120px"}),

        ], md = 6),


        dbc.Col([

            dbc.Row([

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(id = "stockCD1", className = "text-light", style = {"text-align":"center", "font-size":"20px"}),
                        dcc.Graph(id = "line-map1", style = {"height": "26vh"}), 
                    ], style = {"margin-top": "20px"}, color = "dark"),
                ], md = 5),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(id = "stockCD2", className = "text-light", style = {"text-align":"center", "font-size":"20px"}),
                        dcc.Graph(id = "line-map2", style = {"height": "26vh"}), 
                    ], style = {"margin-top": "20px"}, color = "dark"),
                ], md = 5),

            ], style = {"justify-content": "space-evenly"}),

            dbc.Row([

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(id = "stockCD3", className = "text-light", style = {"text-align":"center", "font-size":"20px"}),
                        dcc.Graph(id = "line-map3", style = {"height": "26vh"}), 
                    ], style = {"margin-top": "20px"}, color = "dark"),
                ], md = 5),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(id = "stockCD4", className = "text-light", style = {"text-align":"center", "font-size":"20px"}),
                        dcc.Graph(id = "line-map4", style = {"height": "26vh"}), 
                    ], style = {"margin-top": "20px"}, color = "dark"),
                ], md = 5),
            ], style = {"justify-content": "space-evenly"}),

            dbc.Row([

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(id = "stockCD5", className = "text-light", style = {"text-align":"center", "font-size":"20px"}),
                        dcc.Graph(id = "line-map5", style = {"height": "26vh"}), 
                    ], style = {"margin-top": "20px"}, color = "dark"),
                ], md = 5),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(id = "stockCD6", className = "text-light", style = {"text-align":"center", "font-size":"20px"}),
                        dcc.Graph(id = "line-map6", style = {"height": "26vh"}), 
                    ], style = {"margin-top": "20px"}, color = "dark"),
                ], md = 5),
            ], style = {"justify-content": "space-evenly"}),

        ], md = 6),

    ], className = "g-0"),
], fluid = True)





##====================================================================================================##
#Web Interactivity
##====================================================================================================##
@app.callback(
    [
    #StockCards OutPut
    Output(component_id = "stock1", component_property = "children"),
    Output(component_id = "stock2", component_property = "children"),
    Output(component_id = "stock3", component_property = "children"),
    Output(component_id = "stock4", component_property = "children"),
    Output(component_id = "stock5", component_property = "children"),
    Output(component_id = "stock6", component_property = "children"),
    Output(component_id = "value1", component_property = "children"),
    Output(component_id = "value2", component_property = "children"),
    Output(component_id = "value3", component_property = "children"),
    Output(component_id = "value4", component_property = "children"),
    Output(component_id = "value5", component_property = "children"),
    Output(component_id = "value6", component_property = "children"),
    #Graphic OutPut
    Output(component_id = "stockCD1", component_property = "children"),
    Output(component_id = "stockCD2", component_property = "children"),
    Output(component_id = "stockCD3", component_property = "children"),
    Output(component_id = "stockCD4", component_property = "children"),
    Output(component_id = "stockCD5", component_property = "children"),
    Output(component_id = "stockCD6", component_property = "children"),
    Output(component_id = "line-map1", component_property = "figure"),
    Output(component_id = "line-map2", component_property = "figure"),
    Output(component_id = "line-map3", component_property = "figure"),
    Output(component_id = "line-map4", component_property = "figure"),
    Output(component_id = "line-map5", component_property = "figure"),
    Output(component_id = "line-map6", component_property = "figure")
    ],

    [
    #Date Input
    Input(component_id = "date-select", component_property = "date"),
    ]
)

def update(date):

    presentDate = date

    #Stock Portfolio
    lStockValue, lStockReturn, lBestStocks = LongStockFilter(archive, presentDate, pastDate, lSample)
    mBestStocks = MidStockFilter(lStockReturn, lBestStocks, mSample, mid)
    sBestStocks = ShortStockFilter(lStockReturn, mBestStocks, sSample, short)
            
    #BackTest (need to automize Date and Interaction selection)
    chosenDate = dt.date(2021, 12, 30)
    nIteraction = 0
    BackTestRevenue = BackTest(archive, chosenDate, lSample, mSample, sSample, long, mid, short, nIteraction)
    print('BackTest, com início em ' + str(chosenDate) + ' e ' + str(nIteraction) + ' Iterações, resultou em: '+str(round(BackTestRevenue,2)) + '%')

    #Dash
    stockInDash, figInDash = ShowInDash(lStockValue, lStockReturn, sBestStocks)

    stock1 = (stockInDash.index[0]).split(".")[0]
    stock2 = (stockInDash.index[1]).split(".")[0]
    stock3 = (stockInDash.index[2]).split(".")[0]
    stock4 = (stockInDash.index[3]).split(".")[0]
    stock5 = (stockInDash.index[4]).split(".")[0]
    stock6 = (stockInDash.index[5]).split(".")[0]

    value1 = round(stockInDash[0], 2)
    value2 = round(stockInDash[1], 2)
    value3 = round(stockInDash[2], 2)
    value4 = round(stockInDash[3], 2)
    value5 = round(stockInDash[4], 2)
    value6 = round(stockInDash[5], 2)


    #Graphic
    #Stocks in Graphic Title
    stockCD1 = stock1
    stockCD2 = stock2
    stockCD3 = stock3
    stockCD4 = stock4
    stockCD5 = stock5
    stockCD6 = stock6

    #Figure
    fig1 = FigureBuild(figInDash, stockInDash.index[0])
    fig2 = FigureBuild(figInDash, stockInDash.index[1])
    fig3 = FigureBuild(figInDash, stockInDash.index[2])
    fig4 = FigureBuild(figInDash, stockInDash.index[3])
    fig5 = FigureBuild(figInDash, stockInDash.index[4])
    fig6 = FigureBuild(figInDash, stockInDash.index[5])


   
    return (stock1, stock2, stock3, stock4, stock5, stock6, 
            value1, value2, value3, value4, value5, value6,
            stockCD1, stockCD2, stockCD3, stockCD4, stockCD5, stockCD6, 
            fig1, fig2, fig3, fig4, fig5, fig6)





if __name__ == "__main__":
    app.run_server(debug = True)