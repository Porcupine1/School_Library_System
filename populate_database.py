import datetime
import random
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
import sys

from numpy import quantile
from login import hashPassword


database = QSqlDatabase.addDatabase("QSQLITE")
database.setDatabaseName("Library.db")

if not database.open():
    print("Unable to open data source file.")
    sys.exit(1)
query = QSqlQuery()
query.setForwardOnly(True)

############### CREATE USERS ##########
users = [(2,'willow', 'Salifyanji Mbashi', 'ted'),
            (3, 'will', 'Wilfred Phiri', 'password'),
            (4, 'jack', 'Jack Cholwe', '1234'),
            (5, 'frank', 'Tracy Diope', 'qwerty'),
            (6, 'joe', 'Joe Banda', 'beck'),
            (7, 'peach', 'Peach Sulingar', 'banana'),
            (8, 'wilder', 'Jack Wilder', '1234'),
            (9, 'frank12', 'Frank Ziwa', 'qwerty')]
for user in users:
    hashed_user_password = str(hashPassword(user[3]))
    query.prepare('INSERT INTO users VALUES(?, ?, ?, ?)')
    query.addBindValue(user[0])
    query.addBindValue(user[1])
    query.addBindValue(user[2])
    query.addBindValue(hashed_user_password)
    query.exec_()
    query.exec_(
        f"INSERT INTO user_permissions VALUES('{user[1]}',1,1,1,1,0,1,0,1,1,0,1,1,1,0,0,0)")
############## END ################

############### CREATE CLIENTS ##########
clients = [(1, 'Lorenzo St.Patrick', '8A1', 'H1WA'),
            (2, 'Tariq Mwansa', '10C1', 'H3WC'),
            (3, 'Dru Mwale', '12E4', 'H5WA'),
            (4, 'Zeke Chola', '9B3', 'H4WB'),
            (5, 'Emet Chongo', '8A1', 'H1WD'),
            (6, 'Efi Zulu', '11D2', 'H1WA'),
            (7, 'Lauren Mbashi', '8A1', 'H2WD'),
            (8, 'Daine Tejada', '8A4', 'H5WD')]

for client in clients:
    query.exec_(
                f"""INSERT INTO clients VALUES('{client[0]}', '{client[1]}', '{client[2]}', '{client[3]}')""")
############## END ################

############### CREATE CATEGORIES ##########
categories = ['Fiction', 'Fantasy', 'Adventure', 'Academic']

for category in categories:
    query.exec_(f"INSERT INTO categories VALUES('{category}')")
############## END ################

############### CREATE BOOKS ##########
books = [(1, 'Physics', 'Academic'),
          (2, 'Harry Potter', 'Fantasy'),
          (3, 'Percy Jackson', 'Adventure'),
          (4, 'Math', 'Academic')]

for book in books:
    query.exec_(
                f"INSERT INTO books VALUES('{book[0]}', '{book[1]}', '{book[2]}', {random.randint(1, 1000)})")
############## END ################

############### ISSUE BOOKS ##########
start = datetime.datetime(2022, 1, 19)
dates = [start+datetime.timedelta(i) for i in range(6)]
for date in dates:
    query.exec_(f"SELECT count(*) FROM transactions WHERE user_id={user[0]} AND DATE(datetime)='{datetime.datetime.today().date()}'")
    while query.next():
        today_transac_count = query.value(0)
    for j in range(1, 5):
        user = random.choice(users)
        client = random.choice(clients)
        book = random.choice(books)
        quantity = random.randint(1,10)
        
        ###### lend
        query.exec_(
                    f"""INSERT INTO client_records(client_id, book_id, quantity, returned) VALUES({client[0]}, {book[0]}, {quantity}, FALSE)""")
        if query.lastError().isValid():
                    query.exec_(
                        f"""UPDATE client_records SET quantity=quantity+{quantity}, returned=FALSE WHERE client_id={client[0]} AND book_id={book[0]}""")

        if today_transac_count > 0:
                query.exec_(
                    f"""INSERT INTO transactions(client_id, book_id, quantity, type, user_id, datetime) 
                    VALUES({client[0]}, {book[0]}, {quantity}, 'LEND', {user[0]}, '{date}')""")
                today_transac_count += 1
                    
        else:
                # If no transaction have been performed today, perform transaction and an obligatory zero quantity transaction of day
                query.exec_(
                    f"""INSERT INTO transactions(client_id, book_id, quantity, type, user_id) 
                    VALUES({client[0]}, {book[0]}, {quantity}, 'LEND', {user[0]}, '{date}')""")
                query.exec_(
                    f"""INSERT INTO transactions(type, user_id, datetime) 
                        VALUES('RETRIEVE', {user[0]}, '{date}')""") # Zero quantity transaction of day
                today_transac_count += 1 # Increase transaction count, exclusive of zero quantity transaction of day
                
        query.exec_(
                f"""UPDATE books SET quantity=quantity-{quantity} WHERE book_id={book[0]}""")