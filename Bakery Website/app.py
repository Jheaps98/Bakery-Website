from flask import Flask, render_template, request, redirect, jsonify, session
from os import path
import sqlite3, datetime
from datetime import datetime, time, date, timedelta

app = Flask(__name__)
app.secret_key = "cronton bakery"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

db_locale = "bookings.db"


@app.route('/Register', methods=['GET', 'POST'])
def Register():
    if request.method == "GET":
        return render_template('Register.html')
    else:
        userdetails = (
            request.form['Firstname'], 
            request.form['Surname'], 
            request.form['UserName'], 
            request.form["Password"], 
            request.form['Admin']
        )
        
        if not insertuser(userdetails):
            return render_template('Register.html', error="Username already exists. Please choose a different one.")
          
        return redirect("/")
  
def insertuser(userdetails):
    con = sqlite3.connect(db_locale)
    command = con.cursor()

    existing_user = command.execute("SELECT Username FROM User WHERE Username = ?", (userdetails[2],)).fetchone()
    if existing_user:
        con.close()
        return False  
    
    sqlstring = """INSERT INTO User (FirstName, Surname, Username, Password, Admin) VALUES (?, ?, ?, ?, ?)"""
    command.execute(sqlstring, userdetails)
    con.commit()
    con.close()
    return True 


@app.route('/Login', methods=['GET', 'POST'])
def index():
  con = sqlite3.connect(db_locale)
  command = con.cursor()
  command.execute("SELECT Username, Password, UserID, FirstName, Admin FROM User")


  if request.method == 'POST':

    data = command.fetchall()
    username_input = request.form.get('username')
    password_input = request.form.get('password')
    print(data)
    for x in data:
      user1 = str(x[0])
      pass1 = str(x[1])
      admin = str(x[4])
      userid = str(x[2])
      FirstName = str(x[3])

      if str(username_input) == user1 and str(password_input) == pass1:
        session['UserID'] = userid
        session["FirstName"] = FirstName
        session["admin"] = admin
        con.close()

        return redirect("/")
        
    
    invalidmessage = "Username or password incorrect"
    return render_template('index.html', invalid=invalidmessage)
  
  return render_template('index.html')
  
@app.route("/")
def Home():
  if "UserID" not in session:
    return redirect("/Login")
  else:
    print(session["admin"])
    if session["admin"] == "Y":
      print("")
      return redirect("/AdminMenu")
    else:
      print("")
      return render_template("menu.html", user=session["FirstName"])
    

@app.route("/AdminMenu")
def AdminMenu():
    if "UserID" not in session:
        return redirect("/Login")

    con = sqlite3.connect(db_locale)
    command = con.cursor()

    command.execute("""SELECT SUM(Order_Bill) FROM Orders WHERE Completed = "N" """)
    revenue_orders = command.fetchone()[0] or 0

    command.execute("""SELECT SUM(Order_Bill) FROM Orders WHERE Completed = "Y" """)
    revenue_completed = command.fetchone()[0] or 0

    command.execute("""SELECT COUNT(*) FROM Orders WHERE Completed = "N" """)
    total_orders = command.fetchone()[0]

    command.execute("""SELECT COUNT(*) FROM Orders WHERE Completed = "Y" """)
    total_completed = command.fetchone()[0]

    con.close()

    total_revenue = revenue_orders + revenue_completed

    return render_template("Adminmenu.html", user=session["FirstName"], total_revenue=total_revenue, active_orders=total_orders, completed_orders=total_completed)


@app.route("/LogOut")
def Logout():
  session.clear()
  return redirect("/")

@app.route("/Order", methods=["GET", "POST"])
def Order():
    if "UserID" not in session:
        return redirect("/Login")

    
    con = sqlite3.connect(db_locale)
    command = con.cursor()
    command.execute("SELECT Products.Product_Name, Products.Price, Products.Description,Products.Image, Products.ProductsID, Stock.Buyable FROM Products INNER JOIN Stock ON Products.StockID = Stock.StockID")
    products = [{"name": row[0], "price": f"£{(row[1]):.2f}", "description": row[2], "image": row[3], "ProductsID": row[4], "Buyable": row[5]} for row in command.fetchall()]
    con.close()

    
    if request.method == "POST":
        selected_item = request.form.get("food_item")
        for item in products:
            if item["name"] == selected_item:
                session["cart"] = session.get("cart", [])  
                session["cart"].append(item)

        

    return render_template("Orderpage.html", user=session["FirstName"], menu=products)



def addItems():
  food_menu = [
        {"name": "Protein Smoothie", "price": "£4.00", "description": "High Protein, smooth nutty smoothie with chocolate drizzle", "image": "/static/images/ProteinSmoothie.jpg"},
        {"name": "Chocolate Chip Muffin", "price": "£2.00", "description": "A soft, moist muffin loaded with chocolate chips.", "image": "/static/images/ChocMuffin.jpg"},
        {"name": "Wholegrain Wrap", "price": "£4.00", "description": "A healthy wholegrain wrap filled with grilled chicken and fresh greens.", "image": "/static/images/Wrap.jpg"},
        {"name": "Club Sandwich", "price": "£4.00", "description": "3 slices of bread, chicken, bacon, and greatness", "image": "/static/images/ClubSand.jpg"},
        {"name": "Salad Box", "price": "£3.40", "description": "Fresh greens mixed with tomato, garlic and many legumes", "image": "/static/images/SaladBox.jpg"},
        {"name": "Cheese Bites", "price": "£2.00", "description": "Fried Cheesy treat for a cheat day", "image": "/static/images/CheeseBites.jpg"},
    ]
   
  con = sqlite3.connect(db_locale)
  command = con.cursor()
  for item in food_menu:
      sqlstring =""" INSERT INTO Products (Product_Name, Price, Description, Image) VALUES (:name,:price,:description,:image)"""
      command.execute(sqlstring, item)

  con.commit()
  con.close()
   

@app.route("/Checkout")
def Checkout():
    if "UserID" not in session:
        return redirect("/Login")

    cart_items = session.get("cart", [])
    
    

    return render_template("Checkout.html", user=session["FirstName"], cart=cart_items,)


@app.route("/AddOrder")
def Add_Order():
    if "UserID" not in session:
        return redirect("/Login")
    else:
        cart_items = session.get("cart", [])
        total_price = sum(float(item['price'].replace('£', '')) for item in cart_items)
        return render_template("AddOrder.html", user=session["FirstName"], cart=cart_items, total_price=total_price)

@app.route("/Removeitem/<item_name>", methods=["POST"])
def Removeitem(item_name):
    cart_items = session.get("cart", [])

    
    for i in range(len(cart_items)):
        if cart_items[i]["name"] == item_name:
            del cart_items[i]  
            break  

    session["cart"] = cart_items
    return redirect("/Checkout")

    
@app.route("/ImportOrder", methods=["POST"])
def OrderImport():
  con = sqlite3.connect(db_locale)
  command = con.cursor()
  cart_items = session.get("cart", [])
  username = session.get("UserID")
  total_price = sum(float(item['price'].replace('£', '')) for item in cart_items)
  order_time = datetime.now()
  format_ordertime = order_time.strftime("%Y-%m-%d %H:%M:%S")
  print(order_time, format_ordertime)
  notes = request.form["AddNotes"]
  print(notes)
  
  sqlstring = """INSERT INTO Orders (Order_Bill, Username, Order_Date, Completed, Notes) VALUES (?,?,?,?, ?)"""
  insert = (total_price, username, str(format_ordertime), "N", notes)
  command.execute(sqlstring, insert)
  OrderID = command.lastrowid
  print(OrderID)

  con.commit()
  con.close()

  con = sqlite3.connect(db_locale)
  command = con.cursor()
     
  for item in cart_items:
     sqlstring = ("""INSERT INTO Contents (OrderID, ProductsID) VALUES (?,?) """)
     print(item)
     product = item["ProductsID"]
     insert = (OrderID, product)

     command.execute(sqlstring, insert)
  
  
  for item in cart_items:
    
    sqlstring = """SELECT Stock.StockID
                    FROM Stock
                    INNER JOIN Products ON Stock.Product_Name = Products.Product_Name
                    WHERE ProductsID = ?
                    """
    command.execute(sqlstring, (item["ProductsID"],))
    data1 = command.fetchone()
    sqlstring = """UPDATE Stock SET Amount_in_stock = Amount_in_stock - 1
                   WHERE StockID = ?"""
    
    command.execute(sqlstring, (data1))

  con.commit()
  con.close()
  
  return redirect("/Completion")
  

@app.route("/Completion")
def completionpage():
  if "UserID" not in session:
        return redirect("/Login")
  else:
    return render_template("Completion.html", user=session["FirstName"])
  
@app.route("/CompletedOrder")
def completedorder():
  if "UserID" not in session:
    return redirect("/Login")
  else:
    session.clear()
    return redirect("/")
  
@app.route("/View_Orders")
def display_orders():
    if "UserID" not in session:
        return redirect("/Login")
    else:
      con = sqlite3.connect(db_locale)
      command = con.cursor()
      sqlstring = """SELECT Orders.OrderID, Orders.Order_Bill, User.Username, Orders.Order_Date, Products.Product_Name, Orders.Notes
                     FROM Orders
                     INNER JOIN Contents ON Orders.OrderID = Contents.OrderID
                     INNER JOIN Products ON Contents.ProductsID = Products.ProductsID
                     INNER JOIN User ON Orders.Username = User.UserID
                     WHERE Completed == "N"
                     """ 
      command.execute(sqlstring)
      data = command.fetchall()

      
      order_dict = {} 
      for row in data:
        order_id = row[0]
        if order_id not in order_dict:
          order_dict[order_id] = []
        order_dict[order_id].append(row)

      grouped_orders = list(order_dict.values())
      
      for order in grouped_orders:
        print(order)

      data = grouped_orders

      
      return render_template("ViewOrders.html", user=session["FirstName"], data=data)
    
@app.route("/ViewStock")
def ViewStock():
  if "UserID" not in session:
        return redirect("/Login")
  else:
    con = sqlite3.connect(db_locale)
    command = con.cursor()
    sqlstring = """SELECT Stock.StockID, Stock.Amount_in_stock, Stock.Stock_Notif, Stock.Product_Name
                    FROM Stock
                    INNER JOIN Products ON Stock.Product_Name = Products.Product_Name
                    """
    command.execute(sqlstring)
    data1 = command.fetchall()

    stock_dict = {} 
    for row in data1:
      stock_id = row[0]
      if stock_id not in stock_dict:
        stock_dict[stock_id] = []
      stock_dict[stock_id].append(row)

    grouped_orders = list(stock_dict.values())
      
    for order in grouped_orders:
      print(order)

    data1 = grouped_orders

    con.close()
    
    return render_template("Stock.html", user=session["FirstName"], data1 = data1)

@app.route("/EditStock/<int:ProductID>", methods=["GET", "POST"])
def EditStock(ProductID):
  if "UserID" not in session:
        return redirect("/Login")
  else:
    if request.method == "GET":
      con = sqlite3.connect(db_locale)
      command=con.cursor()

      sqlstring = """SELECT Product_Name FROM Products WHERE ProductsID = ? """ 
      command.execute(sqlstring, (ProductID,))
      name = (command.fetchone()[0])
      print(name)

      con.close()
      updatestock()

      return render_template("EditStock.html", user=session["FirstName"], product=name)
    
def updatestock():
    con = sqlite3.connect(db_locale)
    command=con.cursor()
    sqlstring = """SELECT * FROM Stock"""

    command.execute(sqlstring)
    data = command.fetchall()
    for item in data:
        if item[1] < 10:
          sqlstring = """ UPDATE Stock SET Stock_Notif = ? WHERE StockID = ?"""

          value = ("Y", item[0], )
          command.execute(sqlstring, value)
        elif item[1] >= 10:
            sqlstring = """ UPDATE Stock SET Stock_Notif = ? WHERE StockID = ?"""

            value = ("N", item[0], )
            command.execute(sqlstring, value)
        else:
          continue

    for item in data:
      if item[1] >= 1:
        sqlstring = """ UPDATE Stock SET Buyable = ? WHERE StockID = ?"""
        value = ("Y", item[0],)
        command.execute(sqlstring, value)
      elif item[1] < 1:
        sqlstring = """ UPDATE Stock Set Buyable = ? WHERE StockID = ?"""
        value = ("N", item[0],)
        command.execute(sqlstring, value)
      else:
        continue
    
    con.commit()
    con.close()


@app.route("/EditStock/<string:name>", methods=["POST" ])
def EditStock2(name):
  if "UserID" not in session:
        return redirect("/Login")
  else:
      con = sqlite3.connect(db_locale)
      command=con.cursor()

      sqlstring = """UPDATE Stock SET Amount_in_stock = ? WHERE Stock.Product_Name = ?"""
      details = (int(request.form["Amount_in_stock"]), name,)
      command.execute(sqlstring, details)

      con.commit()
      con.close()
      return redirect("/ViewStock")
  
@app.route("/MarkCompleted/<int:OrderID>")
def MarkCompleted(OrderID):
    con = sqlite3.connect(db_locale)
    command = con.cursor()
    

    
    insertsqlstring = """
        UPDATE Orders SET Completed = ?
        WHERE OrderID = ?
    """
    command.execute(insertsqlstring, ("Y",OrderID,))


    con.commit()
    con.close()

    return redirect("/View_Orders")


@app.route("/View_CompletedOrders")
def display_completedorders():
    if "UserID" not in session:
        return redirect("/Login")
    else:
      con = sqlite3.connect(db_locale)
      command = con.cursor()
      sqlstring = """SELECT Orders.OrderID, Orders.Order_Bill, User.Username, Orders.Order_Date, Products.Product_Name
                     FROM Orders
                     INNER JOIN Contents ON Orders.OrderID = Contents.OrderID
                     INNER JOIN Products ON Contents.ProductsID = Products.ProductsID
                     INNER JOIN User ON Orders.Username = User.UserID
                     WHERE Completed == "Y"
                     """ 
      
      command.execute(sqlstring)
      data = command.fetchall()

      
      completedorder_dict = {} 
      for row in data:
        completedorder_id = row[0]
        if completedorder_id not in completedorder_dict:
          completedorder_dict[completedorder_id] = []
        completedorder_dict[completedorder_id].append(row) 

      completedgrouped_orders = list(completedorder_dict.values())
      
      for completedorder in completedgrouped_orders:
        print(completedorder)

      data = completedgrouped_orders

      
      return render_template("CompletedOrders.html", user=session["FirstName"], data=data)
  
  
@app.route("/OrderHistory")
def OrderHistory():
  if "UserID" not in session:
    return redirect("/Login")
  else:
    con = sqlite3.connect(db_locale)
    command = con.cursor()
    sqlstring = """SELECT Orders.OrderID, Orders.Order_Bill, User.Username, Orders.Order_Date, Products.Product_Name
                     FROM Orders
                     INNER JOIN Contents ON Orders.OrderID = Contents.OrderID
                     INNER JOIN Products ON Contents.ProductsID = Products.ProductsID
                     INNER JOIN User ON Orders.Username = User.UserID
                     WHERE Completed = "Y" AND User.UserID = ?"""
    command.execute(sqlstring, (session["UserID"],))
    data = command.fetchall()

    order_dict = {} 
    for row in data:
      order_id = row[0]
      if order_id not in order_dict:
        order_dict[order_id] = []
      order_dict[order_id].append(row) 

    grouped_orders = list(order_dict.values())
      
    for order in grouped_orders:
      print(order)

    data = grouped_orders

      
    return render_template("OrderHistory.html", user=session["FirstName"], data=data)

@app.route("/ViewReviews")
def ViewReviews():
    if "UserID" not in session:
        return redirect("/Login")
    else:
        con = sqlite3.connect(db_locale)
        command = con.cursor()
        sqlstring = """SELECT Reviews.ReviewID, Reviews.Stars, Reviews.Comment, User.Username
               FROM Reviews
               INNER JOIN User ON Reviews.UserID = User.UserID"""

        command.execute(sqlstring)
        reviews = command.fetchall()
        reviews2 = []
        con.close()
        stars = []
        for review in reviews:
            print(review)
            review = list(review)
            if review[1] == 1:
                RatingStar = "⭐"
            elif review[1] == 2:
                RatingStar = "⭐⭐"
            elif review[1] == 3:
                RatingStar = "⭐⭐⭐"
            elif review[1] == 4:
                RatingStar = "⭐⭐⭐⭐"
            elif review[1] == 5:
                RatingStar = "⭐⭐⭐⭐⭐"
            review = tuple(review)
            stars.append(RatingStar)
            reviews2.append((review[0], RatingStar, review[2], review[3]))
            print(review)

    

           

        if session["admin"] == "Y":
          return render_template("AdminViewReviews.html", reviews=reviews2, user=session["FirstName"])
        else:
          return render_template("ViewReviews.html", reviews=reviews2, user=session["FirstName"])

@app.route("/AddReviews", methods=["GET", "POST"])
def AddReviews():
    if "UserID" not in session:
        return redirect("/Login")
    else:
        if request.method == "POST":
            stars = request.form["Stars"]
            comment = request.form["Comment"]
            userID = session["UserID"]

            con = sqlite3.connect(db_locale)
            command = con.cursor()
            insert_sql = "INSERT INTO Reviews (Stars, Comment, UserID) VALUES (?, ?, ?)"
            command.execute(insert_sql, (stars, comment, userID))
            con.commit()
            con.close()

            return redirect("/ViewReviews")

        return render_template("AddReviews.html", user=session["FirstName"])
  
@app.route("/FAQ")
def FAQ():
  if "UserID" not in session:
    return redirect("/Login")
  else:
    return render_template("FAQ.html", user=session["FirstName"])



@app.route("/OpenHoursInfo")
def OpenHours():
   return render_template("OpenHoursInfo.html")

if __name__ == "__main__":
  app.run(host='0.0.0.0', port='8080', debug=True)
  
#///LAST GOALS FOR PROGRAM ///
# - ***** MORE FOOD OPTIONS 
# - ***** POTENTIAL ALLERGY NOTIFICATIONS[]




 


  