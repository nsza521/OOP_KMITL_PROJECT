import datetime

class System:
    def __init__(self):
        self.__account_list = []
        self.__item_list = []
        self.__sniper = []
        self.__coupon_list = []
        ##self.__catagories = []

    ##setup funcs
    def add_item(self,name,id,start_price,category,store,type = None,buy_price = None):
        if type == "buyable":
            self.__item_list.append(BuyableItem(buy_price,id,name,start_price,category,store))
        elif type is None:
            self.__item_list.append(Item(id,name,start_price,category,store))
        else:
            raise "Whaaaaaa"
    def add_coupon(self,coupon_code,discount):
        self.__coupon_list.append(Coupon(coupon_code,discount))

    def sign_up(self,user_name,password,id):
        self.__account_list.append(Account(user_name,password,id))

    def sign_in(self,user_name,password,):
        for acc in self.__account_list:
            if acc.user_name == user_name and acc.password == password:
                return acc.id
        return "Not Found"
    
    ##finders
    def find_account_by_id(self,acc_id):
        for acc in self.__account_list:
            if acc.get_id() == acc_id:
                return acc
    def find_item_by_id(self,item_id):
        for item in self.__item_list:
            if item.id == item_id:
                return item
    def find_coupon_by_code(self,coupon_code):
        for coupon in self.__coupon_list:
            if coupon.code == coupon_code:
                return coupon.discount
            
    #update
    def update_sniper(self,time):
        for sniper in self.__sniper:
            if sniper.on_time(time):
                if sniper.price > sniper.item.price:
                    sniper.account.bid(sniper.item,(sniper.price - sniper.item.price))
    def update_item(self,time):
        for item in self.__item_list:
            item.update(time)

    #create
    def create_sniper(self,item,acc,price):
        self.__sniper.append(Sniper(item,acc,price))

    #money_related
    def add_money_by_tranfer(self,amount,acc_id,slip_info):
        self.find_account_by_id(acc_id).add_credit(amount,slip_info)
    def add_money_by_card(self,acc_id,amount,payment_info):
        self.find_account_by_id(acc_id).add_credit(amount,"by card lol")
    def withdraw_credit(self,acc_id,amount):
        self.find_account_by_id(acc_id).withdraw_credit(amount)
    def see_transactions(self,acc_id):
        for transaction in self.find_account_by_id(acc_id).transaction:
            print(str(transaction))
    #auctions
    def bid(self,acc_id,item_id,amount):
        self.find_account_by_id(acc_id).bid(self.find_item_by_id(item_id),amount)
    def see_bid_history(self,item_id):
        for bid in self.find_item_by_id(item_id).bid_history:
            print(str(bid))
    def buy(self,acc_id,item_id):
        self.find_account_by_id(acc_id).buy(self.find_item_by_id(item_id))
    def see_cart(self,acc_id):
        self.find_account_by_id(acc_id).see_cart()
    def sniper(self,acc_id,item_id,price):
        if self.find_account_by_id(acc_id).check_credit(price) and price > self.find_item_by_id(item_id).price:
            self.create_sniper(self.find_item_by_id(item_id),self.find_account_by_id(acc_id),price)


    def pay_shipping_price(self,acc_id,item_id,coupon_code = None):
        if coupon_code is None:
            discount = 0
        elif self.find_coupon_by_code(coupon_code) is not None:
            discount = self.find_coupon_by_code(coupon_code).discount
        else :
            return "Wrong Code"
        self.find_account_by_id(acc_id).pay_shipping(self.find_item_by_id(item_id),discount)

class Account:
    def __init__(self,user_name,password,id):
        self.__user_name = user_name
        self.__password = password
        self.__id = id
        self.__credit = 0
        self.__cart = Cart()
        self.__transactions = []
        self.__bid_items = []

    #gettrs
    @property
    def id(self):
        return self.__id

    def add_credit(self,amount,payment):
        self.__credit += amount
        self.create_transaction("Add",amount,payment)
    def withdraw_credit(self,amount):
        if self.check_credit(amount):
            self.__credit -= amount
            self.create_transaction("Withdraw",amount,"Tranfer slip")
            return "Done"
        return self.check_credit(amount)
    def create_transaction(self,type,amount,payment):
        self.__transactions.append(Transaction(type,amount,"SCB",payment))
    def lock_cred(self,amount,mode = "lock"):
        if mode == "unlock":
            self.__credit += amount
        elif mode == "lock":
            self.__credit -= amount

    ###
    def add_to_cart(self,item):
        self.__cart.add_order(item)
    def see_cart(self):
        self.__cart.display_order()

    #validation
    def check_credit(self,amount):
        return self.__credit >= amount

    #auctions
    def bid(self,item,amount):
        if self == item.find_leader():
            R_cred = amount
        else:
            R_cred = item.price + amount
        if self.check_credit(R_cred):
            if item not in self.__bid_items:
                self.__bid_items.append(item)
            item.bidded(self,amount)
    def buy(self,item):
        if self == item.find_leader():
            R_cred = item.buy_price - item.price
        else:
            R_cred = item.buy_price
        if self.check_credit(R_cred):
            self.__credit -= item.buy_price
            item.bought(self)
            self.add_to_cart(item)
    def win_bid(self,item):
        self.add_to_cart(item)

    def pay_shipping(self,item,discount):
        if self.check_credit(self.__cart.find_shipping(item).price):
            self.__credit -= (self.__cart.find_shipping(item).price - discount)
            self.__cart.pay_shipping(item)

    #display2user
    def see_bid_items(self):
        for item in self.__bid_items:
            if self == item.find_leader():
                print(f"Name: {item.name} Price: {item.price} [You are Leader]")
            else:
                print(f"Name: {item.name} Price: {item.price} [You are not Leader]")

    #funcs4debug
    def get_id(self):
        return self.__id
    def get_cred(self):
        return self.__credit

class Store:
    def __init__(self,name,path):
        self.__name = name
        self.__path = path

class Cart:
    def __init__(self):
        self.__order = []

    def add_order(self,item):
        self.__order.append(Shipping(item))

    def find_shipping(self,item):
        for shipping in self.__order:
            if shipping.item == item:
                return shipping

    def pay_shipping(self,item):
        return self.find_shipping(item).purchased()

    def display_order(self):
        for order in self.__order:
            print(str(order))

class Item:
    def __init__(self,id,name,start_price,category,store):
        self._status = "Available"
        self.__id = id
        self.__name = name
        self.__start_price = start_price
        self._price = start_price
        self.__bid_history = []
        self.__category = category
        self.__store = store
        self.__close_time = ""

    #update
    def update(self,time):
        '''ถ้าเวลาครบกำหนด'''
        self._status = "Ended"
        self.find_leader().win_bid(self)
        pass

    #getter
    @property
    def price(self):
        return self._price
    @property
    def id(self):
        return self.__id
    @property
    def bid_history(self):
        return self.__bid_history
    @property
    def status(self):
        return self._status
    @property
    def name(self):
        return self.__name
    
    #finder
    def find_leader(self):
        for bid in self.__bid_history:
            if bid.price == self._price:
                return bid.account
    def is_leader(self,acc):
        return self.find_leader() == acc

    def create_bid(self,acc,amount):
        self.__bid_history.append(Bid(acc,amount))


    def bidded(self,bidder,amount):
        if self.find_leader() is not None:
            self.find_leader().lock_cred(self._price,"unlock")
        self._price += amount
        bidder.lock_cred(self._price,)
        self.create_bid(bidder,self._price)

class BuyableItem(Item):
    def __init__(self,buy_price,id,name,start_price,category,store):
        self.__buy_price = buy_price
        super().__init__(id,name,start_price,category,store)

    #getter
    @property
    def buy_price(self):
        return self.__buy_price

    def bought(self,acc):
        self._status = "Bought"
        self.create_bid(acc,self.__buy_price)
        if self.find_leader() is not None:
            self.find_leader().lock_cred(self._price,"unlock")

class Transaction:
    def __init__(self,type,amount,bank,payment):
        self.__type = type
        self.__amount = amount
        self.__bank = bank
      

class Category:
    def __init__(self,id,name,description):
        self.__id = id
        self.__name = name
        self.__descriptoion = description

class Coupon:
    def __init__(self,code,discount):
        self.__code = code
        self.__discount = discount

    @property
    def discount(self):
        return self.__discount
    @property
    def code(self):
        return self.__code


    def check_code(self,code):
        return self.__code == code

class Shipping:
    def __init__(self,item):
        self.__item = item
        self.__status = "Not Purchase"
        self.__shipping_price = 100

    @property
    def item(self):
        return self.__item
    @property
    def price(self):
        return self.__shipping_price

    def purchased(self):
        self.__status = "Puechased"
    
    def __str__(self):
        return f"Item: {self.__item.name} Shipping fee: {self.__shipping_price} Status: {self.__status}"

class Bid:
    def __init__(self,account,price):
        self.__account = account
        self.__total_price = price

    #getters
    @property
    def account(self):
        return self.__account
    @property
    def price(self):
        return self.__total_price

    def __str__(self):
        return f"Account: {self.__account.id} Price: {self.__total_price}"

class Sniper:
    def __init__(self,item,acc,price):
        self.__item = item
        self.__acc = acc
        self.__price = price

    ##getter
    @property
    def price(self):
        return self.__price
    @property
    def account(self):
        return self.__acc
    @property
    def item(self):
        return self.__item

    def on_time(self):
        pass
        ##return item.end_time <= 10minutes
    

sys = System()
sys.sign_up("A","12345678","001")
sys.sign_up("B","12345678","002")
cat1 = Category("00001","type1","dunno")
cat1 = Category("00002","type2","dunno2")
store1 = Store("Store1","http/:xxxxx")
store1 = Store("Store2","http/:yyyyyy")

#Test add money
#tranfer
sys.add_money_by_tranfer(100000,"001","สลิป")
print(sys.find_account_by_id("001").get_cred())
#card
sys.add_money_by_card("002",100000,"66011471")
print(sys.find_account_by_id("002").get_cred())

sys.add_item("Iphone","1234",10000,cat1,store1)
sys.add_item("Samsung","1235",9000,cat1,store1,"buyable",20000)

#teat_bid
sys.bid("001","1234",500)
print("A:"+str(sys.find_account_by_id("001").get_cred()))
sys.bid("002","1234",1000)
print("A:"+str(sys.find_account_by_id("001").get_cred()))
print("B:"+str(sys.find_account_by_id("002").get_cred()))

sys.see_bid_history("1234")
# sys.find_account_by_id("001").see_bid_items()
# sys.find_account_by_id("002").see_bid_items()
sys.bid("001","1235",500)
# sys.find_account_by_id("001").see_bid_items()

sys.buy("001","1235")
sys.see_bid_history("1235")
print("A:"+str(sys.find_account_by_id("001").get_cred()))
sys.pay_shipping_price("001","1235")
print("A:"+str(sys.find_account_by_id("001").get_cred()))
sys.see_cart("001")
sys.sniper("002","1234",17000)