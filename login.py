from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QMessageBox, QHeaderView, QMainWindow, QWidget
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlRelationalTableModel, QSqlRelation, QSqlTableModel
from PyQt5 import uic
import hashlib
import hmac
import sys
import os
from ast import literal_eval


def initializeDatabase() -> None:
    """
    Creates tables  (users, books, transactions, categories) if database was did not exist.\n
    Creates admin user.
    """
    create_users_table_query = '''CREATE TABLE IF NOT EXISTS users (
                                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_name   VARCHAR (30)    NOT NULL
                                                            UNIQUE,
                                user_password   VARCHAR  NOT NULL
                            );
                            '''
    create_books_table_query = '''CREATE TABLE IF NOT EXISTS books (
                                book_id    INTEGER  PRIMARY KEY AUTOINCREMENT,
                                book_title VARCHAR NOT NULL,
                                category   VARCHAR NOT NULL,
                                quantity   INTEGER NOT NULL,
                                UNIQUE (book_title, category), 
                                CONSTRAINT category FOREIGN KEY(category) REFERENCES categories (category)
                            );
                            '''
    create_clients_table_query = '''CREATE TABLE IF NOT EXISTS clients (
                                    client_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                                    client_name TEXT    NOT NULL,
                                    client_class    TEXT    NOT NULL,
                                    client_house    TEXT    NOT NULL,
                                    UNIQUE (client_name, client_class, client_house)
                                    );'''
    create_client_records_table_query = '''CREATE TABLE IF NOT EXISTS client_records (
                                        client_record_id   INTEGER  PRIMARY KEY AUTOINCREMENT,
                                        client_id  INTEGER
                                                NOT NULL,
                                        book_id    INTEGER REFERENCES books (book_id) 
                                                        NOT NULL,
                                        quantity INTEGER NOT NULL,
                                        returned    BOOLEAN NOT NULL,
                                        UNIQUE (client_id, book_id),
                                        CONSTRAINT client FOREIGN KEY(client_id) REFERENCES clients (client_id),
                                        CONSTRAINT book FOREIGN KEY(book_id) REFERENCES books (book_id)
                            );'''
    create_transactions_table_query = '''CREATE TABLE IF NOT EXISTS transactions (
                                    transaction_id INTEGER  PRIMARY KEY AUTOINCREMENT,
                                    client_id   NOT NULL,
                                    book_id TEXT    NOT NULL,
                                    quantity INTEGER NOT NULL,
                                    type    TEXT    NOT NULL,
                                    user_id INTEGER NOT NULL,
                                    datetime    datetime NOT NULL,
                                    CONSTRAINT book FOREIGN KEY(book_id) REFERENCES books (book_id),
                                    CONSTRAINT client FOREIGN KEY(client_id) REFERENCES clients (client_id),
                                    CONSTRAINT user FOREIGN KEY(user_id) REFERENCES Users (user_id));'''
    create_categories_table_query = '''CREATE TABLE IF NOT EXISTS categories (
                                category VARCHAR PRIMARY KEY);'''
    create_client_record_view_query = '''CREATE VIEW IF NOT EXISTS client_record_vw AS
                                        SELECT books.book_title AS BOOK_TITLE,
                                               books.category AS CATEGORY,
                                               client_records.quantity AS OWING_QUANTITY,
                                               returned AS RETURNED
                                          FROM client_records
                                               INNER JOIN
                                               books ON client_records.book_id = books.book_id;'''

    query.exec_(create_users_table_query)
    query.exec_(create_books_table_query)
    query.exec_(create_transactions_table_query)
    query.exec_(create_categories_table_query)
    query.exec_(create_clients_table_query)
    query.exec_(create_client_records_table_query)
    query.exec_(create_client_record_view_query)

    query.exec_("INSERT INTO categories VALUES('Unknown')")

    hashed_user_password = str(hashPassword('admin'))
    query.prepare('INSERT INTO users(user_name, user_password) VALUES(?, ?)')
    query.addBindValue('admin')
    query.addBindValue(hashed_user_password)
    query.exec_()


def hashPassword(password: str) -> bytes:
    """
    Hashes password and concatenates with a salt.    
    """
    salt = os.urandom(16)
    hashed_user_password = hashlib.pbkdf2_hmac(
        'sha256', password.encode(), salt, 100000)
    return hashed_user_password + salt


def password_check(entered_password: str, db_password: bytes) -> bool:
    """
    Hashes entered password using salt from hashed password pulled from database then compares both passwords.
    """
    salt = db_password[-16:]
    hashed_entered_password = hashlib.pbkdf2_hmac(
        'sha256', entered_password.encode(), salt, 100000) + salt
    return hmac.compare_digest(hashed_entered_password, db_password)


login, _ = uic.loadUiType('login.ui')
main, _ = uic.loadUiType('main.ui')


class LoginWindow(QWidget, login):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        initializeDatabase()
        self.login_btn.clicked.connect(self.handleLogin)

    def handleLogin(self):
        username = self.username_le.text()
        password = self.password_le.text()

        query.exec_(
            f"SELECT user_id, user_password FROM users WHERE user_name = '{username}'")
        data = []
        while query.next():
            data.append((query.value(0)))
            data.append((query.value(1)))
        try:
            if password_check(password, literal_eval(data[1])):
                self.main_window = MainApp(data[0], username)
                self.close()
                self.main_window.show()
            else:
                self.label.setText(
                    'Make sure you entered Your username and password correctly.')
        except IndexError:
            self.label.setText(
                'Make sure you entered Your username and password correctly.')


class MainApp(QMainWindow, main):

    def __init__(self, user_id, username):
        QWidget.__init__(self)
        self.edit = []
        self.user_id = user_id
        self.username = username
        self.setupUi(self)
        self.handleUi()
        self.handleButtons()

    def handleUi(self):
        classes = ['8A1', '8A2', '8A3', '8A4', '9B1', '9B2', '9B3', '9B4', '10C1', '10C2', '10C3', '10C4', '10C5',
                   '10C6', '11D1', '11D2', '11D3', '11D4', '11D5', '11D6', '12E1', '12E2', '12E3', '12E4', '12E5',
                   '12E6']
        houses = ['H1WA', 'H1WB', 'H1WC', 'H1WD', 'H2WA', 'H2WB', 'H2WC', 'H2WD', 'H3WA', 'H3WB', 'H3WC', 'H3WD',
                  'H4WA',
                  'H4WB', 'H4WC', 'H4WD', 'H5WA', 'H5WB', 'H5WC', 'H5WD', 'H6WB', 'H6WC', 'H6WD', 'H7WB', 'H7WC',
                  'H7WD',
                  'H8WA', 'H8WB', 'H8WC', 'H8WD']
        self.class_combo_box.addItems(classes)
        self.house_combo_box.addItems(houses)
        self.class_combo_box.setCurrentIndex(-1)
        self.house_combo_box.setCurrentIndex(-1)
        self.main_tab_widget.tabBar().setVisible(False)
        self.main_tab_widget.setObjectName('main_tab_widget')
        self.setupCategoryComboBox()
        self.setupTableView()
        self.setupClientRecordView()

    def setupCategoryComboBox(self):
        self.category_cb_model = QSqlTableModel()
        self.category_cb_model.setTable('categories')
        column = self.category_cb_model.fieldIndex('category')
        self.category_cb_model.setSort(column, Qt.AscendingOrder)
        self.category_cb_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.category_cb_model.select()
        self.category_combo_box.setModel(self.category_cb_model)
        self.category_combo_box_2.setModel(self.category_cb_model)
        self.category_combo_box_3.setModel(self.category_cb_model)

        index = self.category_combo_box.findText("Unknown")
        self.category_combo_box.setCurrentIndex(index)
        self.category_combo_box_2.setCurrentIndex(index)
        self.category_combo_box_3.setCurrentIndex(index)

    def setupTableView(self):
        self.book_table_model = QSqlRelationalTableModel()
        self.book_table_model.setTable('books')
        self.book_table_model.setRelation(self.book_table_model.fieldIndex('category'), QSqlRelation(
            'categories', 'category', 'category'))
        self.all_books_table_view.setModel(self.book_table_model)
        self.all_books_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.book_table_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.book_table_model.setQuery(
            QSqlQuery("SELECT book_title, category, quantity FROM books ORDER BY book_title, category"))

    def setupClientRecordView(self):
        self.client_record_table_model = QSqlTableModel()
        self.client_record_table_model.setTable('client_record_vw')
        self.client_record_tv.setModel(self.client_record_table_model)
        self.client_record_tv.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.client_record_table_model.select()

    def updateCategoryList(self, data):
        self.category_lw.clear()
        query.exec_(
            f"SELECT category FROM books WHERE book_title = '{data[0][1]}'")
        data_2 = []
        while query.next():
            data_2.append(query.value(0))
        self.category_lw.addItems([cate for cate in data_2])
        if not data_2:
            self.edit_extra_label.setText(
                f'"{data[0][1]}" did not appear in any category.')

    def showClientRecord(self):
        pass

    @staticmethod
    def resetTab(title_le, category_cb, quantity_sb, name_le=None, class_cb=None, house_cb=None):
        title_le.clear()
        index = category_cb.findText("Unknown")
        category_cb.setCurrentIndex(index)
        quantity_sb.setValue(0)

        if name_le is not None:
            name_le.clear()
            class_cb.setCurrentIndex(-1)
            house_cb.setCurrentIndex(-1)

    def categorySelected(self):
        book_title = self.edit_extra_label.text().split(' ')[0].strip('"')
        category = self.category_lw.selectedItems()[0].data(0)
        self.searchBook(book_title, category)

    def completeBookEdit(self, book_title, category, quantity):
        query.exec_(
            f"UPDATE books SET book_title='{book_title}', category='{category}', quantity='{quantity}' WHERE book_id='{self.edit[0][0]}'")
        QMessageBox.information(
            self, 'Changes Successful', 'Book successfully edited!', QMessageBox.Ok, QMessageBox.Ok)
        self.book_table_model.submitAll()
        self.category_cb_model.submitAll()
        self.edit = []
        self.resetTab(
            self.book_title_le_2, self.category_combo_box_2, self.quantity_spin_box_2)
        index = self.category_combo_box.findText("Unknown")
        self.category_combo_box.setCurrentIndex(index)
        self.category_combo_box_3.setCurrentIndex(index)
        self.edit_info_label.clear()
        self.edit_extra_label.clear()
        self.category_lw.clear()

    def completeLendBook(self, book_id, quantity):
        client_id = self.addClient(self.client_name_le.text().strip().capitalize(), self.class_combo_box.currentText(
        ), self.house_combo_box.currentText())

        if client_id:
            query.exec_(
                f"""INSERT INTO client_records(client_id, book_id, quantity, returned) VALUES('{client_id}', '{book_id}', '{quantity}', 'FALSE')""")

            if query.lastError().isValid():
                query.exec_(
                    f"""SELECT client_record_id FROM client_records WHERE client_id="{client_id}" AND book_id='{book_id}'""")
                client_book_id = None
                while query.next():
                    client_book_id = query.value(0)

                query.exec_(f"""UPDATE client_records SET quantity=quantity+'{quantity}' WHERE client_record_id='{client_book_id}'""")

            query.exec_(
                f"""INSERT INTO transactions(client_id, book_id, quantity, type, user_id, datetime) 
                VALUES('{client_id}', '{book_id}', '{quantity}', 'LEND', '{self.user_id}', DATETIME())""")
            query.exec_(
                f"""UPDATE books SET quantity=quantity-'{quantity}' WHERE book_id='{book_id}'""")
            self.book_table_model.submitAll()
            self.resetTab(self.book_title_le_3, self.category_combo_box_3, self.quantity_spin_box_3,
                          self.client_name_le, self.class_combo_box, self.house_combo_box)

    def handleButtons(self):
        self.dashboard_btn.clicked.connect(self.open_dashboard_tab)
        self.books_btn.clicked.connect(self.open_books_tab)
        self.issue_book_btn.clicked.connect(self.open_issue_book_tab)
        self.history_btn.clicked.connect(self.open_history_tab)
        self.settings_btn.clicked.connect(self.open_settings_tab)
        self.add_book_btn.clicked.connect(lambda: self.addBook(self.book_title_le.text().capitalize(
        ), self.category_combo_box.currentText().capitalize(), self.quantity_spin_box.value()))
        self.delete_book_btn.clicked.connect(
            lambda: self.deleteBook(self.book_title_le_2.text().capitalize(),
                                    self.category_combo_box_2.currentText().capitalize()))
        self.search_book_btn.clicked.connect(
            lambda: self.searchBook(self.book_title_le_2.text().capitalize(),
                                    self.category_combo_box_2.currentText().capitalize()))
        self.edit_book_btn.clicked.connect(lambda: self.editBook(self.book_title_le_2.text().capitalize(
        ), self.category_combo_box_2.currentText().capitalize(), self.quantity_spin_box_2.value()))
        self.add_category_btn.clicked.connect(
            lambda: self.addCategory(self.add_category_le.text().capitalize(), self.category_info_label))
        self.search_category_btn.clicked.connect(
            lambda: self.searchCategory(self.add_category_le.text().capitalize()))
        self.lend_book_btn.clicked.connect(lambda: self.lendBook(self.book_title_le_3.text().capitalize(
        ), self.category_combo_box_3.currentText().capitalize(), self.quantity_spin_box_3.value()))

        self.category_lw.itemClicked.connect(self.categorySelected)

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
                f"SELECT * FROM books WHERE book_title = '{book_title}' AND category = '{category}'")

            data = []
            while query.next():
                row = [query.value(0), query.value(1), query.value(2), query.value(3)]
                data.append(tuple(row))

            if not data:
                query.exec_(
                    f"SELECT * FROM books WHERE book_title = '{book_title}'")
                while query.next():
                    row = [query.value(0), query.value(1), query.value(2), query.value(3)]
                    data.append(tuple(row))

                if not data:
                    QMessageBox.information(
                        self, 'Not Found', f'"{book_title}" not found.', QMessageBox.Ok, QMessageBox.Ok)
                    self.edit_info_label.clear()
                    self.edit_extra_label.clear()
                    self.resetTab(
                        self.book_title_le_2, self.category_combo_box_2, self.quantity_spin_box_2)

                    self.category_lw.clear()
                    self.edit_extra_label.setText(
                        f'"{book_title}" did not appear in any category.')
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
        Adds book and or category to the database if it does not exist.
        """

        if book_title == "" or category == "" or quantity == "":
            QMessageBox.critical(
                self, 'Invalid Entry', 'Book title is required!', QMessageBox.Ok, QMessageBox.Ok)
        else:
            res = self.addCategory(category, None)
            query.exec_(
                f"INSERT INTO books(book_title, category, quantity) VALUES('{book_title}', '{category}', '{quantity}')")
            self.book_table_model.submitAll()
            if query.lastError().isValid():
                QMessageBox.information(
                    self, 'Book exists', f'"{book_title}" already exists in "{category}" category', QMessageBox.Ok,
                    QMessageBox.Ok)

            elif res != 'exists':
                QMessageBox.information(
                    self, 'Operation Successful', f'"{book_title}" and "{category}" category were successfully added!', QMessageBox.Ok, QMessageBox.Ok)
            else:
                QMessageBox.information(
                    self, 'Operation Successful', f'"{book_title}" was successfully added!', QMessageBox.Ok, QMessageBox.Ok)
            self.resetTab(self.book_title_le, self.category_combo_box, self.quantity_spin_box)

    def deleteBook(self, book_title: str, category: str):

        found = self.searchBook(book_title, category)

        if found:
            response = QMessageBox.question(
                self, 'Delete book',
                f'Are you sure you want to delete all books titled "{book_title}" in "{category}" category from the library?\n\nClick No to change category.\nNB: This can\'t be undone.',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

            if response == QMessageBox.Yes:
                query.exec_(
                    f"""DELETE FROM books WHERE book_title='{book_title}' AND category='{category}'""")
                self.edit_info_label.setText(
                    f'"{book_title}" deleted from "{category}" category.')
                self.resetTab(
                    self.book_title_le_2, self.category_combo_box_2, self.quantity_spin_box_2)
                self.edit = []
                self.updateCategoryList([(None, book_title, None, None)])
                self.book_table_model.submitAll()

        if found == 'Try different category':
            QMessageBox.information(
                self, 'Book Not found', f'{book_title} is not in {category} category.\n\nTry different category.',
                QMessageBox.Ok, QMessageBox.Ok)

    def editBook(self, book_title, category, quantity):
        if not self.edit:
            QMessageBox.information(
                self, 'Search First',
                'You have not searched for book.\n\nFirst search for book in library to obtain it\'s data before you can edit it.',
                QMessageBox.Ok, QMessageBox.Ok)
        elif self.edit == [(self.edit[0][0], book_title, category, quantity)]:
            QMessageBox.information(
                self, 'No Change Detected', 'You have not made any change to book',
                QMessageBox.Ok, QMessageBox.Ok)
        else:
            if self.edit[0][2] != category:
                found = self.searchBook(book_title, category)
                if found is True:
                    QMessageBox.information(
                        self, 'Exists', f'"{book_title}" already exists in "{category}".', QMessageBox.Ok,
                        QMessageBox.Ok)
                else:
                    self.completeBookEdit(book_title, category, quantity)
            else:
                self.completeBookEdit(book_title, category, quantity)

    def addClient(self, name, class_, house):
        if name == "" or class_ == "" or house == "":
            QMessageBox.information(
                self, 'Invalid', 'Fill out all entries.', QMessageBox.Ok, QMessageBox.Ok)
            return None

        else:
            query.exec_(
                f"""INSERT INTO clients(client_name, client_class, client_house) VALUES('{name}', '{class_}', '{house}')""")
            print(query.lastError().text())
            query.exec_(
                f"""SELECT client_id FROM clients WHERE client_name = '{name}' AND client_class = '{class_}' AND client_house = '{house}'""")

            while query.next():
                client_id = query.value(0)
                return client_id

    def returnBook(self, book_title, num=1):

        update_book_query = f'''UPDATE books SET quantity = quantity+{num} WHERE book_title={book_title}'''
        query.exec_(update_book_query)

    def lendBook(self, book_title, category, quantity):

        query.exec_(
            f"""SELECT * FROM books WHERE book_title='{book_title}' AND category='{category}'""")
        data = {}
        while query.next():
            data['book_id'] = int(query.value(0))
            data['quantity'] = int(query.value(3))
        if not data:
            QMessageBox.information(
                self, 'Not Found',
                f'"{book_title}" is not in "{category}" category. Make sure you have spelled them correctly or search using the Edit/Delete tab.',
                QMessageBox.Ok, QMessageBox.Ok)

        elif data['quantity'] == 0:
            QMessageBox.information(
                self, 'Out Of Book',
                f'Out of "{book_title}" in "{category}" category. Try search for it in different category using the Edit/Delete tab.',
                QMessageBox.Ok, QMessageBox.Ok)
        else:
            if data['quantity'] < quantity:
                if data['quantity'] == 1:
                    quantity_words = ['is', 'book']
                else:
                    quantity_words = ['are', 'books']
                response = QMessageBox.question(self, 'Not Enough Books',
                                                f'There {quantity_words[0]} only {data["quantity"]} {quantity_words[1]} titled "{book_title}" in "{category}" category left.\n\nDo you want to get all of them?',
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if response == QMessageBox.Yes:
                    quantity = data['quantity']
                    self.completeLendBook(data['book_id'], quantity)

            else:
                self.completeLendBook(data['book_id'], quantity)

    def addCategory(self, category: str, label: QLabel or None) -> str or None:
        """
        Adds category to database if it does not exist.
        """
        if category:
            query.exec_(
                f"INSERT INTO categories VALUES('{category}')")
            self.category_cb_model.submitAll()
            index = self.category_combo_box.findText('Unknown')
            self.category_combo_box.setCurrentIndex(index)
            self.category_combo_box_2.setCurrentIndex(index)
            self.category_combo_box_3.setCurrentIndex(index)

            if label is not None:
                label.setText(
                    f'"{category}" category successfully added to library.')
                self.add_category_le.clear()

            if query.lastError().isValid():
                if label is not None:
                    label.setText(
                        f'"{category}" category already exists in library.')
                return 'exists'

        else:
            if label is not None:
                label.setText("NO INPUT GIVEN!")
        query.clear()

    def searchCategory(self, category: str) -> None:
        """
        Checks if category already exists.

        """
        if category:
            query.exec_(
                f"SELECT * FROM categories WHERE category = '{category}'")

            data = []
            while query.next():
                data.append(query.value(0))

            if not data:
                self.category_info_label.setText(
                    f'"{category}" category does not exist in library.')

            else:
                self.category_info_label.setText(
                    f'"{category}" category exists in library.')
                self.add_category_le.clear()

        else:
            self.category_info_label.setText("NO INPUT GIVEN!")


if __name__ == '__main__':
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
