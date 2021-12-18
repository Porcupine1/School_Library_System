from sqlite3.dbapi2 import Cursor
from PyQt5.QtWidgets import QApplication, QLineEdit, QMainWindow, QPushButton, QWidget
from PyQt5 import uic
import hashlib, hmac, sys, sqlite3, os
from ast import literal_eval

def initializeDatabase(exists):
    
    if not exists:
        cursor = sqliteConnection.cursor()
        create_users_table_query = '''CREATE TABLE IF NOT EXISTS USERS (
                                    USER_ID INTEGER PRIMARY KEY AUTOINCREMENT
                                                            NOT NULL
                                                            UNIQUE,
                                    USER_NAME   VARCHAR (30)    NOT NULL
                                                                UNIQUE,
                                    USER_PASSWORD   VARCHAR  NOT NULL
                                );
                                '''
        create_books_table_query = '''CREATE TABLE IF NOT EXISTS BOOKS (
                                    BOOK_TITLE VARCHAR PRIMARY KEY
                                                    NOT NULL
                                                    UNIQUE,
                                    CATEGORY    VARCHAR REFERENCES CATEGORIES (CATEGORY_NAME),
                                    QUANTITY    INTEGER NOT NULL
                                );
                                '''
        create_transactions_table_query = '''CREATE TABLE IF NOT EXISTS TRANSACTIONS (
                                        TRANSACTION_ID INTEGER  PRIMARY KEY AUTOINCREMENT
                                                                NOT NULL
                                                                UNIQUE,
                                        TYPE    TEXT    NOT NULL,
                                        CLIENT                  NOT NULL,
                                        BOOK_ID TEXT    REFERENCES BOOKS (BOOK_TITLE) 
                                                                NOT NULL,
                                        USER_ID INTEGER REFERENCES Users (USER_ID) 
                                                                NOT NULL,
                                        DATETIME    DATETIME NOT NULL
                                    );
                                    '''
        create_categories_table_query = '''CREATE TABLE IF NOT EXISTS CATEGORIES (
                                    CATEGORY_NAME VARCHAR PRIMARY KEY
                                                            UNIQUE
                                                            NOT NULL
                                    );
                                    '''
        cursor.execute(create_users_table_query)
        cursor.execute(create_books_table_query)
        cursor.execute(create_transactions_table_query)
        cursor.execute(create_categories_table_query)
        hashed_user_password = str(hashPassword('admin'))
        cursor.execute(r'INSERT INTO USERS(USER_NAME, USER_PASSWORD) VALUES("admin", "{}")'.format(hashed_user_password))

        cursor.close()


def hashPassword(password):
    salt = os.urandom(16)
    hashed_user_password = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return hashed_user_password+salt

def password_check(entered_password, db_password):
    salt = db_password[-16:]
    hashed_entered_password = hashlib.pbkdf2_hmac('sha256', entered_password.encode(), salt, 100000)+salt
    return hmac.compare_digest(hashed_entered_password, db_password)
    

login, _ = uic.loadUiType('login.ui')
main, _ = uic.loadUiType('main.ui')


class LoginWindow(QWidget, login):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        initializeDatabase(exists)
        self.login_btn.clicked.connect(self.handleLogin)

    def handleLogin(self):
        username = self.username_le.text()
        password = self.password_le.text()
        cursor = sqliteConnection.cursor()
        login_query = (f"SELECT user_password FROM users WHERE user_name = '{username}'")        
         
        cursor.execute(login_query)
        data = cursor.fetchone()
        if str(data) == "[]":
                self.label.setText('Make Sure You Enterd Your User Name And Password Correctly.')
        elif password_check(password, literal_eval(data[0])):
            print('Logged in')
            self.main_window = MainApp()
            self.close()
            self.main_window.show()
        
        
        cursor.close()

class MainApp(QMainWindow, main):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)

if __name__ == '__main__':
    exists = os.path.isfile('Library.db')
    sqliteConnection = sqlite3.connect('Library.db',isolation_level=None)
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())
