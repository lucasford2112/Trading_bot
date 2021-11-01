import websocket, json, pprint, talib, numpy, config
from binance.enums import *
from binance.client import Client

# Read the price data from:
Socket = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"

# Number of periods that the algorithm takes into account
RSE_period = 14
# Upper threshold value:
RSI_Overbought = 70
# Lower threshold value:
RSI_Oversold = 30
# Trading pair:
Trade_Symbol = 'ETHUSDT'
# Trading quantity:
Trade_Quantity = 0.005
# We will use the following to check if we're in or out of a trade 
in_position = False

# This list will contain al previous closing values for the selected trading pair and timeframe
closes = []

# This is how we access the Binance API, as documented here: https://python-binance.readthedocs.io/en/latest/ 
# The keys are stored in a separate text file
client = Client(config.API_KEY, config.API_SECRET)

# Define a function to place an order:
def order(side,quantity,symbol,order_type=ORDER_TYPE_MARKET):
    try: 
        print("Sending Order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False
    
    return True

# Define a function to confirm we're connected to the socket:
def on_open(ws):
    print("Connection opened")

# Define a function to confirm we're no longer connected to the socket:
def on_close(ws):
    print("Connection closed")

# The data  we receive are 1 minute candles. From the Binance web socket documentation, 
# we obtain this information about each candle:
"""{
  "e": "kline",     // Event type
  "E": 123456789,   // Event time
  "s": "BNBBTC",    // Symbol
  "k": {
    "t": 123400000, // Kline start time
    "T": 123460000, // Kline close time
    "s": "BNBBTC",  // Symbol
    "i": "1m",      // Interval
    "f": 100,       // First trade ID
    "L": 200,       // Last trade ID
    "o": "0.0010",  // Open price
    "c": "0.0020",  // Close price
    "h": "0.0025",  // High price
    "l": "0.0015",  // Low price
    "v": "1000",    // Base asset volume
    "n": 100,       // Number of trades
    "x": false,     // Is this kline closed?
    "q": "1.0000",  // Quote asset volume
    "V": "500",     // Taker buy base asset volume
    "Q": "0.500",   // Taker buy quote asset volume
    "B": "123456"   // Ignore
  }
}""" 
# With this function, we extract the information we need from each candle:
def on_message(ws,message):
    global closes, in_position

    #print("Message received")
    json_message = json.loads(message)
    #pprint.pprint(json_message)
     
    # We grab the whole candle dictionary:
    candle = json_message['k']

    # We grab the boolean for whether or not the candle is closed:
    is_candle_closed = candle['x']

    # We grab the close price:
    close = candle['c']

    # Append each closing value to the list created at the beginning:
    if is_candle_closed:
        print("candle closed at {}".format(close))
        closes.append(float(close))
        print('closes')
        print(closes)

        # If we have more than 14 closing values, start calculating the RSI:
        if len(closes) > RSE_period:
            np_closes = numpy.array(closes)
            rsi = talib.RSI(np_closes, RSE_period)
            #print('Calculated RSIs')
            #print(rsi)
            last_rsi = rsi[-1]
            print('the current RSI is {}'.format(last_rsi))

            # If the last RSI value is higher than 70 and we are not already out, sell:
            if last_rsi > RSI_Overbought:
                if in_position:
                    print('Overbought, Sell!')
                    order_succeeded = order(SIDE_SELL,Trade_Quantity,Trade_Symbol)
                    if order_succeeded:
                        in_position = False
                else:
                    print('Looking from outside!')

            # If the last RSI value is lower than 30 and we are not already in, buy:
            if last_rsi < RSI_Oversold:
                if in_position:
                    print('Already in!')
                else:
                    print('Oversold, Buy!')
                    order_succeeded = order(SIDE_BUY,Trade_Quantity,Trade_Symbol)
                    if order_succeeded:
                        in_position = True


# The instructions to run the bot based on the previous functions:
ws = websocket.WebSocketApp(Socket, on_open=on_open ,on_close=on_close , on_message = on_message)
ws.run_forever()



