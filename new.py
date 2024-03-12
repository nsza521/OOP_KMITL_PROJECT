class System:
    def __init__(self):
        self.__account_list = []
        self.__item_list = []
        self.__sniper = []
        ##self.__catagories = []

    ##setup funcs
    def add_item(self,name,id,start_price,category,store,type = None,buy_price = None):
        if type == "buyable":
            self.__item_list.append(BuyableItem(buy_price,id,name,start_price,category,store))
        elif type is None:
            self.__item_list.append(Item(id,name,start_price,category,store))
        else:
            raise "Whaaaaaa"

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
    #money_related
    def add_money_by_tranfer(self,amount,acc_id,slip_info):
        self.find_account_by_id(acc_id).add_credit(amount,slip_info)
    def add_money_by_card(self,acc_id,amount,payment_info):
        self.find_account_by_id(acc_id).add_credit(amount,"by card lol")
    def withdraw_credit(self,acc_id,amount):
        self.find_account_by_id(acc_id).withdraw_credit(amount)

    #auctions
    def bid(self,acc_id,item_id,amount):
        self.find_account_by_id(acc_id).bid(self.find_item_by_id(item_id),amount)
    def see_bid_history(self,item_id):
        for bid in self.find_item_by_id(item_id).bid_history:
            print(str(bid))
    def buy(self,acc_id,item_id):
        self.find_account_by_id("acc_id").buy(self.find_item_by_id(item_id))

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

    #validation
    def check_credit(self,amount):
        return self.__credit >= amount

    #auctions
    def bid(self,item,amount):
        if self.check_credit(item.price + amount):
            if item not in self.__bid_items:
                self.__bid_items.append(item)
            item.bidded(self,amount)
    def buy(self,item):
        if self.check_credit(item.buy_price):
            item.bought(self)
            self.add_to_cart(item)

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

class Item:
    def __init__(self,id,name,start_price,category,store):
        self._status = "Available"
        self.__id = id
        self.__name = name
        self.__start_price = start_price
        self.__price = start_price
        self.__bid_history = []
        self.__category = category
        self.__store = store

    #getter
    @property
    def price(self):
        return self.__price
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
            if bid.price == self.__price:
                return bid.account

    def create_bid(self,acc):
        self.__bid_history.append(Bid(acc,self.__price))


    def bidded(self,bidder,amount):
        if self.find_leader() is not None:
            self.find_leader().lock_cred(self.__price,"unlock")
        self.__price += amount
        bidder.lock_cred(self.__price)
        self.create_bid(bidder)

class BuyableItem(Item):
    def __init__(self,buy_price,id,name,start_price,category,store):
        self.__buy_price = buy_price
        super().__init__(id,name,start_price,category,store)

    #getter
    @property
    def buy_price(self):
        return self.__buy_price

    def bought(self):
        self._status = "Bought"
        pass

class Transaction:
    def __init__(self,type,amount,bank,payment):
        self.__type = type
        self.__amount = amount
        self.__bank = bank
        self.__payment = payment

class Category:
    def __init__(self,id,name,description):
        self.__id = id
        self.__name = name
        self.__descriptoion = description

class Coupon:
    def __init__(self,code):
        self.__code = code

    def check_code(self,code):
        return self.__code == code

class Shipping:
    def __init__(self,item):
        self.__item = item
        self.__status = "Not Purchase"
        self.__shipping_price = 100

    def purchase(self,credit):
        if credit >= self.__shipping_price:
            pass
        return "Not Enought Credit"

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
    def __init__(self,item,acc,amount):
        self.__item = item
        self.__acc = acc
        self.__amount = amount

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
sys.find_account_by_id("001").see_bid_items()
sys.find_account_by_id("002").see_bid_items()
sys.bid("001","1235",500)
sys.find_account_by_id("001").see_bid_items()