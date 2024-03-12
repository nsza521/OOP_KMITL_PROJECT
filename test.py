class User:
  def __init__(self,user_name,password):
    self.__user_name = user_name
    self.__password=password
  def get_name(self):
      return self.__user_name
  def get_password(self):
      return self.__password

###########
class Account:
  def __init__(self,account_no,credit,user):
    self.__account_no=account_no
    self._credit=credit
    self.__user=user 
    self.__tranfer_transactions=[]
    self.__address_list=[]

  @property
  def tranfer_transactions(self):
     return self.__tranfer_transactions
  @property   
  def credit(self):
    return self._credit
  @property   
  def account_no(self):
    return self.__account_no

  def get_credit(self):
    return self._credit

  def add_tranfer_transaction(self,amount,target_account,type):
    self.__tranfer_transactions.append(TranferTransaction(target_account,amount,"Buy","anytime soon"))

  def check_credit(self,amount):
    return amount <= self._credit
  def change_credit(self,amount):
    self._credit += amount
  def __rshift__(self,other):
    self.change_credit(-other[0])
    self.add_tranfer_transaction(-other[0],other[1],"buy")
    other[1].change_credit(+other[0])
    other[1].add_tranfer_transaction(+other[0],self,"buy")
    

#########
class Seller_Account(Account):
  def __init__(self,account_no,credit,user):
    super().__init__(account_no,credit,user)
    self.selling_item = []
  def add_item(self,item_ins):
     self.selling_item.append(item_ins)

##############
class Buyer_Account(Account):
  def __init__(self,account_no,credit,user):
    super().__init__(account_no,credit,user)
    self.__usable_credit=credit

  def lock_credit(self,amount,mode):
    if mode == "lock":
      self.__usable_credit -= amount
    elif mode == "unlock":
      self.__usable_credit += amount
  def check_credit(self,amount):
    return self.__usable_credit >= amount
  def get_credit(self):
    return self.__usable_credit

  def buy(self,item):
    if self.check_credit(item.buy_price):
      self >> [item.buy_price,item.seller_account]
      item.bought(self)
      self.__usable_credit = self._credit

#############
class Item:
  def __init__(self,name, status, start_price, buy_price, seller_account,id):
    self.name = name
    self.__status = status
    self.__start_price = start_price
    self.__buy_price = buy_price
    self.__price = start_price
    self.__bid_history = []
    self.__seller_account = seller_account
    self.__most_bidder = None
    self.__id=id

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
  def buy_price(self):
    return self.__buy_price

  @property
  def price(self):
    return self.__price

  @property
  def bid_history(self):
    return self.__bid_history
  @property
  def seller_account(self):
    return self.__seller_account

  def change_status(self,status):
    self.__status=status        

  def change_price(self,price):
    self.__price = price

  def bought(self,acc):
    self.change_status("bought")
    if self.__most_bidder is not None:
      self.__most_bidder.lock_credit(self.__price,"unlock")
      self._most_bidder = acc
      self.add_bid_transaction(0,self.__buy_price,acc,"time","buy")

  def add_bid_transaction(self,bid_amount,total_price,account,time,type = "bid"):
    self.__bid_history.append(Bid(bid_amount,total_price,account,time,type))

  def bid(self,account,bid_price):
    if self.status == "Active" and bid_price - self.__price > 0 and account.check_credit(bid_price):
      self.add_bid_transaction(bid_price-self.__price,bid_price,account,"time")
      if self.__most_bidder is not None:
        self.__most_bidder.lock_credit(self.__price,"unlock")
      self.__most_bidder = account
      account.lock_credit(bid_price,"lock")
      self.__price = bid_price
  
  def cancle_auction(self,acc_no):
    if acc_no != self.seller_account.account_no:
      return "You are not the seller"
    self.__status = "Cancled"
    if self.__most_bidder is not None:
      self.__most_bidder.lock_credit(self.__price,"unlock")
    return "Done"

#########################
class Bid:
  def __init__(self,bid_amount,total_price,account,time,type = "bid"):
    self.__type = type
    self.__bid_amount=bid_amount
    self.__total_price=total_price
    self.__account=account
    self.__time = time

  #display
  def __str__(self):
    if self.__type == "bid":
      return f"Bid amount: {self.__bid_amount}, Total price: {self.__total_price}, Account no: {self.__account.account_no}, Time: {self.__time}"
    elif self.__type == "buy":
      return f"BOUGHT!!!, Price: {self.__total_price}, Account no: {self.__account.account_no}, Time:{self.__time}"

#####################
class System:
  def __init__(self):
    self.__item_list = []
    self.__category = []
    self.__buyer_account_list = []
    self.__seller_account_list = []

  def add_item(self,item):
    self.__item_list.append(item)
  def add_buyer_account(self,account):
    self.__buyer_account_list.append(account)
  def add_seller_account(self,account):
    self.__seller_account_list.append(account)

  ##find funcs
    ##ถ้าโดนสั่งแก้
#   def find_seller_by_id(self,acc_id):
#     for item in self.__item_list:
#       if item.seller_account.account_no == acc_id:
#         return item.seller_account 
  def find_buyer_account_by_id(self,id):
    for account in self.__buyer_account_list:
      if account.account_no == id:
        return account
  def find_seller_account_by_id(self,id):
    for account in self.__seller_account_list:
      if account.account_no == id:
        return account
  def find_item_by_id(self,id):
    for item in self.__item_list:
      if item.id == id:
        return item
  def get_item_by_category(self,cat_name):
    for category in self.__category:
      if category.name == cat_name:
        return category
        
  def login(self,user_name,pass_word):
    for account in (self.__buyer_account_list+self.__seller_account_list):
      if account.user.user_name == user_name and account.user.pass_word == pass_word:
        return account.account_no
    return "Incorrect Username or Password"

  def put_on_auction(self,name, status, start_price, buy_price, seller_account_id,id):
    seller = self.find_seller_account_by_id(seller_account_id)
    item = Item(name, status, start_price, buy_price, seller,id)
    self.add_item(item)
    seller.add_item(item)
      
  def see_bid_history(self,item_id):
    item = self.find_item_by_id(item_id)
    bid_list = item.bid_history
    for bid in bid_list:
      print(str(bid))
  def bid(self,item_id,account_id,bid_amount): 
    acc = self.find_buyer_account_by_id(account_id)
    item = self.find_item_by_id(item_id)
    item.bid(acc,bid_amount)

  def cancel_auction(self,item_id,acc_no):
    item = self.find_item_by_id(item_id)
    return item.cancle_auction(acc_no)

  def buy(self,item_id,account_id):
    item = self.find_item_by_id(item_id)
    acc = self.find_buyer_account_by_id(account_id)
    acc.buy(item)

  def add_credit(self,acc_id,amount):
    pass
    acc = self.find_buyer_account_by_id(acc_id)
    acc.add_credit(amount)
  def see_tranfer_transaction(self,acc_id):
    acc = self.find_buyer_account_by_id(acc_id)
    transac_list = acc.tranfer_transactions
    for transac in transac_list:
      print(str(transac))

#########
class Catagory:
  def __init__(self,name):
    self.__name = name

#########
class Report:
  def __init__(self,target_acc,accusation,date):
    self.__target_account = target_acc
    self.__date = date
    self.__accusation  = accusation

##########
class Banned:
  def __init__(self,account,start_date,end_date,cause):
    self.__account=account
    self.__start_date=start_date
    self.__end_date=end_date
    self.__cause=cause

##########
class Transaction:
  def __init__(self,amount,type,time):
    self._amount = amount
    self._type = type
    self._time = time

class TranferTransaction(Transaction):
  def __init__(self,target_acc,amount,type,time):
    self.__target_acc = target_acc
    super().__init__(amount,type,time)

  def __str__(self):
    return f"Target Account: {self.__target_acc.account_no}, Amount: {self._amount}, Time: {self._time}"
  
class WATransaction(Transaction):
  def __init__(self,payment,amount,type,time):
    self.__payment = payment
    super().__init__(amount,type,time)


app = System()
buyer_list = [{"Tar2990":"12345678"}]
seller_list = [{"Seller":"gggggg"}]

buyer1 = Buyer_Account("100",100000,User("Tar2990","12345678"))
app.add_buyer_account(buyer1)
buyer2 = Buyer_Account("101",100000,User("Pakorn","12345678"))
app.add_buyer_account(buyer2)
seller1 = Seller_Account("001",1000,User("Seller","gggggg"))
app.add_seller_account(seller1)
seller2 = Seller_Account("002",1000,User("Paaaa","0123"))
app.add_seller_account(seller2)

app.put_on_auction("iPhone", "Active", 1000, 12000, "001" ,"000001")

app.bid("000001", "100", 1002)
print(buyer1.get_credit())
app.bid("000001", "101", 1500)
print("buyer2:"+str(buyer2.get_credit()))
print("buyer1:"+str(buyer1.get_credit()))
print(app.cancel_auction("000001","002"))
print("buyer2:"+str(buyer2.get_credit()))
app.buy("000001","101")
app.see_bid_history("000001")
app.see_tranfer_transaction("101")
from datetime import datetime
print(datetime.strptime("20:00", "%H:%M").strftime("%H:%M"))