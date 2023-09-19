#>---------------------------------------------------------------------------------------------------<#
#importing packages
#>---------------------------------------------------------------------------------------------------<#

import gunicorn

import datetime as dt
import yfinance as yf
from datetime import datetime

import pandas as pd
import pandas_datareader.data as web

import plotly.express as px
import plotly.graph_objects as go

import dash_bootstrap_components as dbc
from dash import dash, dcc, html
from dash.dependencies import Input, Output, State





##====================================================================================================##
#Essential Functions for Code and App Start
##====================================================================================================##

yf.pdr_override()

app = dash.Dash(__name__, external_stylesheets = [dbc.themes.LUX, dbc.icons.BOOTSTRAP])
server = app.server





##====================================================================================================##
#Varibles and Code Functions
##====================================================================================================##

#Variables
archive = "https://raw.githubusercontent.com/FDovigo/dataRepository/f3289eeded7b08ff64ed3fb90351f18d36209608/IBrx50.csv"
imageLogo = "https://raw.githubusercontent.com/FDovigo/imageRepository/main/Sharpy/logocinza.jpg"
imageIndex = "https://raw.githubusercontent.com/FDovigo/imageRepository/main/Sharpy/index.jpg"
imageSharp = "https://raw.githubusercontent.com/FDovigo/imageRepository/main/Sharpy/sharpy.png"
dev1 = "https://raw.githubusercontent.com/FDovigo/imageRepository/main/Sharpy/dev1.jpg"
dev2 = "https://raw.githubusercontent.com/FDovigo/imageRepository/main/Sharpy/dev2.jpg"
dev3 = "https://raw.githubusercontent.com/FDovigo/imageRepository/main/Sharpy/dev3.jpg"

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
    rcStockAcumulated = rcStockValue.copy()
    for value in rcStockAcumulated:
        rcStockAcumulated[value] = rcStockValue[value] / rcStockValue[value].iloc[0]


    rcResult = rcStockAcumulated
    rcResultMean = rcResult.mean()
    rcAcumulated = ((rcStockAcumulated - 1) * 100)

    return rcStockValue, rcResult, rcResultMean, rcAcumulated

def RevenueIBOV(presentDate, IBOV):
    
    rcFutureDate = presentDate + dt.timedelta(30)

    rcStockValue = DownloadData(data = IBOV, pastDate = presentDate, presentDate = rcFutureDate)
    rcStockAcumulated = (rcStockValue / rcStockValue.iloc[0])

    rcResult = rcStockAcumulated
    rcAcumulated = ((rcStockAcumulated - 1) * 100)

    return rcResult, rcAcumulated

def ShowInDash(lStockValue, lStockReturn, sBestStocks):

    stockInDash = pd.DataFrame()
    stockInDash = lStockValue[sBestStocks].iloc[-1]
    
    figInDash = (lStockReturn[sBestStocks] - 1) * 100

    return stockInDash, figInDash

def BtShowInDash(StockValue, sBestStocks):

    stockInDashStart = pd.DataFrame()
    stockInDashEnd = pd.DataFrame()
    stockInDashStart = StockValue[sBestStocks].iloc[0]
    stockInDashEnd = StockValue[sBestStocks].iloc[-1]
    

    return stockInDashStart, stockInDashEnd



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
def BackTest(archive, chosenDate, lSample, mSample, sSample, long, mid, short):

    btPresentDate = chosenDate
    btPastDate = btPresentDate - dt.timedelta(long)

    lStockValue, lStockReturn, lBestStocks = LongStockFilter(archive, btPresentDate, btPastDate, lSample)
    mBestStocks = MidStockFilter(lStockReturn, lBestStocks, mSample, mid)
    sBestStocks = ShortStockFilter(lStockReturn, mBestStocks, sSample, short)

    rcStockValue, rcResult, rcResultMean, rcAcumulated = RevenueCalc(presentDate = btPresentDate, bestStocks = sBestStocks)
    rcResultMean = (rcResultMean - 1)*100

    return lStockValue, lStockReturn, sBestStocks, rcStockValue, rcResult, rcResultMean, rcAcumulated

#Graph Construction for Sharpy Dashboard
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

#Graph Construction for Backtest Dashboard
def BtFigureBuild(figInDash):

    fig = px.line(figInDash)
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
        tickformat = "%d %b"
    )
    fig.update_yaxes(
        showgrid =True,
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
#Web Pre-Builds -> Sharpy Page
##====================================================================================================##


leftSharpy = dbc.Container(children=[

    #Left Column
    dbc.Col([

        html.P("Selecione a Data Inicial da Carteira", className = "text-primary",
                style = {"margin-top": "8vh", "text-align":"center", "font-size": "2vh"}),

        html.Div([            
            dcc.DatePickerSingle(
                id = "date-select",
                min_date_allowed = '2019-12-31',
                max_date_allowed = '2022-12-31',
                date = '2022-12-31',
                display_format = "MMM D, YY",
                day_size = 45,
                style = {"border": "0px solid black", "margin-top": "3vh"},
            ),
        ], style = {"display" : "flex", "justifyContent" : "center"}),


        dcc.Loading(id = "loading1", type = "circle", children = [

            dbc.Row([

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H1(id = "stock1", className = "text-body-secondary", style = {"text-align":"center", "font-size": "2vh"}),
                            html.H1(id = "value1", className = "text-dark-emphasis", style = {"text-align":"center", "font-size": "2.5vh"}),
                        ])
                    ],  color = "light", outline = True, 
                        style = {"margin-top": "8vh",
                                "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                "color": "#FFFFFF"})
                ], md = 3),

                dbc.Col([
                    dbc.Card([ 
                        dbc.CardBody([
                            html.H4(id = "stock2", className = "text-body-secondary", style = {"text-align":"center", "font-size": "2vh"}),
                            html.H2(id = "value2", className = "text-dark-emphasis", style = {"text-align":"center", "font-size": "2.5vh"}),
                        ])
                    ],  color = "light", outline = True, 
                        style = {"margin-top": "8vh",
                                "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                "color": "#FFFFFF"})
                ], md = 3),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(id = "stock3", className = "text-body-secondary", style = {"text-align":"center", "font-size": "2vh"}),
                            html.H2(id = "value3", className = "text-dark-emphasis", style = {"text-align":"center", "font-size": "2.5vh"}),
                        ])
                    ],  color = "light", outline = True, 
                        style = {"margin-top": "8vh",
                                "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                "color": "#FFFFFF"})
                ], md = 3), 
            ], style = {"justify-content": "space-evenly"}),


            dbc.Row([

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(id = "stock4", className = "text-body-secondary", style = {"text-align":"center", "font-size": "2vh"}),
                            html.H2(id = "value4", className = "text-dark-emphasis", style = {"text-align":"center", "font-size": "2.5vh"}),
                        ])
                    ],  color = "light", outline = True, 
                        style = {"margin-top": "6vh",
                                "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                "color": "#FFFFFF"})
                ], md = 3),

                dbc.Col([
                    dbc.Card([ 
                        dbc.CardBody([
                            html.H4(id = "stock5", className = "text-body-secondary", style = {"text-align":"center", "font-size": "2vh"}),
                            html.H2(id = "value5", className = "text-dark-emphasis", style = {"text-align":"center", "font-size": "2.5vh"}),
                        ])
                    ],  color = "light", outline = True, 
                        style = {"margin-top": "6vh",
                                "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                "color": "#FFFFFF"})
                ], md = 3),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(id = "stock6", className = "text-body-secondary", style = {"text-align":"center", "font-size": "2vh"}),
                            html.H2(id = "value6", className = "text-dark-emphasis", style = {"text-align":"center", "font-size": "2.5vh"}),
                        ])
                    ],  color = "light", outline = True, 
                        style = {"margin-top": "6vh",
                                "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                "color": "#FFFFFF"})
                ], md = 3), 
            ], style = {"justify-content": "space-evenly"}),

        ]),


        html.Div([
                html.Img(src = imageLogo, style = {"height": "8vh", "margin-top": "14vh","margin-bottom": "14vh"})
        ], style = {"display" : "flex", "justifyContent" : "center"})

    ], md = 12),

], fluid = True)



rightSharpy = dbc.Container(children=[

    #Right Column
    dbc.Col([

        dcc.Loading(id = "loading2", type = "cube", children = [

            dbc.Row([

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(id = "stockCD1", className = "text-light", style = {"text-align":"center", "font-size":"1.75vh"}),
                        dcc.Graph(id = "line-map1", style = {"height": "23vh"}), 
                    ], style = {"margin-top": "2vh"}, color = "dark"),
                ], md = 5),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(id = "stockCD2", className = "text-light", style = {"text-align":"center", "font-size":"1.75vh"}),
                        dcc.Graph(id = "line-map2", style = {"height": "23vh"}), 
                    ], style = {"margin-top": "2vh"}, color = "dark"),
                ], md = 5),

            ], style = {"justify-content": "space-evenly"}),


            dbc.Row([

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(id = "stockCD3", className = "text-light", style = {"text-align":"center", "font-size":"1.75vh"}),
                        dcc.Graph(id = "line-map3", style = {"height": "23vh"}), 
                    ], style = {"margin-top": "2vh"}, color = "dark"),
                ], md = 5),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(id = "stockCD4", className = "text-light", style = {"text-align":"center", "font-size":"1.75vh"}),
                        dcc.Graph(id = "line-map4", style = {"height": "23vh"}), 
                    ], style = {"margin-top": "2vh"}, color = "dark"),
                ], md = 5),
            ], style = {"justify-content": "space-evenly"}),


            dbc.Row([

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(id = "stockCD5", className = "text-light", style = {"text-align":"center", "font-size":"1.75vh"}),
                        dcc.Graph(id = "line-map5", style = {"height": "23vh"}), 
                    ], style = {"margin-top": "2vh"}, color = "dark"),
                ], md = 5),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(id = "stockCD6", className = "text-light", style = {"text-align":"center", "font-size":"1.75vh"}),
                        dcc.Graph(id = "line-map6", style = {"height": "23vh"}), 
                    ], style = {"margin-top": "2vh"}, color = "dark"),
                ], md = 5),
            ], style = {"justify-content": "space-evenly"}),
        
        ])

    ], md = 12),

], fluid = True)





##====================================================================================================##
#Web Pre-Builds -> Backtest Page
##====================================================================================================##


leftBacktest = dbc.Container(children=[

    #Left Column
    dbc.Col([

        html.P("Selecione a Data Inicial do Backtest", className = "text-primary",
                style = {"margin-top": "6vh", "text-align":"center", "font-size": "2vh"}),

        html.Div([            
            dcc.DatePickerSingle(
                id = "btdate-select",
                min_date_allowed = '2019-12-31',
                max_date_allowed = '2022-12-31',
                date = '2022-12-31',
                display_format = "MMM D, YY",
                day_size = 45,
                style = {"border": "0px solid black", "margin-top": "2vh"},
            ),
        ], style = {"display" : "flex", "justifyContent" : "center"}),


        dcc.Loading(id = "loading1", type = "circle", children = [

            dbc.Row([

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H1(id = "btstock1", className = "text-body-secondary", style = {"text-align":"center", "font-size": "2vh"}),
                            dbc.Stack([
                                dbc.Col([
                                    html.H1("Inicial", className = "text-body-secondary", style = {"text-align":"center", "font-size": "1.5vh"}),
                                    html.H1(id = "btvalue1s", className = "text-dark-emphasis", style = {"text-align":"center", "font-size": "1.5vh"}),
                                ], md = 6),
                                dbc.Col([
                                    html.H1("Final", className = "text-body-secondary", style = {"text-align":"center", "font-size": "1.5vh"}),
                                    html.H1(id = "btvalue1f", className = "text-dark-emphasis", style = {"text-align":"center", "font-size": "1.5vh"}),
                                ], md = 6)
                            ], direction = "horizontal", gap = 2, style = {"justify-content": "space-evenly", "margin-top": "1.666vh", "margin-bottom": "1vh"}),
                            html.H1(id = "btresult1", className = "text-body-secondary", style = {"text-align":"center", "font-size": "2vh"}),
                        ])
                    ],  color = "light", outline = True,
                        style = {"margin-top": "7vh",
                                "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                "color": "#FFFFFF"})
                ], md = 3),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H1(id = "btstock2", className = "text-body-secondary", style = {"text-align":"center", "font-size": "2vh"}),
                            dbc.Stack([
                                dbc.Col([
                                    html.H1("Inicial", className = "text-body-secondary", style = {"text-align":"center", "font-size": "1.5vh"}),
                                    html.H1(id = "btvalue2s", className = "text-dark-emphasis", style = {"text-align":"center", "font-size": "1.5vh"}),
                                ], md = 6),
                                dbc.Col([
                                    html.H1("Final", className = "text-body-secondary", style = {"text-align":"center", "font-size": "1.5vh"}),
                                    html.H1(id = "btvalue2f", className = "text-dark-emphasis", style = {"text-align":"center", "font-size": "1.5vh"}),
                                ], md = 6)
                            ], direction = "horizontal", gap = 2, style = {"justify-content": "space-evenly", "margin-top": "1.666vh", "margin-bottom": "1vh"}),
                            html.H1(id = "btresult2", className = "text-body-secondary", style = {"text-align":"center", "font-size": "2vh"}),
                        ])
                    ],  color = "light", outline = True,
                        style = {"margin-top": "7vh",
                                "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                "color": "#FFFFFF"})
                ], md = 3),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H1(id = "btstock3", className = "text-body-secondary", style = {"text-align":"center", "font-size": "2vh"}),
                            dbc.Stack([
                                dbc.Col([
                                    html.H1("Inicial", className = "text-body-secondary", style = {"text-align":"center", "font-size": "1.5vh"}),
                                    html.H1(id = "btvalue3s", className = "text-dark-emphasis", style = {"text-align":"center", "font-size": "1.5vh"}),
                                ], md = 6),
                                dbc.Col([
                                    html.H1("Final", className = "text-body-secondary", style = {"text-align":"center", "font-size": "1.5vh"}),
                                    html.H1(id = "btvalue3f", className = "text-dark-emphasis", style = {"text-align":"center", "font-size": "1.5vh"}),
                                ], md = 6)
                            ], direction = "horizontal", gap = 2, style = {"justify-content": "space-evenly", "margin-top": "1.666vh", "margin-bottom": "1vh"}),
                            html.H1(id = "btresult3", className = "text-body-secondary", style = {"text-align":"center", "font-size": "2vh"}),
                        ])
                    ],  color = "light", outline = True,
                        style = {"margin-top": "7vh",
                                "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                "color": "#FFFFFF"})
                ], md = 3),
 
            ], style = {"justify-content": "space-evenly"}),


            dbc.Row([

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H1(id = "btstock4", className = "text-body-secondary", style = {"text-align":"center", "font-size": "2vh"}),
                            dbc.Stack([
                                dbc.Col([
                                    html.H1("Inicial", className = "text-body-secondary", style = {"text-align":"center", "font-size": "1.5vh"}),
                                    html.H1(id = "btvalue4s", className = "text-dark-emphasis", style = {"text-align":"center", "font-size": "1.5vh"}),
                                ], md = 6),
                                dbc.Col([
                                    html.H1("Final", className = "text-body-secondary", style = {"text-align":"center", "font-size": "1.5vh"}),
                                    html.H1(id = "btvalue4f", className = "text-dark-emphasis", style = {"text-align":"center", "font-size": "1.5vh"}),
                                ], md = 6)
                            ], direction = "horizontal", gap = 2, style = {"justify-content": "space-evenly", "margin-top": "1.666vh", "margin-bottom": "1vh"}),
                            html.H1(id = "btresult4", className = "text-body-secondary", style = {"text-align":"center", "font-size": "2vh"}),
                        ])
                    ],  color = "light", outline = True,
                        style = {"margin-top": "5vh",
                                "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                "color": "#FFFFFF"})
                ], md = 3),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H1(id = "btstock5", className = "text-body-secondary", style = {"text-align":"center", "font-size": "2vh"}),
                            dbc.Stack([
                                dbc.Col([
                                    html.H1("Inicial", className = "text-body-secondary", style = {"text-align":"center", "font-size": "1.5vh"}),
                                    html.H1(id = "btvalue5s", className = "text-dark-emphasis", style = {"text-align":"center", "font-size": "1.5vh"}),
                                ], md = 6),
                                dbc.Col([
                                    html.H1("Final", className = "text-body-secondary", style = {"text-align":"center", "font-size": "1.5vh"}),
                                    html.H1(id = "btvalue5f", className = "text-dark-emphasis", style = {"text-align":"center", "font-size": "1.5vh"}),
                                ], md = 6)
                            ], direction = "horizontal", gap = 2, style = {"justify-content": "space-evenly", "margin-top": "1.666vh", "margin-bottom": "1vh"}),
                            html.H1(id = "btresult5", className = "text-body-secondary", style = {"text-align":"center", "font-size": "2vh"}),
                        ])
                    ],  color = "light", outline = True,
                        style = {"margin-top": "5vh",
                                "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                "color": "#FFFFFF"})
                ], md = 3),

                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H1(id = "btstock6", className = "text-body-secondary", style = {"text-align":"center", "font-size": "2vh"}),
                            dbc.Stack([
                                dbc.Col([
                                    html.H1("Inicial", className = "text-body-secondary", style = {"text-align":"center", "font-size": "1.5vh"}),
                                    html.H1(id = "btvalue6s", className = "text-dark-emphasis", style = {"text-align":"center", "font-size": "1.5vh"}),
                                ], md = 6),
                                dbc.Col([
                                    html.H1("Final", className = "text-body-secondary", style = {"text-align":"center", "font-size": "1.5vh"}),
                                    html.H1(id = "btvalue6f", className = "text-dark-emphasis", style = {"text-align":"center", "font-size": "1.5vh"}),
                                ], md = 6)
                            ], direction = "horizontal", gap = 2, style = {"justify-content": "space-evenly", "margin-top": "1.666vh", "margin-bottom": "1vh"}),
                            html.H1(id = "btresult6", className = "text-body-secondary", style = {"text-align":"center", "font-size": "2vh"}),
                        ])
                    ],  color = "light", outline = True,
                        style = {"margin-top": "5vh",
                                "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                "color": "#FFFFFF"})
                ], md = 3),
 
            ], style = {"justify-content": "space-evenly"}),

        ]),


        html.Div([
                html.Img(src = imageLogo, style = {"height": "8vh", "margin-top": "11vh","margin-bottom": "11vh"})
        ], style = {"display" : "flex", "justifyContent" : "center"})

    ], md = 12),

], fluid = True)



rightBacktest = dbc.Container(children=[

    #Right Column
    dbc.Col([

        dcc.Loading(id = "loading2", type = "cube", children = [

            dbc.Row([
                #aqui estarão as 6 ações selecionadas no backtest
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Backtest Stocks", className = "text-light", style = {"text-align":"center", "font-size":"1.75vh"}),
                        dcc.Graph(id = "btstocks", style = {"height": "37vh"}), 
                    ], style = {"margin-top": "2.5vh"}, color = "dark"),
                ], md = 11),

            ], style = {"justify-content": "space-evenly"}),


            dbc.Row([
                #aqui estará um gráfico mostrando a comparação do backtest com o ibovespa e o cdi (adicionar o cdi após o código já estar em funcionamento)
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Backtest x IBOV", className = "text-light", style = {"text-align":"center", "font-size":"1.75vh"}),
                        dcc.Graph(id = "btIBOV", style = {"height": "37vh"}), 
                    ], style = {"margin-top": "2.5vh"}, color = "dark"),
                ], md = 11),

            ], style = {"justify-content": "space-evenly"}),
        
        ])
    
    ])

])





##====================================================================================================##
#Web Pre-Builds -> Strategy Page
##====================================================================================================##


leftStrategy = dbc.Container(children=[

    dbc.Col([

        html.H1("Convergência das Medias Móveis", style = {"margin-top": "4vh", "text-align": "center", "font-size": "2.5vh"}),
        html.P("Sharpy é baseado em dois pilares:", style = {"margin-top": "2vh", "text-align": "center", "font-size": "2vh"}),

        dbc.Row([

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Primeiro Pilar", style = {"text-align": "center", "font-size":"2vh"}),
                    dbc.CardBody("Relação risco retorno das ações. Origem do nome do robô, referência ao Índice Sharpe.", 
                                 style = {"text-align": "center", "font-size":"1.75vh"})
                ],  color = "light", outline = True, 
                    style = {"height": "100%", "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)"}),
            ], style = {"margin-top": "2vh"}, md = 5),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Segundo Pilar", style = {"text-align": "center", "font-size":"2vh"}),
                    dbc.CardBody("Médias móveis (MM). As ações com as melhores MMs serão escolhidas para compor a carteira.", style = {"text-align": "center", "font-size":"1.75vh"})
                ],  color = "light", outline = True, 
                    style = {"height": "100%", "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)"}),
            ], style = {"margin-top": "2vh"}, md = 5),

        ], style = {"justify-content": "space-evenly"}),

     

        html.H1("A União dos Pilares", style = {"margin-top": "4vh", "text-align": "center", "font-size": "2vh"}),

        dbc.Row([

            dbc.Col([
                dbc.Card([
                    html.P("A seleção das ações é feita a partir da média móvel da relação risco retorno de cada ativo. " 
                    "Para tal, calculamos MMs para 3 períodos, longo prazo (180 dias), médio prazo (60 dias) e curto prazo (12 dias). "
                    "A filtragem tem início no período de 180 dias. Ações que desempenham bem nesse período passam para a próxima peneira. "
                    "Da mesma forma, ações que apresentam bom desempenho no médio prazo, passam para a última seleção. "
                    "Ao final, selecionamos as 6 ações que possuem melhor MM de curto prazo, realizando assim a operação denominada Convergência de Fluxo.",
                    style = {"text-align": "center", "font-size": "1.5vh"}),
                ], outline = True, color = "light")  
            ], md = 10),
        
        ], style = {"justify-content": "center"}),



        dbc.Row([

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Difusor de Fluxo", style = {"text-align": "center", "font-size":"1.75vh"}),
                    dbc.CardBody("A convergência de fluxo é uma estratégia baseada no Difusor de Fluxo, do Analista André de Moraes (ex Analista Chefe da XP). "
                                "A estratégia baseia-se na análise de 3 períodos para um ativo de interesse, longo, médio e curto prazo. "
                                "De forma simplificada, ativos que possuem tendência de alta nos 3 períodos, podem ter seu Difusor de Fluxo analisado. "
                                "O difusor é um gráfico formado por 3 MMs, longo, médio e curto prazo. "
                                "Ativos que com MM de curto e médio prazo em alta que tenham acabado de superar a MM de longo prazo, tornam-se fortes candidatos a compra. ", 
                                style = {"text-align": "center", "font-size":"1.5vh"})
                ],  color = "light", outline = True,
                    style = {"height": "100%", "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)"}),
            ], style = {"margin-top": "2vh"}, md = 5),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Conversor de Fluxo", style = {"text-align": "center", "font-size":"1.75vh"}),
                    dbc.CardBody("A convergência de fluxo parte do princípio das MMs de 3 prazos, mas substitui uma simples MM baseada no preço da ação por uma relação de risco retorno. "
                                "Desta forma, ações com melhor risco restorno no longo, médio e principalmente curto prazo são selecionadas para formarem a carteira. "
                                "O prazo ideal para duração das operações foi estipulado entre 15 e 60 dias, momento em que é recomendada uma nova análise e possível reformulação da carteira de ações.", 
                                style = {"text-align": "center", "font-size":"1.5vh"})
                ],  color = "light", outline = True, 
                    style = {"height": "100%", "justify-content": "center", "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)"}),
            ], style = {"margin-top": "2vh"}, md = 5),

        ], style = {"justify-content": "space-evenly"}),
        
    ])

], fluid = True)



rightStrategy = dbc.Container(children=[

    dbc.Col([
            
        dbc.Card([

            dbc.CardHeader("O Robozinho", style = {"text-align": "center", "font-size":"2vh"}),

            dbc.CardBody([
            
                dbc.Stack([

                    dbc.Col([
                        html.P(
                            "Olá, eu sou o Sharpy, o robô quantitativo criado por alunos da FinancEEL. "
                            "Minha principal função é a elaboração de carteiras de ações para prazos entre 15 e 60 dias, com base em ativos do IBrX50.",
                            style = {"margin-bottom": "1rem", "text-align": "start", "font-size":"1.75vh"}
                        )
                    ], style = {"height": "100%"}, md = 9),

                    dbc.Col(html.Img(src = imageSharp, style = {"height": "15vh"}), style = {"text-align":"center"}, md = 3),

                ], direction = "horizontal"),

                html.P(
                    "A interface que você está utilizando foi feita para facilitar a visualização dos meus resultados, "
                    "em uma tentativa de imaginar como seria possível distribuir o acesso a um robô como eu. ",
                    style = {"margin-bottom": "1rem", "text-align": "start", "font-size":"1.75vh"}
                ),

                html.P(
                    "Ei, antes de ir embora, gostaria de te contar uma coisa. "
                    "O Sharpy também funciona em celulares, caso tenha interesse, de uma checadinha.",
                    style = {"margin-bottom": "0rem", "text-align": "start", "font-size":"1.75vh"}
                )

            ]),


            html.Hr(style = {"margin-top": "0rem", "margin-bottom": "0rem"}),


            html.H1("Meus Desenvolvedores", style = {"margin-top": "3vh", "font-size":"2vh", "text-align": "center"}),


            dbc.Row([

                
                dbc.Col([

                    dbc.Row([

                        dbc.Card(html.Img(src = dev1, style = {"margin-top": "1vh", "margin-bottom": "1vh", "height": "100%", "width": "100%"}), style = {"text-align": "center"}),

                        dbc.Card([
                            html.H1("Felipe Dovigo", className = "g-0", style = {"margin-top": "1vh", "font-size": "1vh"}),

                            dbc.NavItem([
                                dbc.NavLink([
                                    html.I(className = "bi bi-linkedin"), 
                                ], className = "g-0", href = "https://www.linkedin.com/in/felipe-dovigo/", external_link = True, style = {"margin-bottom": "0.75vh", "color": "#c0c0c0", "display": "flex", "justify-content":"center"}), 
                            ], style = {"width": "100%"}),

                        ], style = {"display": "flex", "text-align": "center"}),

                    ], style = {"margin-top": "0.5vh", "margin-bottom": "1vh", "max-width": "20vh"}),

                ], style = {"margin-top": "1vh", "margin-bottom": "2vh", "display" : "flex", "justify-content" : "space-evenly"}, md = 2),


                dbc.Col([

                    dbc.Row([

                        dbc.Card(html.Img(src = dev2, style = {"margin-top": "1vh", "margin-bottom": "1vh", "height": "100%", "width": "100%"}), style = {"text-align": "center"}),

                        dbc.Card([
                            html.H1("Beatriz Nogueira", className = "g-0", style = {"margin-top": "1vh", "font-size": "1vh"}),

                            dbc.NavItem([
                                dbc.NavLink([
                                    html.I(className = "bi bi-linkedin"), 
                                ], className = "g-0", href = "https://www.linkedin.com/in/beatriz-n-lourenço/", external_link = True, style = {"margin-bottom": "0.75vh", "color": "#c0c0c0", "display": "flex", "justify-content":"center"}), 
                            ], style = {"width": "100%"}),

                        ], style = {"display": "flex", "text-align": "center"}),

                    ], style = {"margin-top": "0.5vh", "margin-bottom": "1vh", "max-width": "20vh"}),

                ], style = {"margin-top": "1vh", "margin-bottom": "2vh", "display" : "flex", "justify-content" : "space-evenly"}, md = 2),


                dbc.Col([

                    dbc.Row([

                        dbc.Card(html.Img(src = dev3, style = {"margin-top": "1vh", "margin-bottom": "1vh", "height": "100%", "width": "100%"}), style = {"text-align": "center"}),

                        dbc.Card([
                            html.H1("Julia Oliveira", className = "g-0", style = {"margin-top": "1vh", "font-size": "1vh"}),

                            dbc.NavItem([
                                dbc.NavLink([
                                    html.I(className = "bi bi-linkedin"), 
                                ], className = "g-0", href = "https://www.linkedin.com/in/júliaribmo/", external_link = True, style = {"margin-bottom": "0.75vh", "color": "#c0c0c0", "display": "flex", "justify-content":"center"}), 
                            ], style = {"width": "100%"}),

                        ], style = {"display": "flex", "text-align": "center"}),

                    ], style = {"margin-top": "0.5vh", "margin-bottom": "1vh", "max-width": "20vh"}),

                ], style = {"margin-top": "1vh", "margin-bottom": "2vh", "display" : "flex", "justify-content" : "space-evenly"}, md = 2),


            ], className = "g-0", style = {"justify-content" : "space-evenly"})


        ], style = {"margin-top": "7vh", "margin-botoom": "2vh"})

    ], md = 11)

], fluid = True)





##====================================================================================================##
#Web Layout
##====================================================================================================##


leftContent = dbc.Col(id = "left-content")
rightContent = dbc.Col(id = "right-content")


app.layout = dbc.Container(children=[

    #URL Read
    dcc.Location(id = "url"),

    dbc.Navbar(className = "bg-dark", children = [

        dbc.Container([


            dbc.Row([
                dbc.Col(html.Img(src = imageIndex, style = {"height": "3.5vh"}), 
                        style = {"margin-left": "2vh", "margin-top": "0.5vh", "margin-bottom": "0.5vh", "display" : "flex", "justifyContent" : "center"}),  
            ], className = "g-0", align = "center"),


            dbc.NavbarToggler (id = "nav-toggler", n_clicks = 0),
            dbc.Collapse(id = "nav-collapse", children = [

                dbc.Row([
                    dbc.Col([
                        dbc.Nav([
                            dbc.NavItem(dbc.NavLink("Home", className = "text-light", style = {"font-size": "2vh"}, active = "exact", href = "/"), className = "btn btn-dark"),
                            dbc.NavItem(dbc.NavLink("Backtest", className = "text-light", style = {"font-size": "2vh"}, active = "exact", href = "/backtest"), className = "btn btn-dark"),
                            dbc.NavItem(dbc.NavLink("Strategy", className = "text-light", style = {"font-size": "2vh"}, active = "exact", href = "/strategy"), className = "btn btn-dark"),
                        ], navbar = True),
                    ]),
                ],className = "g-0", align = "center", style = {"margin-left": "3vh"}),

                dbc.Row([
                    dbc.Col([
                        dbc.Nav([
                            dbc.NavItem(dbc.NavLink(html.I(className = "bi bi-linkedin"), href = "https://www.linkedin.com/company/financeel-liga-de-mercado-financeiro-da-eel-usp/?originalSubdomain=br", external_link = True, style = {"margin-top": "1vh", "color": "#c0c0c0"})),
                            dbc.NavItem(dbc.NavLink(html.I(className = "bi bi-instagram"), href = "https://www.instagram.com/_financeel/", external_link = True, style = {"margin-top": "1vh", "color": "#c0c0c0"})),
                        ], navbar = True),
                    ]),
                ],className = "g-0 ms-auto", align = "center", style = {"margin-left": "2vh"} )

            ], navbar = True, is_open = False),

        ], fluid = True)
        
    ], style = {"padding": "0.75vh"}),
    

    dbc.Row([

        dbc.Col(id = "colleft", children = [
            leftContent
        ], md = ()),
        
        dbc.Col(id = "colright", children = [
            rightContent
        ], md = ())

    ], className = "g-0")


], className = "g-0", fluid = True)





##====================================================================================================##
#Web Interactivity
##====================================================================================================##

@app.callback(
    [
    Output("left-content", "children"),
    Output("right-content", "children"),
    Output("colleft", "md"),
    Output("colright", "md"),
    ],
    [
    Input("url", "pathname")
    ]
)

def render_page(pathname):

    if pathname == "/" or pathname == "/sharpy":
        colleft = 6
        colright = 6
        return leftSharpy, rightSharpy, colleft, colright
    
    if pathname == "/backtest":
        colleft = 7
        colright = 5
        return leftBacktest, rightBacktest, colleft, colright
    
    if pathname == "/strategy":
        colleft = 8
        colright = 4
        return leftStrategy, rightStrategy, colleft, colright





##====================================================================================================##
#Web Interactivity -> Sharpy Page
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

    #aparentemente "date" não é recebido como data, mas sim como string, tendo isso em vista, não é possível realizar
    #a operação de subtração com a função timedelta
    presentDate = datetime.strptime(date, "%Y-%m-%d").date()
    pastDate = presentDate - dt.timedelta(long)

    #Stock Portfolio
    lStockValue, lStockReturn, lBestStocks = LongStockFilter(archive, presentDate, pastDate, lSample)
    mBestStocks = MidStockFilter(lStockReturn, lBestStocks, mSample, mid)
    sBestStocks = ShortStockFilter(lStockReturn, mBestStocks, sSample, short)

    #Dash
    stockInDash, figInDash = ShowInDash(lStockValue, lStockReturn, sBestStocks)

    stock1 = (stockInDash.index[0]).split(".")[0]
    stock2 = (stockInDash.index[1]).split(".")[0]
    stock3 = (stockInDash.index[2]).split(".")[0]
    stock4 = (stockInDash.index[3]).split(".")[0]
    stock5 = (stockInDash.index[4]).split(".")[0]
    stock6 = (stockInDash.index[5]).split(".")[0]

    value1 = "R$ "+ str(format(stockInDash[0], ".2f")) 
    value2 = "R$ "+ str(format(stockInDash[1], ".2f"))
    value3 = "R$ "+ str(format(stockInDash[2], ".2f"))
    value4 = "R$ "+ str(format(stockInDash[3], ".2f"))
    value5 = "R$ "+ str(format(stockInDash[4], ".2f"))
    value6 = "R$ "+ str(format(stockInDash[5], ".2f"))


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





##====================================================================================================##
#Web Interactivity -> Backtest Calc
##====================================================================================================##


@app.callback(
    [
    #StockCards OutPut
    Output(component_id = "btstock1", component_property = "children"),
    Output(component_id = "btstock2", component_property = "children"),
    Output(component_id = "btstock3", component_property = "children"),
    Output(component_id = "btstock4", component_property = "children"),
    Output(component_id = "btstock5", component_property = "children"),
    Output(component_id = "btstock6", component_property = "children"),
    Output(component_id = "btvalue1s", component_property = "children"),
    Output(component_id = "btvalue2s", component_property = "children"),
    Output(component_id = "btvalue3s", component_property = "children"),
    Output(component_id = "btvalue4s", component_property = "children"),
    Output(component_id = "btvalue5s", component_property = "children"),
    Output(component_id = "btvalue6s", component_property = "children"),
    Output(component_id = "btvalue1f", component_property = "children"),
    Output(component_id = "btvalue2f", component_property = "children"),
    Output(component_id = "btvalue3f", component_property = "children"),
    Output(component_id = "btvalue4f", component_property = "children"),
    Output(component_id = "btvalue5f", component_property = "children"),
    Output(component_id = "btvalue6f", component_property = "children"),
    Output(component_id = "btresult1", component_property = "children"),
    Output(component_id = "btresult2", component_property = "children"),
    Output(component_id = "btresult3", component_property = "children"),
    Output(component_id = "btresult4", component_property = "children"),
    Output(component_id = "btresult5", component_property = "children"),
    Output(component_id = "btresult6", component_property = "children"),
    #Graphic OutPut
    Output(component_id = "btstocks", component_property = "figure"),
    Output(component_id = "btIBOV", component_property = "figure"),
    ],

    [
    #Date Input
    Input(component_id = "btdate-select", component_property = "date"),
    ]
)

def updatebt(date):

    btpresentDate = datetime.strptime(date, "%Y-%m-%d").date()
            
    #BackTest (need to automize Date and Interaction selection)
    #revenue é uma lista das sBestStocks e seu produto (exemplo: PETR4 2.03%, etc)
    #revenueMean é uma lista que contém apenas 1 resultado (exemplo: BackTest 3.72%)
    #revenueAcumulated é um df que contém as ações e os retornos acumulados respectivos a cada dia

    #Stock Portfolio
    lStockValue, lStockReturn, sBestStocks, rcStockValue, rcResult, rcResultMean, rcAcumulated = BackTest(archive, btpresentDate, lSample, mSample, sSample, long, mid, short)
    IBOVresult, IBOVacumulated = RevenueIBOV(btpresentDate, "^BVSP")
    #print(btIBOVAcumulated)


    #Dash
    stockInDashStart, stockInDashEnd = BtShowInDash(rcStockValue, sBestStocks)


    btstock1 = (stockInDashStart.index[0]).split(".")[0]
    btstock2 = (stockInDashStart.index[1]).split(".")[0]
    btstock3 = (stockInDashStart.index[2]).split(".")[0]
    btstock4 = (stockInDashStart.index[3]).split(".")[0]
    btstock5 = (stockInDashStart.index[4]).split(".")[0]
    btstock6 = (stockInDashStart.index[5]).split(".")[0]

    btvalue1s = "R$"+ str(format(stockInDashStart[0], ".2f")) 
    btvalue2s = "R$"+ str(format(stockInDashStart[1], ".2f"))
    btvalue3s = "R$"+ str(format(stockInDashStart[2], ".2f"))
    btvalue4s = "R$"+ str(format(stockInDashStart[3], ".2f"))
    btvalue5s = "R$"+ str(format(stockInDashStart[4], ".2f"))
    btvalue6s = "R$"+ str(format(stockInDashStart[5], ".2f"))

    btvalue1f = "R$"+ str(format(stockInDashEnd[0], ".2f")) 
    btvalue2f = "R$"+ str(format(stockInDashEnd[1], ".2f"))
    btvalue3f = "R$"+ str(format(stockInDashEnd[2], ".2f"))
    btvalue4f = "R$"+ str(format(stockInDashEnd[3], ".2f"))
    btvalue5f = "R$"+ str(format(stockInDashEnd[4], ".2f"))
    btvalue6f = "R$"+ str(format(stockInDashEnd[5], ".2f"))

    btresult1 = str(format(((stockInDashEnd[0] / stockInDashStart[0])-1)*100, ".2f")) +"%"
    btresult2 = str(format(((stockInDashEnd[1] / stockInDashStart[1])-1)*100, ".2f")) +"%"
    btresult3 = str(format(((stockInDashEnd[2] / stockInDashStart[2])-1)*100, ".2f")) +"%"
    btresult4 = str(format(((stockInDashEnd[3] / stockInDashStart[3])-1)*100, ".2f")) +"%"
    btresult5 = str(format(((stockInDashEnd[4] / stockInDashStart[4])-1)*100, ".2f")) +"%"
    btresult6 = str(format(((stockInDashEnd[5] / stockInDashStart[5])-1)*100, ".2f")) +"%"

    #btresult1 = str(format(45.35 / 41.54, ".2f")) +"%" = 

    revenueMeanxTime = pd.DataFrame()
    revenueMeanxTime["BackTest"] = rcAcumulated.sum(axis = 1)
    revenueMeanxTime = revenueMeanxTime / len(rcAcumulated.columns)
    revenueMeanxTime["IBOV"] = IBOVacumulated


    #Figure
    btstocks = BtFigureBuild(rcAcumulated)
    btIBOV = BtFigureBuild(revenueMeanxTime)

   
    return (btstock1, btstock2, btstock3, btstock4, btstock5, btstock6,
            btvalue1s, btvalue2s, btvalue3s, btvalue4s, btvalue5s, btvalue6s,
            btvalue1f, btvalue2f, btvalue3f, btvalue4f, btvalue5f, btvalue6f,
            btresult1, btresult2, btresult3, btresult4, btresult5, btresult6,
            btstocks, btIBOV)





##====================================================================================================##
#App Styling
##====================================================================================================##

@app.callback(
    Output("nav-collapse", "is_open"),
    [
    Input("nav-toggler", "n_clicks")
    ],
    [
    State("nav-collapse", "is_open") 
    ]
)

def toggle_nav_collapse(n, is_open):

    if n:
        return not is_open
    return is_open










##====================================================================================================##
#Other Functions
##====================================================================================================##

if __name__ == "__main__":
    app.run_server(debug = True)

