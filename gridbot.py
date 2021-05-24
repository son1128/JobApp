import config
import json
import websocket
from binance.client import Client
from binance.enums import *


client = Client(config.api_key, config.api_secret, tld="com")


# loose functions
def decimal_places_from_string(input_string):
    # input a string of the market price, extracted from binance data

    input_float = float(input_string)
    input_int = int(input_float)

    # number of digits in total
    total_digits = len(input_string)

    # number of digits before decimal point
    digits_before_decimal = len(str(input_int))

    # if no decimal point...
    if total_digits == digits_before_decimal:
        return 0

    # if there is decimal point...
    else:
        digits_after_decimal = (total_digits - (digits_before_decimal + 1))
        return digits_after_decimal


# --- Classes required
# myAccount     - Calculating info about assets available on exchange (Binance in this case)
# myWS          - Used to save and retrieve websocket data
# Gridbot
# Gridlines     - Individual gridlines assigned to the gridbot
class myAccount:
    # --- This class is used to calculate information about the assets available on the exchange etc.
    def __init__(self, client):
        self.client = client
        self.prebots = []           # where bots go before becoming active
        self.active_bots = []       # where active bots go :)

    def get_balance_info(self, pairing):
        exchange_info = self.client.get_exchange_info()
        symbols = exchange_info["symbols"]
        for x in symbols:
            if x['symbol'] == pairing.upper():
                base_asset = x['baseAsset']
                quote_asset = x['quoteAsset']
                break

        # counting the amount of base and quote assets in your account
        account = self.client.get_account()
        balances = account["balances"]

        asset_counter = 2
        while asset_counter > 0:
            for x in balances:
                if x['asset'] == base_asset:
                    base_asset_free = x['free']
                    asset_counter -= 1

                elif x['asset'] == quote_asset:
                    quote_asset_free = x['free']
                    asset_counter -= 1

        print(f"{base_asset} free: {base_asset_free}")
        print(f"{quote_asset} free: {quote_asset_free}")

        output = [pairing, base_asset, base_asset_free,
                  quote_asset, quote_asset_free]
        self.prebots.append(output)

        return output

    def create_gridbot(self, pairing, grid_upper, grid_lower, investment, n_gridlines, entry_price=None, stop_loss=[False, 0], take_profits=[False, 0], trailing_up=[False, 0], trailing_down=[False, 0]):
        # check Gridbot class for explanation on above parameters

        # 1. create gridbot, and update Gridbot class to have added features, as above
        my_bot = Gridbot(pairing, grid_upper, grid_lower,
                         investment, n_gridlines)

        # 2. perform all buy/sell orders required to set up bot, eg. limit or market orders for any missing assets
        # this is done with the prior inputs, given above, as well as possibly an entry-price feature?

        # 3. populate all Gridlines within Gridbot class

        # 4. myAccount cleanup
        self.prebots.pop()
        self.active_bots.append(my_bot)
        print(f"{pairing} grid-bot has been set up successfully!")


class myWS:
    # --- This class is used to save and retrieve websocket data
    # 'pairing' refers to the trading pair, from which data is being requested from (eg. VET/BTC)
    # 'SOCKET' refers to the websocket accessed to present this data (this is determined by pairing)
    def __init__(self, pairing):
        self.pairing = pairing
        self.SOCKET = f"wss://stream.binance.com:9443/ws/{pairing}@kline_15m"
        self.openWS()

    def openWS(self):
        self.ws = websocket.WebSocketApp(
            self.SOCKET,
            on_open=lambda SOCKET: self.on_open(),
            on_close=lambda SOCKET: self.on_close(),
            on_message=lambda SOCKET, message: self.on_message(SOCKET, message))
        self.ws.run_forever()

    def on_open(self):
        pass

    def on_close(self):
        pass

    def on_message(self, ws, message):
        json_message = json.loads(message)
        self.market_price = json_message['k']['c']

        input_string = str(self.market_price)
        self.dp = decimal_places_from_string(input_string)

        self.ws.close()


class Gridbot:
    # --- This class 'Gridbot' refers to each individual bot set up in this fashion
    # 'pairing' refers to the trading pair (eg. VET/BTC)
    # 'grid_upper' refers to the highest sell order of the grid bot
    # 'grid_lower' refers to the lowest buy order of the grid bot
    # 'investment' refers to the amount of assets assigned in the quote asset (eg. BTC in VET/BTC)
    # 'n_gridlines' refers to the number of gridlines assigned to the bot
    # 'entry_price' refers to what price the assets are exchanged at in order to set up the bot
    # 'stop_loss' refers to whether the bot will immediately close, and sell all of the base asset into the quote asset after dropping to a set value
    # 'take_profits' refers to whether the bot will immediately close, and sell all of the base asset into the quote asset after creating a certain amount of profit
    # 'trailing_up' refers to whether the bot will trail and dynamically follow the market price when it rises out of range
    # 'trailing_down' refers to whether the bot will trail and dynamically follow the market price when it falls out of range (not advised)
    def __init__(self, pairing, grid_upper, grid_lower, investment, n_gridlines, entry_price=None, stop_loss=False, take_profits=False, trailing_up=False, trailing_down=False):
        self.pairing = pairing
        self.grid_upper = grid_upper
        self.grid_lower = grid_lower
        self.investment = investment
        self.n_gridlines = n_gridlines
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profits = take_profits
        self.trailing_up = trailing_up
        self.trailing_down = trailing_down

        self.grid_list = []
        self.bot_profits = 0
        self.invest_change = 0
        self.get_market_price()

    def get_market_price(self):
        WS = myWS(self.pairing)
        print(
            f"The current market price of {WS.pairing} is {WS.market_price}!")
        self.market_price = WS.market_price
        return self.market_price

    def check_stop_loss(self):
        if self.stop_loss != False:
            market_price = self.get_market_price()
            if self.stop_loss > market_price:
                print(
                    f"The market price of {self.pairing} has dropped below the stop-loss. All of the base asset will now be sold.")
                # 1. remove all grids
                for x in self.grid_list:
                    # cancel all orders
                    pass
                self.grid_list = []

                # 2. instantly place sell order
                pass

    def check_take_profits(self):
        if self.take_profits != False:
            if self.take_profits >= self.invest_change:
                print(
                    f"The {self.pairing} bot has made {self.invest_change}, and then successfully closed.")
                # 1. remove all grids
                for x in self.grid_list:
                    # cancel all orders
                    pass
                self.grid_list = []

                # 2. instantly place sell order
                pass

    def check_trailing_up(self):
        if self.trailing_up != False:
            market_price = self.get_market_price()
            if (market_price > self.grid_upper) and (self.trailing_up > self.grid_upper):
                # 1. remove bottom gridline
                pass
                # 2. generate generate top gridline

                # 3. update gridlist

    def check_trailing_down(self):
        if self.trailing_down != False:
            market_price = self.get_market_price()
            if (self.grid_lower > market_price) and (self.grid_lower > self.trailing_down):
                # 1. remove top gridline
                pass
                # 2. generate generate bottom gridline

                # 3. update gridlist

    def generate_gridlines(self):
        # space from lowest and highest gridline
        self.grid_span = (self.grid_upper - self.grid_lower)

        # spacing between each gridline
        grid_step_float = (self.grid_span / self.n_gridlines)

        self.grid_step = (
            ((((self.grid_upper / self.grid_lower) - 1) * 100) / self.n_gridlines))
        formatted_grid_step = f"{round(self.grid_step, 2)}"

        # investment placed on each gridline
        self.invest_per_grid = (self.investment / self.n_gridlines)
        formatted_invest_per_grid = f"{round(self.invest_per_grid, pairing_decimals)}"

        # make a loop to make a list, add each gridline to list in sequence
        decimal_places = decimal_places_from_string(self.market_price)
        temp_buy_list = []
        temp_sell_list = []

        # grids for buy orders
        for x in range(self.n_gridlines):
            line_x = (self.grid_lower + (grid_step_float * x))
            line_x = round(line_x, decimal_places)
            temp_buy_list.append(line_x)

        # grids for sell orders
        for x in range(self.n_gridlines):
            line_x = (self.grid_lower + (grid_step_float * (x + 1)))
            line_x = round(line_x, decimal_places)
            temp_sell_list.append(line_x)

        # creating grid class
        for x in range(self.n_gridlines):
            self.grid_list.append(
                Gridline(temp_buy_list[x], temp_sell_list[x]))

        print("grid_list:")
        for i in self.grid_list:
            print(i)

        print(f"There will be {self.n_gridlines} grid-lines")
        print(f"There will be a {formatted_grid_step}% grid-step")
        print(
            f"There will be {formatted_invest_per_grid} of {pairing.upper()} on each grid-line")


class Gridline:
    # --- This class 'Gridline' represents individual Gridlines within a Gridbot
    # 'buy_price' refers to the buying price of each gridline
    # 'sell_price' refers to the selling price of each gridline
    # 'buy_status' refers to whether there is a pending buy-order (True), or pending sell order (False)
    def __init__(self, buy_price, sell_price):
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.buy_status = False

    def __repr__(self):
        return (f"Buy Price: {self.buy_price} /// Sell Price: {self.sell_price} /// Buy Status: {self.buy_status}")

    def __str__(self):
        return (f"Buy Price: {self.buy_price} /// Sell Price: {self.sell_price} /// Buy Status: {self.buy_status}")


# 1. get bot settings (using fixed variables for initial setup)
test_account = myAccount(client)
pairing = "vetbtc"
grid_upper = 0.00000251
grid_lower = 0.00000215
investment = 0.0002  # btc
n_gridlines = 12
pairing_decimals = 6


# 2. check current price
test_bot_WS = myWS(pairing)
print(f"There are {test_bot_WS.dp} decimal places in this pairing!")


# 3. make list of what grid would look like
test_bot = Gridbot(pairing, grid_upper, grid_lower,
                   investment, n_gridlines)

test_bot.generate_gridlines()


# 4. sum the neccessary funds and check against current funds


# defining the base and quote assets of the pairing
[pairing, base_asset, base_asset_free,
 quote_asset, quote_asset_free] = test_account.get_balance_info(pairing)


# determine how many gridlines are above and below the market price
# for i in test_bot.grid_list:
#     if (float(test_bot.market_price) > i.buy_price):
#         i.buy_status = True

#     elif (float(test_bot.market_price) > i.sell_price):
#         i.buy_status = False

# num_buy_orders = 0
# num_sell_orders = 0
# for i in test_bot.grid_list:
#     print(i)
#     if i.buy_status:
#         num_buy_orders += 1
#     else:
#         num_sell_orders += 1

# print(f" Number of buy orders: {num_buy_orders}")
# print(f" Number of sell orders: {num_sell_orders}")

# base_asset_required = (num_sell_orders * test_bot.invest_per_grid)
# quote_asset_required = (num_buy_orders * test_bot.invest_per_grid) * \
#     ((float(test_bot.market_price) + test_bot.grid_lower) / 2)

# print(test_bot.invest_per_grid)

# print(f" Amount of base asset needed: {base_asset_required} {base_asset}")
# print(f" Amount of quote asset needed: {quote_asset_required} {quote_asset}")
