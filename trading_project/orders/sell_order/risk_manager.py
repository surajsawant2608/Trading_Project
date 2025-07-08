from orders.sell_order.sell_executor import place_order
class RiskManager:
    def __init__(self, token, symbol, stack, total_qty, user_id, on_exit_callback=None, step_percent=3, max_stack=3):
        self.token = token
        self.symbol = symbol
        self.stack = stack[:]
        self.total_qty = total_qty
        self.remaining_qty = total_qty
        self.partial_exit_done = False
        self.step_percent = step_percent
        self.max_stack = max_stack
        self.exit_done = False
        self.user_id = user_id
        self.on_exit_callback = on_exit_callback
        self.logs = []

    def log(self, msg):
        self.logs.append(msg)
        print(msg)

    def process_price(self, price):
        if self.exit_done:
            return

        self.log(f"\n💹 {self.symbol} Price: ₹{price}")

        if price <= self.stack[0]:
            self.log(f"🛑 SL ₹{self.stack[0]} hit → Exit all ({self.remaining_qty}) at ₹{price}")
            place_order(self.user_id, self.symbol, self.token, self.remaining_qty)
            self.remaining_qty = 0
            self.exit_done = True
            if self.on_exit_callback:
                self.on_exit_callback(reason="sl", price=price)
            return

        if not self.partial_exit_done and price >= self.stack[2]:
            exit_qty = round(self.total_qty * 0.75)
            self.remaining_qty -= exit_qty
            self.partial_exit_done = True
            self.log(f"🎯 Target ₹{self.stack[2]} hit → Exit 75% ({exit_qty}) at ₹{price}. Remaining: {self.remaining_qty}")
            place_order(self.user_id, self.symbol, self.token, exit_qty)

        if self.partial_exit_done and self.remaining_qty > 0:
            while price > self.stack[-1]:
                next_level = round(self.stack[-1] * (1 + self.step_percent / 100), 2)
                self.stack.append(next_level)
                if len(self.stack) > self.max_stack:
                    self.stack.pop(0)
                self.log(f"📈 New target added: ₹{next_level}")

            if price <= self.stack[0]:
                self.log(f"🛑 Trailing SL ₹{self.stack[0]} hit → Exit remaining {self.remaining_qty} at ₹{price}")
                place_order(self.user_id, self.symbol, self.token, self.remaining_qty)
                self.remaining_qty = 0
                self.exit_done = True
                if self.on_exit_callback:
                    self.on_exit_callback(reason="trailing_sl", price=price)
                return

            self.log(f"📊 Trailing Stack: SL ₹{self.stack[0]}, Target ₹{self.stack[1]}, Next ₹{self.stack[2]}")
