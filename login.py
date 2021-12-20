from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QComboBox, QLabel, QMessageBox, QSpinBox, QTableView, QHeaderView, QLineEdit, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlRelationalTableModel, QSqlRelation, QSqlTableModel
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
                                    BOOK_ID    INTEGER PRIMARY KEY AUTOINCREMENT
                                                    NOT NULL
                                                    UNIQUE,
                                    BOOK_TITLE VARCHAR NOT NULL,
                                    CATEGORY   VARCHAR,
                                    QUANTITY   INTEGER NOT NULL,
                                    CONSTRAINT category FOREIGN KEY(CATEGORY) REFERENCES CATEGORIES (CATEGORY_NAME)
                                );
                                '''
        create_transactions_table_query = '''CREATE TABLE IF NOT EXISTS TRANSACTIONS (
                                        TRANSACTION_ID INTEGER  PRIMARY KEY AUTOINCREMENT
                                                                NOT NULL
                                                                UNIQUE,
                                        TYPE    TEXT    NOT NULL,
                                        CLIENT                  NOT NULL,
                                        BOOK_ID TEXT    NOT NULL,
                                        USER_ID INTEGER NOT NULL,
                                        DATETIME    DATETIME NOT NULL,
                                        CONSTRAINT book FOREIGN KEY(BOOK_ID) REFERENCES BOOKS (BOOK_ID),
                                        CONSTRAINT user FOREIGN KEY(USER_ID) REFERENCES Users (USER_ID)
                                    );
                                    '''
        create_categories_table_query = '''CREATE TABLE IF NOT EXISTS CATEGORIES (
                                    CATEGORY_NAME VARCHAR PRIMARY KEY
                                                            UNIQUE
                                                            NOT NULL
                                    );
                                    '''
        query.exec_(create_users_table_query)
        query.exec_(create_books_table_query)
        query.exec_(create_transactions_table_query)
        query.exec_(create_categories_table_query)
        hashed_user_password = str(hashPassword('admin'))
        query.prepare(
            r'''INSERT INTO USERS(USER_NAME, USER_PASSWORD) VALUES(?, ?)''')
        query.addBindValue('admin')
        query.addBindValue(hashed_user_password)
        query.exec_()


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

        query.exec_(
            f"SELECT USER_PASSWORD FROM USERS WHERE USER_NAME = '{username}'")
        data = []
        while (query.next()):
            data.append((query.value(0)))

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


class MainApp(QMainWindow, main):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self.handleUiChanges()
        self.handleButtons()

    def handleUiChanges(self):

        self.main_tab_widget.tabBar().setVisible(False)
        self.main_tab_widget.setObjectName('main_tab_widget')
        self.updateCategoryCombox()
        self.updateAllBooksTableView()

    def updateCategoryCombox(self):
        model = QSqlTableModel()
        model.setTable('CATEGORIES')
        column = model.fieldIndex('CATEGORY_NAME')
        model.setEditStrategy(QSqlTableModel.OnFieldChange)
        model.setSort(column, Qt.AscendingOrder)
        model.select()
        self.category_combo_box.setModel(model)
        self.category_combo_box_2.setModel(model)

    def updateAllBooksTableView(self):
        model = QSqlRelationalTableModel()
        model.setTable('BOOKS')
        model.setRelation(model.fieldIndex('CATEGORY'), QSqlRelation(
            'CATEGORIES', 'CATEGORY_NAME', 'CATEGORY_NAME'))
        self.all_books_table_view.setModel(model)
        self.all_books_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.
                                                                          Stretch)
        model.select()

    def handleButtons(self):
        self.dashboard_btn.clicked.connect(self.open_dashboard_tab)
        self.books_btn.clicked.connect(self.open_books_tab)
        self.issue_book_btn.clicked.connect(self.open_issue_book_tab)
        self.history_btn.clicked.connect(self.open_history_tab)
        self.settings_btn.clicked.connect(self.open_settings_tab)
        self.add_book_btn.clicked.connect(self.addBook)
        self.add_category_btn.clicked.connect(
            lambda: self.addCategory(self.add_category_le.text(), self.category_info_label))
        self.search_category_btn.clicked.connect(
            lambda: self.searchCategory(self.add_category_le.text()))

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

    def addBook(self):
        """
        Formasts book details and adds it to the database if it does not exist.        
        """

        book_title = self.book_title_le.text().capitalize()
        category = self.category_combo_box.currentText().capitalize()
        quantity = self.quantity_spin_box.value()
        
        if book_title == "":
            QMessageBox.critical(self, 'Invalid Enrty', 'Book title is required!', QMessageBox.Ok, QMessageBox.Ok)
        else:
            query.exec_(
                f"""SELECT * FROM BOOKS WHERE BOOK_TITLE = '{book_title}' AND CATEGORY = '{category}'""")

            if (query.next()):
                QMessageBox.information(
                    self, 'Book exists', f'"{book_title}" already exists in "{category}" category', QMessageBox.Ok, QMessageBox.Ok)
            else:
                query.exec_(f"SELECT * FROM CATEGORIES WHERE CATEGORY_NAME = '{category}'")
                if not (query.next()):                
                    response = QMessageBox.question(
                        self, 'Add Category?', 
                        f'''"{category}" does not exist in library. Do you want add it to the library?\n\nNB: If not, "{book_title}" will not be added to library.''',
                        QMessageBox.Yes|QMessageBox.No, QMessageBox.Yes)
                    
                    if response == QMessageBox.Yes:
                        self.addCategory(category, None)
                        query.exec_(
                        f"INSERT INTO BOOKS(BOOK_TITLE, CATEGORY, QUANTITY) VALUES('{book_title}', '{category}', '{quantity}')")
                        self.book_title_le.clear()
                        self.category_combo_box.clear()
                        self.quantity_spin_box.clear()
                else:
                    query.exec_(
                        f"INSERT INTO BOOKS(BOOK_TITLE, CATEGORY, QUANTITY) VALUES('{book_title}', '{category}', '{quantity}')")
                    self.book_title_le.clear()
                    self.category_combo_box.clear()
                    self.quantity_spin_box.setValue(0)
                    
                self.updateAllBooksTableView()

    def deleteBook(book_title):

        delete_book_query = f'''DELETE FROM BOOKS WHERE BOOK_TITLE={book_title}'''
        query.exec_(delete_book_query)

    def editBook(book_title, quantity, category=None):

        update_book_query = f'''UPDATE BOOKS SET BOOK_TITLE={book_title}, QUANTITY = {quantity}, BOOK_CATEGORY = {category} WHERE BOOK_TITLE={book_title}'''
        query.exec_(update_book_query)

    def returnBook(book_title, num=1):

        update_book_query = f'''UPDATE BOOKS SET QUANTITY = QUANTITY+{num} WHERE BOOK_TITLE={book_title}'''
        query.exec_(update_book_query)

    def lendBook(book_title, num=1):

        update_book_query = f'''UPDATE BOOKS SET QUANTITY = QUANTITY-{num} WHERE BOOK_TITLE={book_title}'''
        query.exec_(update_book_query)

    def addCategory(self, category_name: str, label: QLabel) -> None:
        """
        Capitalizes entered category name and adds it to database if it does not exist.

        """
        if category_name:
            category_name = category_name.capitalize()
            query.exec_(
                f"SELECT * FROM CATEGORIES WHERE CATEGORY_NAME = '{category_name}'")

            if (query.next() and label is not None):
                label.setText(
                    f'"{category_name}" category already exists in library.')
            else:
                query.exec_(
                    f"INSERT INTO CATEGORIES VALUES('{category_name}')")
                self.updateCategoryCombox()
                if label is not None:
                    label.setText(
                        f'"{category_name}" category sucssessfuly added to library.')
                    self.add_category_le.clear()

        else:
            if label is not None:
                label.setText("NO INPUT GIVEN!")

    def searchCategory(self, category_name: str) -> None:
        """
        Capitalizes entered category name and checks if it already exists.

        """
        if category_name:
            category_name = category_name.capitalize()
            query.exec_(
                f"SELECT * FROM CATEGORIES WHERE CATEGORY_NAME = '{category_name}'")

            data = []
            while (query.next()):
                data.append(query.value(0))

            if data == []:
                self.category_info_label.setText(
                    f'"{category_name}" category does not exist in library.')

            else:
                self.category_info_label.setText(
                    f'"{category_name}" category exists in library.')
                self.add_category_le.clear()

        else:
            self.category_info_label.setText("NO INPUT GIVEN!")


if __name__ == '__main__':
    exists = os.path.isfile('Library.db')
    database = QSqlDatabase.addDatabase("QSQLITE")
    database.setDatabaseName("Library.db")

    if not database.open():
        print("Unable to open data source file.")
        sys.exit(1)
    query = QSqlQuery()
    query.setForwardOnly(True)
    app = QApplication(sys.argv)
    style = open('themes/dark.css', 'r')
    style = style.read()
    app.setStyleSheet(style)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())
