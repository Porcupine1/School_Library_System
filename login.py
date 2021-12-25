from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QMessageBox, QHeaderView, QMainWindow, QWidget
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlRelationalTableModel, QSqlRelation, QSqlTableModel
from PyQt5 import uic
import hashlib
import hmac
import sys
import os
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
                                    CATEGORY   VARCHAR NOT NULL,
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

        query.exec_("INSERT INTO CATEGORIES VALUES('Unknown')")

        hashed_user_password = str(hashPassword('admin'))
        query.prepare('INSERT INTO USERS(USER_NAME, USER_PASSWORD) VALUES(?, ?)')
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
                    'Make sure you entered Your username and password correctly.')
        except TypeError:
            self.label.setText(
                'Make sure you entered Your username and password correctly.')


class MainApp(QMainWindow, main):

    def __init__(self):
        QWidget.__init__(self)
        self.edit = []
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
        model.setSort(column, Qt.AscendingOrder)
        model.select()
        self.category_combo_box.setModel(model)
        self.category_combo_box_2.setModel(model)

        index = self.category_combo_box.findText("Unknown")
        self.category_combo_box.setCurrentIndex(index)
        self.category_combo_box_2.setCurrentIndex(index)

    def updateAllBooksTableView(self):
        model = QSqlRelationalTableModel()
        model.setTable('BOOKS')
        model.setRelation(model.fieldIndex('CATEGORY'), QSqlRelation(
            'CATEGORIES', 'CATEGORY_NAME', 'CATEGORY_NAME'))
        self.all_books_table_view.setModel(model)
        self.all_books_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.
                                                                          Stretch)
        model.setQuery(QSqlQuery(
            '''SELECT BOOK_TITLE, CATEGORY, QUANTITY FROM BOOKS ORDER BY BOOK_TITLE, CATEGORY'''))

    def updateCategoryList(self, data):
        self.category_lw.clear()
        query.exec_(
            f"SELECT CATEGORY FROM BOOKS WHERE BOOK_TITLE = '{data[0][1]}'")
        data_2 = []
        while (query.next()):
            data_2.append(query.value(0))
        self.category_lw.addItems([cate for cate in data_2])
        if data_2 == []:
            self.edit_extra_label.setText(f'"{data[0][1]}" did not appear in any category.')

    def handleButtons(self):
        self.dashboard_btn.clicked.connect(self.open_dashboard_tab)
        self.books_btn.clicked.connect(self.open_books_tab)
        self.issue_book_btn.clicked.connect(self.open_issue_book_tab)
        self.history_btn.clicked.connect(self.open_history_tab)
        self.settings_btn.clicked.connect(self.open_settings_tab)
        self.add_book_btn.clicked.connect(lambda: self.addBook(self.book_title_le.text().capitalize(
        ), self.category_combo_box.currentText().capitalize(), self.quantity_spin_box.value()))
        self.delete_book_btn.clicked.connect(
            lambda: self.deleteBook(self.book_title_le_2.text().capitalize(), self.category_combo_box_2.currentText().capitalize()))
        self.search_book_btn.clicked.connect(
            lambda: self.searchBook(self.book_title_le_2.text().capitalize(), self.category_combo_box_2.currentText().capitalize()))
        self.edit_book_btn.clicked.connect(lambda: self.editBook(self.book_title_le_2.text().capitalize(
        ), self.category_combo_box_2.currentText().capitalize(), self.quantity_spin_box_2.value()))
        self.add_category_btn.clicked.connect(
            lambda: self.addCategory(self.add_category_le.text().capitalize(), self.category_info_label))
        self.search_category_btn.clicked.connect(
            lambda: self.searchCategory(self.add_category_le.text().capitalize()))

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

    def showBookSearchResults(self, data):
        self.edit = data
        self.edit_info_label.setText(f"'{data[0][1]}' found!")
        self.book_title_le_2.setText(data[0][1])
        self.category_combo_box_2.setCurrentIndex(
            self.category_combo_box_2.findText(data[0][2]))
        self.quantity_spin_box_2.setValue(data[0][3])

        self.edit_extra_label.setText(
            f'"{data[0][1]}" appeared in the following categories:')
        self.updateCategoryList(data)

    def searchBook(self, book_title: str, category=None):

        if book_title == "":
            QMessageBox.critical(
                self, 'Invalid Entry', 'Book title is required!', QMessageBox.Ok, QMessageBox.Ok)
            return False
        else:
            query.exec_(
                f"SELECT * FROM BOOKS WHERE BOOK_TITLE = '{book_title}' AND CATEGORY = '{category}'")

            data = []
            while (query.next()):
                row = []
                row.append(query.value(0))
                row.append(query.value(1))
                row.append(query.value(2))
                row.append(query.value(3))
                data.append(tuple(row))

            if data == []:
                query.exec_(
                    f"SELECT * FROM BOOKS WHERE BOOK_TITLE = '{book_title}'")
                while (query.next()):
                    row = []
                    row.append(query.value(0))
                    row.append(query.value(1))
                    row.append(query.value(2))
                    row.append(query.value(3))
                    data.append(tuple(row))

                if data == []:
                    QMessageBox.information(
                        self, 'Not Found', f'"{book_title}" not found.', QMessageBox.Ok, QMessageBox.Ok)
                    self.edit_info_label.clear()
                    self.edit_extra_label.clear()
                    self.book_title_le_2.clear()
                    self.category_combo_box_2.setCurrentIndex(
                        self.category_combo_box_2.findText('Unknown'))
                    self.quantity_spin_box_2.setValue(0)

                    self.category_lw.clear()
                    self.edit_extra_label.setText(f'"{book_title}" did not appear in any category.')
                    self.edit_info_label.setText(f'"{book_title}" not found.')
                    return False

                else:
                    self.showBookSearchResults(data)
                    return 'Try different category'
            else:
                self.showBookSearchResults(data)
                return True

    def addBook(self, book_title, category, quantity):
        """
        Formasts book details and adds it to the database if it does not exist.        
        """

        if book_title == "":
            QMessageBox.critical(
                self, 'Invalid Entry', 'Book title is required!', QMessageBox.Ok, QMessageBox.Ok)
        else:
            query.exec_(
                f"""SELECT * FROM BOOKS WHERE BOOK_TITLE = '{book_title}' AND CATEGORY = '{category}'""")

            if (query.next()):
                QMessageBox.information(
                    self, 'Book exists', f'"{book_title}" already exists in "{category}" category', QMessageBox.Ok, QMessageBox.Ok)
            else:
                query.exec_(
                    f"SELECT * FROM CATEGORIES WHERE CATEGORY_NAME = '{category}'")
                if not (query.next()):
                    response = QMessageBox.question(
                        self, 'Add Category?',
                        f'''"{category}" does not exist in library. Do you want add it to the library?\n\nNB: If not, "{book_title}" will not be added to library.''',
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

                    if response == QMessageBox.Yes:
                        self.addCategory(category, None)
                        query.exec_(
                            f"INSERT INTO BOOKS(BOOK_TITLE, CATEGORY, QUANTITY) VALUES('{book_title}', '{category}', '{quantity}')")
                        QMessageBox.information(
                            self, 'Operation Successful', 'Book successfully added!', QMessageBox.Ok, QMessageBox.Ok)
                        self.book_title_le.clear()
                        index = self.category_combo_box.findText("Unknown")
                        self.category_combo_box.setCurrentIndex(index)
                        self.quantity_spin_box.setValue(0)
                        
                        self.updateAllBooksTableView()

                else:
                    query.exec_(
                        f"INSERT INTO BOOKS(BOOK_TITLE, CATEGORY, QUANTITY) VALUES('{book_title}', '{category}', '{quantity}')")
                    QMessageBox.information(
                        self, 'Operation Successful', 'Book successfully added!', QMessageBox.Ok, QMessageBox.Ok)
                    self.book_title_le.clear()
                    index = self.category_combo_box.findText("Unknown")
                    self.category_combo_box.setCurrentIndex(index)
                    self.quantity_spin_box.setValue(0)

                    self.updateAllBooksTableView()

    def deleteBook(self, book_title: str, category: str):

        found = self.searchBook(book_title, category)

        if found == True:
            response = QMessageBox.question(
                self, 'Delete book', f'Are you sure you want to delete all books titled "{book_title}" in "{category}" category from the library?\n\nClick No to change category.\nNB: This can\'t be undone.',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

            if response == QMessageBox.Yes:
                query.exec_(
                    f"""DELETE FROM BOOKS WHERE BOOK_TITLE='{book_title}' AND CATEGORY='{category}'""")
                self.edit_info_label.setText(f'"{book_title}" deleted from "{category}" category.')
                self.book_title_le_2.clear()
                index = self.category_combo_box_2.findText("Unknown")
                self.category_combo_box_2.setCurrentIndex(index)
                self.quantity_spin_box_2.setValue(0)
                self.edit = []
                self.updateCategoryList([(None, book_title, None, None)])
                self.updateAllBooksTableView()

        if found == 'Try different category':
            QMessageBox.information(
                self, 'Book Not found', f'{book_title} is not in {category} category.\n\nTry different category.', QMessageBox.Ok, QMessageBox.Ok)

    def editBook(self, book_title, category, quantity):
        if self.edit == []:
            QMessageBox.information(
                self, 'Search First', 'You have not searched for book.\n\nFirst search for book in library to obtain it\'s data before you can edit it.',
                QMessageBox.Ok, QMessageBox.Ok)
        elif self.edit == [(self.edit[0][0], book_title, category, quantity)]:
            QMessageBox.information(
                self, 'No Change Detected', 'You have not made any change to book',
                QMessageBox.Ok, QMessageBox.Ok)
        else:
            print(self.edit)
            print(book_title, category, quantity)
            print(query.exec_(f"UPDATE BOOKS SET BOOK_TITLE='{book_title}', CATEGORY='{category}', QUANTITY='{quantity}' WHERE BOOK_ID='{self.edit[0][0]}'"))
            QMessageBox.information(
                self, 'Changes Successful', 'Book successfully edited!', QMessageBox.Ok, QMessageBox.Ok)

            self.updateAllBooksTableView()
            self.updateCategoryCombox()
            self.updateCategoryList(self.edit)

    def returnBook(book_title, num=1):

        update_book_query = f'''UPDATE BOOKS SET QUANTITY = QUANTITY+{num} WHERE BOOK_TITLE={book_title}'''
        query.exec_(update_book_query)

    def lendBook(book_title, num=1):

        update_book_query = f'''UPDATE BOOKS SET QUANTITY = QUANTITY-{num} WHERE BOOK_TITLE={book_title}'''
        query.exec_(update_book_query)

    def addCategory(self, category_name: str, label: QLabel) -> None:
        """
        Adds category to database if it does not exist.

        """
        if category_name:
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
                        f'"{category_name}" category successfully added to library.')
                    self.add_category_le.clear()

        else:
            if label is not None:
                label.setText("NO INPUT GIVEN!")

    def searchCategory(self, category_name: str) -> None:
        """
        Checks if category already exists.

        """
        if category_name:
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
