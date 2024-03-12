from fastapi import FastAPI , HTTPException ,Request , Form , Cookie ,Response 
from fastapi.responses import HTMLResponse , RedirectResponse,JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime , date , timedelta
from typing import Optional

import uvicorn
app = FastAPI()
app.mount('/static',StaticFiles(directory='static'),name='static')
templates = Jinja2Templates(directory="templates")

class User:
    def __init__(self,name,cititzen_id,password):
        self.__name=name
        self.__cititzen_id=cititzen_id
        self.__password=password
    def get_name(self):
        return self.__name
    def get_citizen_id(self):
        return self.__cititzen_id
    def get_password(self):
        return self.__password

class Account:
    def __init__(self,account_no,credit,user):
        self.__account_no=account_no
        self.__credit=credit
        self.__user=user
        self.__transaction_list=[]
        self.__tranfer_transaction = []
        self.__WAtransaction = []
        self.__address_list=[]

    def user_info(self):
        format_dict = {
            "name":self.user.get_name(),
            "citizen_id":self.user.get_citizen_id(),
            "address":self.address_list,
            "id":self.account_no,
            "credit":self.credit
        }
        return format_dict
    
    def add_adress(self,address):
        self.__address_list.append(address)

    @property
    def address_list(self):
        return self.__address_list
    @property
    def transaction_list(self):
        return self.__transaction_list
    @property   
    def credit(self):
        return self.__credit
    @property   
    def account_no(self):
        return self.__account_no
    @property   
    def user(self):
        return self.__user
    
    def change_credit(self,credit):
        self.__credit=credit



    def transfer(self, amount, target_account):
        if  self.check_credit(amount):
            self.change_credit(self.credit - amount)
            target_account.change_credit(target_account.credit + amount)
            self.__transaction_list.append(Payment(amount,target_account))
            return "Done"
        else:
            return "Insufficient funds"
        
    def add_user(self,user):
        self.__user=user

    def check_credit(self,amount):
        return self.__credit >= amount
    
    def add_credit(self,amount,payment):
        self.__credit += amount
        self.create_transaction("Add",amount,payment)

    def withdraw_credit(self,amount):
        if self.check_credit(amount):
            self.__credit -= amount
            self.create_transaction("Withdraw",amount,"Tranfer slip")
            return {"Done":"Done"}
        return {"error":"money_not_have_enough"} 
    
    def create_transaction(self,type,amount,payment):
        self.__transaction_list.append(Transaction(type,amount,"SCB",payment))

    def lock_cred(self,amount,mode = "lock"):
        if mode == "unlock":
            self.__credit += amount
        elif mode == "lock":
            self.__credit -= amount
    
class Seller_Account(Account):
    def __init__(self,account_no,credit,user,item_list):
        super().__init__(account_no,credit,user)
        self.__selling_item = item_list

    def add_item(self,item_ins):
        self.__selling_item.append(item_ins)

    @property
    def item(self):
        return self.__selling_item
    
class Buyer_Account(Account):
    def __init__(self,account_no,credit,user):
        super().__init__(account_no,credit,user)
        self.__cart = Cart()
        self.__bid_items = []

    def get_buyer_bid_item(self):
        format = {}
        for item in self.__bid_items:
            most_bidder = item.find_leader().user.get_name() if item.bid_transactions and item.find_leader() else "No bids yet"
            format[item.name] = {
                "name":item.name,
                "status": item.status,
                "start_price": item.start_price,
                "buy_price": item.buy_price,
                "price": item.price,
                "bid_transactions": item.transaction,  
                "seller_name": item.seller_account.user.get_name(),
                "seller_id":item.seller_account.account_no,
                "id": item.id,
                "path": item.path,
                "date": item.date,
                "time": item.time,
                "most_bidder":most_bidder,
                "seller_credit" : item.seller_account.credit
            }
        return format



    def bid_item(self):
        return self.__bid_items
    
    # Auction
    def bid(self, item, amount):
        R_cred = item.price + amount
        if self.check_credit(R_cred):
            if item not in self.__bid_items:
                self.__bid_items.append(item)
            item.bidded(self, amount)

    # win_bid
    def win_bid(self,item):
        self.add_to_cart(item)
    def add_to_cart(self,item):
        self.__cart.add_order(item)
    def see_cart(self):
        return self.__cart.display_order()

    def clear_item(self, item_clear):
        if item_clear in self.__bid_items:
            self.__bid_items.remove(item_clear)


    def buy(self,item):
        if self == item.find_leader():
            R_cred = item.buy_price - item.price
        else:
            R_cred = item.buy_price
        if self.check_credit(R_cred):
            self.transfer(item.buy_price,item.seller_account)
            item.bought(self)
            self.add_to_cart(item)

    def pay_shipping(self,item,discount):
        if self.check_credit(self.__cart.find_shipping(item).price):
            self.withdraw_credit(self.__cart.find_shipping(item).price - discount)
            self.__cart.pay_shipping(item)

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
        order_info = {}
        for shipping in self.__order:
            order_info[shipping.item.name] = {
                "item_name": shipping.item.name,
                "status": shipping.item.status,
                "status_shipping":shipping.status,
                "start_price": shipping.item.start_price,
                "buy_price": shipping.item.buy_price,
                "price": shipping.item.price,
                "seller_name": shipping.item.seller_account.user.get_name(),
                "id": shipping.item.id,
                "date": shipping.item.date,
                "time": shipping.item.time,
                "path": shipping.item.path,
                "category": shipping.item.category
            }
        return order_info

class Shipping:
    def __init__(self,item):
        self.__item = item
        self.__status = "Not Purchase"
        self.__shipping_price = 60

    @property
    def item(self):
        return self.__item
    @property
    def price(self):
        return self.__shipping_price
    @property
    def status(self):
        return self.__status

    def purchased(self):
        self.__status = "Purchased"
    
    def __str__(self):
        return f"Item: {self.__item.name} Shipping fee: {self.__shipping_price} Status: {self.__status}"

class Item:
    def __init__(self,name, status, start_price, buy_price, price, seller_account,id,date,time,path,category):
        self.__name = name
        self.__status = status
        self.__start_price = start_price
        self.buy_price = buy_price
        self.__price = price
        self.__seller_account = seller_account
        self.__id=id
        self.__bid_transactions = []
        self.__date = date
        self.__time = time
        self.__path = path
        self.__category = category
        # for clear bid item in account after someone win (need item in account to display status in user page)
        self.__bidder_list = []

    @property
    def name(self):
        return self.__name
    @property
    def seller_account(self):
        return self.__seller_account
    @property
    def time(self):
        return self.__time
    @property
    def date(self):
        return self.__date
    @property
    def path(self):
        return self.__path
    @property
    def bid_transactions(self):
        return self.__bid_transactions
    @property
    def status(self):
        return self.__status
    @property
    def id(self):
        return self.__id
    @property
    def start_price(self):
        return self.__start_price
    @property
    def price(self):
        return self.__price
    @property
    def transaction(self):
        return self.__bid_transactions
    @property
    def category(self):
        return self.__category
    
    def time_up(self):
        leader = self.find_leader()
        if leader and self.__status == "Active":
            leader.lock_cred(self.__price, "unlock")
            leader.transfer(self.__price, self.__seller_account)
            leader.win_bid(self)
            self.__status = "Complete"
            self.clear_bidder()
        elif self.__status == "Active":
            self.__status = "Complete (No one Bid)"

    
    #กูว่าทำในนี้ดีกว่าว่ะ saveด้วยหำน้อย ไปแดกข้าวละ
    '''
    def cancle_auction(self):
        self.__status = "Cancle"
        if self.find_leader()
            self.find_leader().lock_credit(self.__price,"unlock")
        return "Done"
    '''
    def bought(self,acc):
        self.__status = "Bought"
        self.add_bid_transaction(0,self.buy_price,acc)
        if self.find_leader() is not None:
            self.find_leader().lock_cred(self.price,"unlock")
            self.clear_bidder()
            # Clear bid item from all buyer

    def add_bid_transaction(self,bid_amount,total_price,account):
        self.__bid_transactions.append(Bid(bid_amount,total_price,account, datetime.now().strftime("%d-%m-%Y %H:%M:%S")))
        
    def bidded(self,bidder,amount):
        if self.find_leader() is not None:
            self.find_leader().lock_cred(self.__price,"unlock")
        self.__price += amount
        bidder.lock_cred(self.__price)
        self.__bidder_list.append(bidder)
        self.add_bid_transaction(amount,self.__price,bidder)

    def clear_bidder(self):
        for bidder in self.__bidder_list:
            bidder.clear_item(self)
        self.__bidder_list = []

    def change_status(self,status):
        if self.__status == "Active":
            self.clear_bidder()
            self.__status=status        
    
    def change_price(self,price):
        self.__price = price

    def find_leader(self):
        for bid in self.__bid_transactions:
            if bid.total_price == self.__price:
                return bid.account

    
    def see_bid_history(self,item_id):
        item = self.find_item_by_id(item_id)
        bid_list = item.bid_history
        for bid in bid_list:
            print(str(bid))
    
    def __str__(self):
        return f"Bid amount: {self.__bid_amount}, Total price: {self.__total_price}, Account no: {self.__account.account_no}, Time: {self.__time}"

class Bid:
    def __init__(self,bid_amount,total_price,account,time):
        self.__bid_amount=bid_amount
        self.__total_price=total_price
        self.__account=account
        self.__time = time
    
    @property
    def bid_amount(self):
        return self.__bid_amount
    @property
    def total_price(self):
        return self.__total_price
    @property
    def account(self):
        return self.__account
    @property
    def time(self):
        return self.__time

class System:
    def __init__(self):
        self.__item_list = []
        self.__user_list = []
        self.__account_list = []
        self.__report_list=[]
        self.__category_list = []
        self.__coupon_list = []


    def see_cart(self,acc_id):
        return self.find_account_by_id(acc_id).see_cart()
    def add_category(self,category):
        self.__category_list.append(category)
    @property
    def category_list(self):
        return self.__category_list
    @property
    def account_login(self):
        return self.__account_login
    @property

    def update(self,dt):
        for item in self.__item_list:
            item.update(dt)
    def add_item(self,item):
        self.__item_list.append(item)

    def add_user(self,user):
        self.__user_list.append(user)

    def add_account(self,account):
        self.__account_list.append(account)
    
    def get_item_instance_by_item_id(self,item_id):
        item_instance=None
        for item in system.get_item():
            if item_id == item.id:
                item_instance=item
                return item_instance
        return None
    

    def login(self,id,password):
        for account in self.__account_list:
            if id == account.user.get_citizen_id() and account.user.get_password() == password:
                return {"login_status":True,"account_no":account.account_no}
        return {"login_status":False,"account_no":Account(0,0,None).account_no}

    def put_on_auction(self, seller_id, item):
        seller_ins = self.get_account(seller_id)
        if isinstance(seller_ins,Seller_Account):
            item_format_cls = Item(name=item["name"],
                                status=item["status"],
                                start_price=item["start_price"],
                                buy_price=item["buy_price"],
                                price=item["start_price"],
                                seller_account=seller_ins,
                                id=len(self.__item_list)+1,
                                date=item["end_date"],
                                time=item["end_time"],
                                path=item["path"],
                                category=Catagory(item["category"]))
            self.add_item(item_format_cls)
            seller_ins.add_item(item_format_cls)
            return {"message": "Item added to auction successfully"}
        else:
            return {"message": "Error: Seller account not found or is not valid"}
    
    '''
    def cancle_auction(self,acc_id,item_id):
        if isinstance(Seller_Account,self.find_account_by_id(acc_id)):
            return self.find_item_by_id(item_id).cancle_auction()
        return "Error nigga ควย"
    '''
    
    def create_user(self, confirm_seller, name_input, id, password_input):
        user_instance = User(name=name_input, cititzen_id=id, password=password_input)
        if confirm_seller:
            account = Seller_Account(account_no=len(self.__account_list) + 1, credit=0, user=user_instance, item_list=[])
        else:
            account = Buyer_Account(account_no=len(self.__account_list) + 1, credit=0, user=user_instance)
        self.add_user(user_instance)
        self.add_account(account)

    def get_bid_transaction_detail(self,item_id):
        sum_bid_transaction=[]
        for bid_transaction in system.get_item_instance_by_item_id(item_id).bid_transactions:
            sum_bid_transaction.append( {"total_price":f"{bid_transaction.total_price}",
                    "account":f"{bid_transaction.account.user.get_name()}",
                    "time":f"{bid_transaction.time}"})
        return sum_bid_transaction
   
    def get_account_list(self):
        return self.__account_list

    def get_item(self):
        return self.__item_list
    
    # Format
    def format_item_details(self, item):
        most_bidder = item.find_leader().user.get_name() if item.bid_transactions and item.find_leader() else "No bids yet"
        return {
            "name":item.name,
            "status": item.status,
            "start_price": item.start_price,
            "buy_price": item.buy_price,
            "price": item.price,
            "bid_transactions": item.transaction,  
            "seller_name": item.seller_account.user.get_name(),
            "seller_id":item.seller_account.account_no,
            "id": item.id,
            "path": item.path,
            "date": item.date,
            "time": item.time,
            "most_bidder":most_bidder,
            "seller_credit" : item.seller_account.credit,
            "category":item.category.name
        }
    # Get ITEM BY USING FORMAT
    def get_seller_item(self,seller_id):
        formatted_dict = {}
        for item in self.__item_list:
            if seller_id == item.seller_account.account_no:
                formatted_dict[item.name] = self.format_item_details(item)
        return formatted_dict
    
    def get_item_format(self):
        formatted_dict = {}
        for item in self.get_item():
            formatted_dict[item.name] = self.format_item_details(item)
        return formatted_dict
    
    def get_item_format_one(self,product_id):
        formatted_dict = {}
        for item in system.get_item():
            if product_id == item.id:
                formatted_dict[item.name] = self.format_item_details(item)
                return formatted_dict
    
    def get_item_by_catalog(self,catalog_name_input):
        formatted_dict = {}
        for item in self.__item_list:
            if item.category.name == catalog_name_input:
                formatted_dict[item.name] = self.format_item_details(item)
        return formatted_dict
    
    def get_account_format(self,seller_id):
        return self.get_account(seller_id).user_info()

    def get_account(self,seller_id):
        for account in self.__account_list:
            if account.account_no == seller_id:
                return account
    
    def find_item_by_id(self,item_id):
        for item in self.__item_list:
            if item.id==item_id:
                return item
    
    def find_account_by_id(self,account_id):
        for account in self.__account_list:
            if account.account_no == account_id:
                return account      

    def buy(self,acc_id,item_id):
        self.find_account_by_id(acc_id).buy(self.find_item_by_id(item_id))

    def bid(self,item_id,acc_id,amount):
        self.find_account_by_id(acc_id).bid(self.find_item_by_id(item_id),amount)
    
    def report(self,account_id,accusation):
        acc = self.find_account_by_id(account_id)
        Report.add_account_report(acc)
        self.__report_list.append(Report("time",accusation))
        return 'Success'

    def withdraw(self,account_id,amount):
        account=self.find_account_by_id(account_id)
        if account.check_credit(amount):
            account.transfer(account,amount)
        else:
            return "Error"
    #money_related
    def add_money(self,acc_id,amount,method):
        if method == "card":
            self.find_account_by_id(acc_id).add_credit(amount,"Credit_Card")
        else:
            self.find_account_by_id(acc_id).add_credit(amount,"Transfer_Money")
    
    # def add_money_by_tranfer(self,acc_id,amount,slip_info):
    #     self.find_account_by_id(acc_id).add_credit(amount,slip_info)
    # def add_money_by_card(self,acc_id,amount,payment_info):
    #     self.find_account_by_id(acc_id).add_credit(amount,"by card lol")

    def withdraw_credit(self,acc_id,amount):
        self.find_account_by_id(acc_id).withdraw_credit(amount)
    
    def find_coupon_by_code(self,coupon_code):
        for coupon in self.__coupon_list:
            if coupon.code == coupon_code:    
                return coupon
            
    def add_coupon(self,coupon_code,discount):
        self.__coupon_list.append(Coupon(coupon_code,discount))

    def pay_shipping_price(self,acc_id,item_id,coupon_code = None):
        if coupon_code is None:
            discount = 0
        elif self.find_coupon_by_code(coupon_code) is not None:
            discount = self.find_coupon_by_code(coupon_code).discount
        else :
            return "Wrong Code"
        self.find_account_by_id(acc_id).pay_shipping(self.find_item_by_id(item_id),discount)
    
    def is_seller(self,acc_id):
        for seller in self.__account_list:
            if acc_id == seller.account_no and isinstance(seller,Seller_Account):
                return True
        return False
    
class Payment:
    def __init__(self,amount,target_account):
        self.__amount=amount
        self.__target_account=target_account
    
    def payment(self):
        pass
        
class Catagory:
    def __init__(self,name):
        self.__name = name

    @property
    def name(self):
        return self.__name

class Report:
    def __init__(self,date,accusation):
        self.__date = date
        self.__accusation  = accusation
        self.__target_account = []
    
    def add_account_report(self,target_account):
        self.__target_account.append(target_account)

class Banned:
    def __init__(self,account,start_date,end_date,cause):
        self.__account=account
        self.__start_date=start_date
        self.__end_date=end_date
        self.__cause=cause

class Transaction:
  def __init__(self,amount,type,time,payment):
    self._amount = amount
    self._type = type
    self._time = time
    self.__payment = payment

    def __str__(self):
        return f"Type: {self.__type} amount: {self.__amount} bank: {self.__bank}"

class TranferTransaction(Transaction):#ใช้ตอนโอน credit
  def __init__(self,target_acc,amount,type,time):
    self.__target_acc = target_acc
    super().__init__(amount,type,time)

  def __str__(self):
    return f"Target Account: {self.__target_acc.account_no}, Amount: {self._amount}, Time: {self._time}"

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

##WA มาจาก withdraw/add credit ตอนถอนตัง เติมตัง  
#   How to use lah please speak thai Ok   ยัง   !!!unlock credit ก่อนค่อยโอน
#   ไอต้า ใน bid มีโอนเครดิคยังตอนเวลาหมด k อาบน้ำก่อนเดี๋ยวมาทำต่อ K
class WATransaction(Transaction):
  def __init__(self,payment,amount,type,time):
    self.__payment = payment
    super().__init__(amount,type,time)


# instance
user_instance = User(name="pakorn",cititzen_id=1110301395893,password="pakorn123")
user_instance2 = User(name="tanawat",cititzen_id=11104014344,password="tanawat123")
user_instance3 = User(name="phet",cititzen_id=111040144325,password="phet123")


account1 = Buyer_Account(account_no=1,credit=0,user=user_instance)
account2 = Seller_Account(account_no=2,credit=0,user=user_instance2,item_list=[])
account3 = Buyer_Account(account_no=3,credit=0,user=user_instance3)

# Time for product as a auction
# YYYY-MM-DD
# "%H:%M"
today = datetime.now().date()
three_days_from_now = today + timedelta(days=3)
desired_time = datetime.strptime("20:45", "%H:%M").strftime("%H:%M")

computer = Catagory("computer")
movie = Catagory("movie")
sport = Catagory("sport")
music = Catagory("music")
eletronic = Catagory("electronic")
toy = Catagory("toy")
plant = Catagory("plant")
cartoon = Catagory("cartoon")
song = Catagory("song")
fashion = Catagory("fashion")
home = Catagory("home")
beauty = Catagory("beauty")
stationery = Catagory("stationery")
watch = Catagory("watch")
car = Catagory("car")
shoes = Catagory("shoes")



item_instance = Item(name="clock so cool",status="Active", start_price=100, buy_price=200, price=100, seller_account=account2,id=1,date=three_days_from_now,time=desired_time,path="https://ih1.redbubble.net/image.3198956303.5903/clkf,bamboo,black,600x600-bg,f8f8f8.jpg",category=home)
item_instance2 = Item(name="clock not cool",status="Active", start_price=100, buy_price=200, price=100, seller_account=account2,id=2,date=three_days_from_now,time=desired_time,path="https://live.staticflickr.com/7148/6768671645_d48c5ef573_z.jpg",category=home)
item_instance3 = Item(name="Nissan GTR R35",status="Active", start_price=11900000, buy_price=31900000, price=11900000, seller_account=account2,id=3,date=three_days_from_now,time=desired_time,path="https://mainstand.co.th/storage/news/3576_NissanGTRBlackEdition.jpg",category=car)
item_instance4 = Item(name="IPAD_PRO",status="Active", start_price=11900000, buy_price=31900000, price=11900000, seller_account=account2,id=4,date=three_days_from_now,time=desired_time,path="https://cdn.siamphone.com/spec/apple/images/ipad_pro_11_(2021)/apple_ipad_pro_11_(2021)_2.jpg",category=eletronic)
item_instance5 = Item(name="IPHONE15",status="Active", start_price=11900000, buy_price=31900000, price=11900000, seller_account=account2,id=5,date=three_days_from_now,time=desired_time,path="https://media-cdn.bnn.in.th/332476/iPhone_15_Pro_Max_Blue_Titanium_1-square_medium.jpg",category=eletronic)
item_instance6 = Item(name="IPHONE12",status="Active", start_price=11900000, buy_price=31900000, price=11900000, seller_account=account2,id=6,date=three_days_from_now,time=desired_time,path="https://media-cdn.bnn.in.th/11746/Apple-iPhone-12-White-1-square_medium.jpg",category=eletronic)
item_instance7 = Item(name="RTX5090 IT",status="Active", start_price=590000, buy_price=21900000, price=590000, seller_account=account2,id=7,date=three_days_from_now,time=desired_time,path="https://i.ytimg.com/vi/PgBFTYdm0MM/maxresdefault.jpg",category=computer)
item_instance8 = Item(name="Mouse Gaming Ratatui Edition",status="Active", start_price=219, buy_price=21900, price=219, seller_account=account2,id=8,date=three_days_from_now,time=desired_time,path="https://i.chzbgr.com/thumb1200/9395205/h39C4B8AA/funny-mouse-memes",category=computer)
item_instance9 = Item(name="Car 4",status="Active", start_price=199, buy_price=18900, price=199, seller_account=account2,id=9,date=three_days_from_now,time=desired_time,path="https://i.ytimg.com/vi/xhvES48E0uY/maxresdefault.jpg",category=movie)
item_instance10 = Item(name="Mr bean",status="Active", start_price=279, buy_price=18900, price=279, seller_account=account2,id=10,date=three_days_from_now,time=desired_time,path="https://images.moviesanywhere.com/46da14790c6e02bd93fd94ec5d3e8f72/96df62d0-571b-4474-a11a-bdf96945384a.jpg",category=movie)
item_instance11 = Item(name="Basketball with Michael Jordan Signature",status="Active", start_price=1200000, buy_price=35000000, price=1200000, seller_account=account2,id=11,date=three_days_from_now,time=desired_time,path="https://www.sportsonline.com.au/cdn/shop/products/IMG_1001-1_1024x1024.jpg?v=1669016674",category=sport)


# add to system
system = System()
system.add_item(item_instance)
system.add_item(item_instance2)
system.add_item(item_instance3)
system.add_item(item_instance4)
system.add_item(item_instance5)
system.add_item(item_instance6)
system.add_item(item_instance7)
system.add_item(item_instance8)
system.add_item(item_instance9)
system.add_item(item_instance10)
system.add_item(item_instance11)
system.add_coupon("DJANGOWELCOME",60)
system.add_coupon("HELLOWORLD",60)
system.add_coupon("HAPPYNEWYEAR",60)
system.add_category(computer)
system.add_category(movie)
system.add_category(sport)
system.add_category(music)
system.add_category(eletronic)
system.add_category(toy)
system.add_category(plant)
system.add_category(cartoon)
system.add_category(song)
system.add_category(fashion)
system.add_category(home)
system.add_category(beauty)
system.add_category(stationery)
system.add_category(watch)
system.add_category(car)
system.add_category(shoes)


# account2.add_item(item_instance)
# account2.add_item(item_instance2)
# account2.add_item(item_instance3)
# account2.add_item(item_instance4)
# account2.add_item(item_instance5)
# account2.add_item(item_instance6)
# account2.add_item(item_instance7)
# account2.add_item(item_instance8)
# account2.add_item(item_instance9)
# account2.add_item(item_instance10)
# account2.add_item(item_instance11)

system.add_user(user_instance)
system.add_user(user_instance2)
system.add_user(user_instance3)
system.add_account(account1)
system.add_account(account2)
system.add_account(account3)

# HTML RESPONSE ##########################################################################################################################################################

# View Product by 
@app.get("/product_catalog={catalog}",tags=['root'])
async def search_item_buy_catalog(request: Request,catalog:str)->dict:
    return templates.TemplateResponse("view_all_product.html",{"request": request,"product":system.get_item_by_catalog(catalog),"category_list":system.category_list})

# View Product All
@app.get("/all_product",tags=['root'])
async def search_item_buy_id(request: Request)->dict:
    return templates.TemplateResponse("view_all_product.html",{"request": request,"product":system.get_item_format(),"category_list":system.category_list})

# View Product Detail
@app.get("/view_product/{product_id}",tags=['root'])
async def search_item_by_id(request: Request,product_id:int)-> dict:
    return templates.TemplateResponse("view_product.html",{"request": request,"product":system.get_item_format_one(product_id)})

# Cancle product Auction API ##########################################################################################################################################################

# Change Status of Product Status : Active Auction , Cancle Auction , Success
@app.get('/cancle_auction/{product_id}/{status}/{seller_id}',tags=['root']) 
async def cancle_auction(product_id:int,status:str,seller_id:int)->dict:
    item_ins = system.find_item_by_id(product_id)
    item_ins.change_status(status)
    return RedirectResponse(url=f"/seller_account_management/", status_code=303)

@app.get('/time_up/{product_id}',tags=['root']) 
async def cancle_auction(product_id:int):
    item_ins = system.find_item_by_id(product_id)
    item_ins.time_up()

# BID API ###############################################################################################################################################################

@app.post("/bid/{item_id}", tags=['root'])
async def add_transaction(item_id: int, account_id: int =Form(...), money: int=Form(...)) -> dict:
    system.bid(item_id, account_id, money)
    return RedirectResponse(url=f"/view_product/{item_id}", status_code=303)


# Seller Backend Manage products ##########################################################################################################################################################

@app.get("/seller_account_management/",tags=['root'])
async def seller_page(request:Request)-> dict:
    seller_id = int(request.cookies.get("user_id"))
    item_format = system.get_seller_item(seller_id)
    return templates.TemplateResponse("seller_account_page.html",{"request": request,"products":item_format})


# Login Logout Register api ,template ##########################################################################################################################################################

@app.get('/login',tags=['root'])
async def register(request:Request)->dict:
    return templates.TemplateResponse("login_page.html",{"request": request})

@app.post('/get_login_info', tags=['root'])
async def login(request: Request, response: Response, id: int = Form(...), password: str = Form(...)) -> dict:
    user = system.login(id, password)
    is_seller = system.is_seller(user["account_no"])
    try:
        response.set_cookie(key="user_id", value=user["account_no"])
        response.set_cookie(key="login_status", value=True)
        response.set_cookie(key="is_seller", value=is_seller)
        return {"redirect_url": "/all_product"}
    except:
        return {"Error":"รหัสผิดครับน้อง"}

@app.get('/logout',tags=['root'])
async def logout(request:Request,response:Response):
    response.set_cookie(key="user_id", value=int(0))
    response.set_cookie(key="login_status", value=bool(False))
    response.set_cookie(key="is_seller", value=False)
    return {"ADAasds":"asdsa"}

#Get_user_info_for_display_in_navbar
@app.get("/get_user_info_which_login", tags=['root'])
async def get_user_info_which_login(request: Request)->dict:
    return {"login_status":request.cookies.get("login_status"),"user_login_id":request.cookies.get("user_id"),"is_seller":request.cookies.get("is_seller")}   

# Register Page
@app.get('/register',tags=['root'])
async def register(request:Request)->dict:
    return templates.TemplateResponse("register.html",{"request": request})

# Register API
@app.post("/register")
async def get_user_data(name: str = Form(...), password: str = Form(...), id: int = Form(...), address: Optional[str] = Form(None),confirm_seller:bool = Form(False)):
    system.create_user(confirm_seller,name,id,password)
    return RedirectResponse(url="/all_product", status_code=303)

########################################################################################################################################################################

# Add item to system
@app.post('/create_auction',tags=['root'])
async def create_auction(request: Request, 
                         product_name: str = Form(...),
                         start_price: float = Form(...),
                         buy_price: float = Form(...),
                         image_link: str = Form(...),
                         end_date: str = Form(...),
                         end_time: str = Form(...),
                         seller_id: int = Form(...),
                         category:str = Form(...))->dict:
    item = {"name":product_name,"status":"Active","start_price":start_price,"buy_price":buy_price,"end_date":end_date,"end_time":end_time,"path":image_link,"category":category}
    system.put_on_auction(seller_id,item)
    return RedirectResponse(url=f"/seller_account_management/", status_code=303)


#Buy API (HOLD ON)
@app.post("/buy_product/{product_id}",tags=['root'])
async def search_item_by_id_and_check_account_money(product_id:int,acc_id:int=Form(...))-> dict:
    system.buy(acc_id,product_id)
    return RedirectResponse(url=f"/all_product", status_code=303)


# page add money
@app.get("/payment/",tags=["root"])
async def search_item_by_id_and_check_account_money(request:Request)-> dict:
    return templates.TemplateResponse("payment.html",{"request": request})


# add money api
@app.post("/add_money_to_account/",tags=["root"])
async def search_item_by_id_and_check_account_money(account_id:int=Form(...),amount:int=Form(...),method:str=Form(...))-> dict:
    system.add_money(account_id,amount,method)
    return RedirectResponse(url=f"/member/", status_code=303)


#Bid transaction
@app.get("/see_bid_transaction/{item_id}",tags=['root'])
async def see_bid_transaction(request:Request,item_id:int):
    return templates.TemplateResponse("bid_transaction.html",{"request": request,"product":system.get_bid_transaction_detail(item_id)})

@app.post("/pay_shipping/{item_id}")
async def see_bid_transaction(item_id: int,acc_id: int = Form(...),discount: Optional[str] = Form(None)):
    system.pay_shipping_price(acc_id, item_id, discount)
    return RedirectResponse(url=f"/member/", status_code=303)

#Buyer Profile maybe cant use buyer_id in path need to change
@app.get("/member/",tags=['root'])
async def see_profile(request:Request):
    account_ins = system.get_account(int(request.cookies.get("user_id")))
    item_bid_list = account_ins.get_buyer_bid_item()
    user_info = system.get_account_format(int(request.cookies.get("user_id")))
    return templates.TemplateResponse("member.html",{"request": request,"user_info":user_info,"bid_list":item_bid_list,"cart_info":system.see_cart(int(request.cookies.get("user_id")))})

# need to redirect + maybe change to WATRANSAC
@app.post("/withdraw",tags=["root"])
async def withdraw(request:Request,account_id:int=Form(...),amount:int=Form(...)):
    return system.find_account_by_id(account_id).withdraw_credit(amount)

# need to redirect + maybe change to WATRANSAC
@app.post("/add_address",tags=["root"])
async def add_address(request:Request,account_id:int=Form(...),address:str=Form(...)):
    system.get_account(account_id).add_adress(address)
    return RedirectResponse(url=f"/member/", status_code=303)
                                                                 
@app.get("/redirect/{path}",tags=["root"])
async def redirect(request:Request,path:str):
    return templates.TemplateResponse("just_redirect.html",{"request": request,"path":path})

if __name__ == '__oop10__':
    uvicorn.run("oop10:app",host="127.0.0.1", port=8000,log_level='info')


@app.get("/main")
def main():
    return "this is a main"




