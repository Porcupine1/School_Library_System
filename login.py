from PyQt5.QtWidgets import QApplication, QTableView, QHeaderView, QLineEdit, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtSql import QSqlRelationalTableModel, QSqlRelation
from PyQt5 import uic
import hashlib
import hmac
import sys
import sqlite3
import os
import icons_rc
from ast import literal_eval


def initializeDatabase(exists: bool) -> None:
    """
    Creates tables  (USERS, BOOKS, TRANSACTIONS, CATEGORIES) if database was did not exist.\n
    Creates admin user.
    """
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
        cursor.execute(r'INSERT INTO USERS(USER_NAME, USER_PASSWORD) VALUES("admin", "{}")'.format(
            hashed_user_password))

        cursor.close()


def hashPassword(password: str) -> bool:
    """
    Hashes password and concatenates with a salt.    
    """
    salt = os.urandom(16)
    hashed_user_password = hashlib.pbkdf2_hmac(
        'sha256', password.encode(), salt, 100000)
    return hashed_user_password+salt


def password_check(entered_password: str, db_password: bytes) -> bool:
    """
    Hashes entered password using salt from hashed password pulled from database then compares both passwords.
    """
    salt = db_password[-16:]
    hashed_entered_password = hashlib.pbkdf2_hmac(
        'sha256', entered_password.encode(), salt, 100000)+salt
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
        login_query = (
            f"SELECT user_password FROM users WHERE user_name = '{username}'")

        cursor.execute(login_query)
        data = cursor.fetchone()

        try:
            if password_check(password, literal_eval(data[0])):
                self.main_window = MainApp()
                self.close()
                self.main_window.show()
            else:
                self.label.setText(
                    'Make sure you enterd Your username and password correctly.')
        except TypeError:
            self.label.setText(
                'Make sure you enterd Your username and password correctly.')

        cursor.close()


class MainApp(QMainWindow, main):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self.handleUi()
        self.showBooks()
        self.handleButtons()

    def handleUi(self):
        self.main_tab_widget.tabBar().setVisible(False)
        self.main_tab_widget.setObjectName('main_tab_widget')

    def handleButtons(self):
        self.dashboard_btn.clicked.connect(self.open_dashboard_tab)
        self.books_btn.clicked.connect(self.open_books_tab)
        self.issue_book_btn.clicked.connect(self.open_issue_book_tab)
        self.history_btn.clicked.connect(self.open_history_tab)
        self.settings_btn.clicked.connect(self.open_settings_tab)

        self.dashboard_btn.setObjectName('tab_btns')
        self.books_btn.setObjectName('tab_btns')
        self.issue_book_btn.setObjectName('tab_btns')
        self.history_btn.setObjectName('tab_btns')
        self.settings_btn.setObjectName('tab_btns')

    def open_dashboard_tab(self):
        self.main_tab_widget.setCurrentIndex(0)

    def open_books_tab(self):
        self.main_tab_widget.setCurrentIndex(1)

    def open_issue_book_tab(self):
        self.main_tab_widget.setCurrentIndex(2)

    def open_history_tab(self):
        self.main_tab_widget.setCurrentIndex(3)

    def open_settings_tab(self):
        self.main_tab_widget.setCurrentIndex(4)

    def showBooks(self):
        pass

    def addBook(book_title, quantity, category=None):
        cursor = sqliteConnection.cursor()
        add_book_query = f"""INSERT INTO BOOKS VALUES('{book_title}', '{category}', '{quantity}')"""
        cursor.execute(add_book_query)

    def deleteBook(book_title):
        cursor = sqliteConnection.cursor()
        delete_book_query = f'''DELETE FROM BOOKS WHERE BOOK_TITLE={book_title}'''
        cursor.execute(delete_book_query)

    def editBook(book_title, quantity, category=None):
        cursor = sqliteConnection.cursor()
        update_book_query = f'''UPDATE BOOKS SET BOOK_TITLE={book_title}, QUANTITY = {quantity}, BOOK_CATEGORY = {category} WHERE BOOK_TITLE={book_title}'''
        cursor.execute(update_book_query)

    def returnBook(book_title, num=1):
        cursor = sqliteConnection.cursor()
        update_book_query = f'''UPDATE BOOKS SET QUANTITY = QUANTITY+{num} WHERE BOOK_TITLE={book_title}'''
        cursor.execute(update_book_query)

    def lendBook(book_title, num=1):
        cursor = sqliteConnection.cursor()
        update_book_query = f'''UPDATE BOOKS SET QUANTITY = QUANTITY-{num} WHERE BOOK_TITLE={book_title}'''
        cursor.execute(update_book_query)


if __name__ == '__main__':
    exists = os.path.isfile('Library.db')  # Checks if database already exits
    # Creates database and makes connection
    sqliteConnection = sqlite3.connect('Library.db', isolation_level=None)
    app = QApplication(sys.argv)
    style = open('themes/dark.css', 'r')
    style = style.read()
    app.setStyleSheet(style)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())
