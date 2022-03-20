from datetime import datetime
import hashlib
import hmac
import os
import sys
from ast import literal_eval

from PyQt5 import uic
from PyQt5.QtChart import (QChart,
                           QChartView, QDateTimeAxis, QLineSeries, QValueAxis)
from PyQt5.QtCore import QDate, QDateTime, QPoint, Qt
from PyQt5.QtGui import QEnterEvent, QPainter, QPixmap, QIcon
from PyQt5.QtSql import (QSqlDatabase, QSqlQuery, QSqlRelation,
                         QSqlRelationalTableModel, QSqlTableModel)
from PyQt5.QtWidgets import (QApplication, QButtonGroup, QDesktopWidget,
                             QHeaderView, QLabel, QLineEdit, QMainWindow,
                             QMessageBox, QPushButton,
                             QWidget)
from pandas import date_range

from queries import *


def initializeDatabase() -> None:
    """
    * Creates tables  (users, books, transactions, categories) if database was did not exist.\n
    * Creates admin user."""

    if not database.tables().__contains__("dates"):
        # Creates dates table starting from current date if it doesn't exist.
        today = datetime.today().date()
        query.exec_("CREATE TABLE dates (id integer primary key)")
        query.exec_("INSERT INTO dates DEFAULT VALUES")
        query.exec_("INSERT INTO dates DEFAULT VALUES")
        query.exec_(
            "INSERT INTO dates SELECT NULL FROM dates d1, dates d2, dates d3 , dates d4")
        query.exec_(
            "INSERT INTO dates SELECT NULL FROM dates d1, dates d2, dates d3 , dates d4")
        query.exec_("ALTER TABLE dates ADD date DATETIME")
        query.exec_(f"UPDATE dates SET date=DATE('{today}',(-1+id)||' day')")
        query.exec_("CREATE UNIQUE index ux_dates_date ON dates (date)")

    query.exec_(create_users_table_query)
    query.exec_(create_books_table_query)
    query.exec_(create_transactions_table_query)
    query.exec_(create_categories_table_query)
    query.exec_(create_clients_table_query)
    query.exec_(create_client_records_table_query)
    query.exec_(create_client_record_view_query)
    query.exec_(create_history_table_query)
    query.exec_(create_user_permissions_table_query)
    query.exec_(create_transaction_acc_view_query)

    # Creates default category, 'Unknown'.
    query.exec_("INSERT INTO categories VALUES('Unknown')")

    hashed_user_password = str(hashPassword('admin'))
    query.prepare('INSERT INTO users(user_name, user_password) VALUES(?, ?)')
    query.addBindValue('admin')
    query.addBindValue(hashed_user_password)
    query.exec_()

    query.exec_("SELECT user_name FROM user_permissions WHERE user_name='admin'")
    if not query.next():
        query.exec_(
            "INSERT INTO user_permissions VALUES('admin',1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1)")


def hashPassword(password: str) -> bytes:
    """
    Hashes password and concatenates with a salt.
    returns: hashed password of type bytes  
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


def btn_close_clicked(self):
    self.close()


def btn_max_clicked(self):
    if self.isMaximized():
        self.max_btn.setIcon(QIcon(QPixmap("./icons/maximize.png")))
        self.showNormal()
        self.title_bar.move(self.title_bar_pos, 0)

    else:
        QPushButton().setIcon(QIcon())
        self.title_bar.move(screen_width - 283, 0)
        self.max_btn.setIcon(QIcon(QPixmap("./icons/restore_down.png")))
        self.showMaximized()


def btn_min_clicked(self):
    self.showMinimized()


def centerWindow(self):
    self.move((screen_width - self.width()) // 2,
              (screen_height - self.height()) // 2)


login, _ = uic.loadUiType('login.ui')
main, _ = uic.loadUiType('main.ui')


class LoginWindow(QWidget, login):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        centerWindow(self)
        self.setFixedSize(400, 500)
        initializeDatabase()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.close_btn.clicked.connect(lambda: btn_close_clicked(self))
        self.min_btn.clicked.connect(lambda: btn_min_clicked(self))
        self.login_btn.clicked.connect(self.handleLogin)
        self.show_password_cb.stateChanged.connect(self.showPassword)

    def showPassword(self, state):
        if state == Qt.Checked:
            self.password_le.setEchoMode(QLineEdit.Normal)
        else:
            self.password_le.setEchoMode(QLineEdit.Password)

    def handleLogin(self):
        username = self.username_le.text()
        password = self.password_le.text()

        self.password_le.clear()
        query.exec_(
            f"SELECT user_id, user_password FROM users WHERE user_name = '{username}'")
        data = []
        while query.next():
            data.append((query.value(0)))
            data.append((query.value(1)))
        try:
            if password_check(password, literal_eval(data[1])):
                self.username_le.clear()
                self.show_password_cb.setChecked(False)
                self.label.clear()
                self.main_window = MainApp(data[0], username)
                self.close()
                self.main_window.show()
                query.exec_(
                    f"""INSERT INTO history(user_name, [action]) VALUES('{username}', 'LOGGED IN')""")
            else:
                self.label.setText(
                    'Make sure you entered Your username and password correctly.')
        except IndexError:
            self.label.setText(
                'Make sure you entered Your username and password correctly.')


class MainApp(QMainWindow, main):

    def __init__(self, user_id, username):
        QWidget.__init__(self)
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.user_id = user_id
        self.username = username
        self.initDashVals()
        self.handleUi()
        self.widget_2.installEventFilter(self)
        self.main_tab_widget.installEventFilter(self)
        self.main_tabs.installEventFilter(self)
        self.handleButtons()
        self._initDrag()
        self.setMouseTracking(True)
        self.edit = []  # Contains record of book to be edited
        query.exec_(f"SELECT user_name FROM users")
        self.usernames = []  # List of existing user names
        while query.next():
            self.usernames.append(query.value(0))

        query.exec_(
            f"SELECT count(*) FROM transactions WHERE user_id={self.user_id} AND DATE(datetime)='{datetime.today().date()}'")
        while query.next():
            # Number of transactions performed today
            self.today_transac_count = query.value(0)

    def _initDrag(self):
        # Set the default value of mouse tracking judgment trigger
        self._move_drag = False
        self._corner_drag = False
        self._bottom_drag = False
        self._right_drag = False

    def eventFilter(self, obj, event):
        # Event filter, used to solve the problem that the mouse returns to the standard mouse style after entering other controls
        if isinstance(event, QEnterEvent):
            self.setCursor(Qt.ArrowCursor)
        return super(MainApp, self).eventFilter(obj, event)

    def resizeEvent(self, QResizeEvent):
        # Custom window sizing events
        # Change the window size by three coordinate ranges
        self._right_rect = [QPoint(x, y) for x in range(self.width() - 5, self.width() + 5)
                            for y in range(self.widget.height() + 15, self.height() - 5)]
        self._bottom_rect = [QPoint(x, y) for x in range(1, self.width() - 5)
                             for y in range(self.height() - 5, self.height() + 1)]
        self._corner_rect = [QPoint(x, y) for x in range(self.width() - 5, self.width() + 1)
                             for y in range(self.height() - 5, self.height() + 1)]

    def mousePressEvent(self, event):
        # Override mouse click events
        if (event.button() == Qt.LeftButton) and (event.pos() in self._corner_rect):
            # Left click the border area in the lower right corner
            self._corner_drag = True
            event.accept()
        elif (event.button() == Qt.LeftButton) and (event.pos() in self._right_rect):
            # Left click on the right border area
            self._right_drag = True
            event.accept()
        elif (event.button() == Qt.LeftButton) and (event.pos() in self._bottom_rect):
            # Click the lower border area with the left mouse button
            self._bottom_drag = True
            event.accept()
        elif (event.button() == Qt.LeftButton) and (event.y() < self.widget.height()):
            # Left click on the title bar area
            self._move_drag = True
            self.move_DragPosition = event.globalPos() - self.pos()
            event.accept()

    def mouseMoveEvent(self, QMouseEvent):
        # Determine mouse position and switch mouse gesture
        if QMouseEvent.pos() in self._corner_rect:  # QMouseEvent.pos() get relative position
            self.setCursor(Qt.SizeFDiagCursor)
        elif QMouseEvent.pos() in self._bottom_rect:
            self.setCursor(Qt.SizeVerCursor)
        elif QMouseEvent.pos() in self._right_rect:
            self.setCursor(Qt.SizeHorCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

        # When the left mouse button click and meet the requirements of the click area, different window adjustments are realized
        # There is no definition of the left and top five directions, mainly because the implementation is not difficult, but the effect is very poor. When dragging and dropping, the window flickers, and then study whether there is a better implementation
        if Qt.LeftButton and self._right_drag:
            # Right adjust window width
            self.resize(QMouseEvent.pos().x(), self.height())
            self.title_bar.move(self.widget_2.width() - 105, 0)
            self.title_bar_pos = self.widget_2.width() - 105

            QMouseEvent.accept()
        elif Qt.LeftButton and self._bottom_drag:
            # Lower adjustment window height
            self.resize(self.width(), QMouseEvent.pos().y())
            QMouseEvent.accept()
        elif Qt.LeftButton and self._corner_drag:
            #  Because my window is set with rounded corners, this size adjustment is useless
            # Adjust the height and width at the same time in the lower right corner
            self.resize(QMouseEvent.pos().x(), QMouseEvent.pos().y())
            QMouseEvent.accept()
        elif Qt.LeftButton and self._move_drag:
            # Title bar drag and drop window position
            if self.isMaximized():
                btn_max_clicked(self)
            self.move(QMouseEvent.globalPos() - self.move_DragPosition)

            QMouseEvent.accept()

    def mouseReleaseEvent(self, QMouseEvent):
        # After the mouse is released, each trigger is reset
        self._move_drag = False
        self._corner_drag = False
        self._bottom_drag = False
        self._right_drag = False

    def handleUi(self):
        """Handles everything that deals with changes to the interface."""
        self.username_label_3.setText(self.username)
        centerWindow(self)
        self.title_bar_pos = 917
        self.setMaximumSize(screen_width, screen_height)
        classes = ['8A1', '8A2', '8A3', '8A4', '9B1', '9B2', '9B3', '9B4', '10C1', '10C2', '10C3', '10C4', '10C5',
                   '10C6', '11D1', '11D2', '11D3', '11D4', '11D5', '11D6', '12E1', '12E2', '12E3', '12E4', '12E5',
                   '12E6']
        houses = ['H1WA', 'H1WB', 'H1WC', 'H1WD', 'H2WA', 'H2WB', 'H2WC', 'H2WD', 'H3WA', 'H3WB', 'H3WC', 'H3WD',
                  'H4WA',
                  'H4WB', 'H4WC', 'H4WD', 'H5WA', 'H5WB', 'H5WC', 'H5WD', 'H6WB', 'H6WC', 'H6WD', 'H7WB', 'H7WC',
                  'H7WD',
                  'H8WA', 'H8WB', 'H8WC', 'H8WD']
        self.handlePermissions()
        self.class_combo_box.addItems(classes)
        self.house_combo_box.addItems(houses)
        self.class_combo_box_2.addItems(classes)
        self.house_combo_box_2.addItems(houses)
        self.class_combo_box.setCurrentIndex(-1)
        self.house_combo_box.setCurrentIndex(-1)
        self.class_combo_box_2.setCurrentIndex(-1)
        self.house_combo_box_2.setCurrentIndex(-1)
        self.main_tab_widget.tabBar().setVisible(False)
        self.setupCategoryComboBox()
        self.setupTableView()
        self.setupClientRecordView()
        self.showUsers()
        self.showHistory()
        self.transactionGraph()

    def handlePermissions(self):
        """Checks user's permissions to appropriately alter what is accessible by the user."""
        tabs = self.main_tabs.findChildren(QPushButton)
        others = [self.add_book_tab, self.edit_book_btn, self.delete_book_btn, self.add_category_btn,
                  self.lend_book_tab, self.return_book_btn, self.create_user_tab, self.delete_user_btn,
                  self.permissions_tab]
        query.exec_(
            f"""SELECT * FROM user_permissions WHERE user_name='{self.username}'""")
        index = 1
        while query.next():
            for tab in tabs:
                if query.value(index) == 1:
                    tab.setVisible(True)
                else:
                    tab.setVisible(False)
                index += 1
            for other in others:
                if query.value(index) == 1:
                    if index == 15:
                        index += 1
                    else:
                        other.setEnabled(True)
                else:
                    if index == 15:
                        self.delete_user_btn.setVisible(False)
                    else:
                        other.setEnabled(False)
                    index += 1

    def initDashVals(self):
        """Calculates the number of total books lent and retrieved all times and current
        date, as well as the outstanding books: books that have not yet been retrieved
        """
        query.exec_("SELECT sum(quantity) FROM transactions WHERE type='LEND'")
        while query.next():
            total_lent = query.value(0)
            
        query.exec_("SELECT sum(quantity) FROM transactions WHERE type='RETRIEVE'")
        while query.next():
            total_retrieved = query.value(0)
            
        query.exec_("SELECT sum(quantity) FROM transactions WHERE type='LEND' AND date(datetime) = date('now', 'localtime')")
        while query.next():
            lent_today = query.value(0)
            
        query.exec_("SELECT sum(quantity) FROM transactions WHERE type='RETRIEVE' AND date(datetime) = date('now', 'localtime')")
        while query.next():
            retrieved_today = query.value(0)
            
        self.total_lent_val.setText(str(total_lent))
        self.total_retrieved_val.setText(str(total_retrieved))
        self.lent_today_val.setText(str(lent_today))
        self.retrieved_today_val.setText(str(retrieved_today))
        self.outstanding_val.setText(str(total_lent - total_retrieved))
    
    @staticmethod
    def increase_dash_val(label, quantity):
        """Increase dashboard value by a certain quantity
        """
        val = int(label.text()) + quantity
        label.setText(str(val))
        
    @staticmethod
    def decrease_dash_val(label, quantity):
        """Decrease dashboard value by a certain quantity
        """
        val = int(label.text()) - quantity
        label.setText(str(val))
    
    def setupCategoryComboBox(self):
        """Loads categories from category table as items in the combo-box"""
        self.category_cb_model = QSqlTableModel()
        self.category_cb_model.setTable('categories')
        column = self.category_cb_model.fieldIndex('category')
        self.category_cb_model.setSort(column, Qt.AscendingOrder)
        self.category_cb_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.category_cb_model.select()
        self.category_combo_box.setModel(self.category_cb_model)
        self.category_combo_box_2.setModel(self.category_cb_model)
        self.category_combo_box_3.setModel(self.category_cb_model)

        # Give default values
        index = self.category_combo_box.findText("Unknown")
        self.category_combo_box.setCurrentIndex(index)
        self.category_combo_box_2.setCurrentIndex(index)
        self.category_combo_box_3.setCurrentIndex(index)

    def booksTableSort(self):
        self.book_table_model.setQuery(
            QSqlQuery("SELECT * FROM books ORDER BY category, book_title"))
    def setupTableView(self):
        """Loads and displays all books from books table, and sorts them first according to category the book-title"""
        self.book_table_model = QSqlRelationalTableModel()
        self.book_table_model.setTable('books')
        self.book_table_model.setRelation(self.book_table_model.fieldIndex('category'), QSqlRelation(
            'categories', 'category', 'category'))
        self.all_books_table_view.setModel(self.book_table_model)
        self.all_books_table_view.horizontalHeader(
        ).setSectionResizeMode(QHeaderView.Stretch)
        self.book_table_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.all_books_table_view.hideColumn(0)
        self.booksTableSort()
        

    def setupClientRecordView(self):
        """Creates table to load books a client has not returned."""
        self.client_record_table_model = QSqlTableModel()
        self.client_record_table_model.setTable('client_record_vw')
        self.client_record_tv.setModel(self.client_record_table_model)
        self.client_record_tv.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for column_hidden in (0, 1, 2):
            self.client_record_tv.hideColumn(column_hidden)

    def updateCategoryList(self, data: list):
        """Updates the list of categories of book searched by user

        Args:
            data (list): book record [book_id, book_title, category, quantity]
        """
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

    def showHistory(self):
        """Loads and displays history of user activities"""
        
        self.history_table_model = QSqlTableModel()
        self.history_table_model.setTable('history')
        self.history_tv.setModel(self.history_table_model)
        self.history_tv.horizontalHeader(
        ).setSectionResizeMode(QHeaderView.Stretch)
        column = self.history_table_model.fieldIndex('datetime')
        self.history_table_model.setSort(column, Qt.DescendingOrder)
        self.history_table_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.history_table_model.select()

    def showClientRecord(self, fname: str, lname: str, class_: str, house: str):
        """Loads and displays books a client has not returned"""

        self.client_info_label.setText(
            f"{fname} {lname}\t{class_}\t{house}")  # Displays client information

        for column_hidden in (0, 1, 2):
            self.client_record_tv.setColumnHidden(
                column_hidden, False)  # Hides unnecessary columns

        self.client_record_table_model.setQuery(
            QSqlQuery(f"""SELECT BOOK_TITLE, CATEGORY, OWING_QUANTITY, RETURNED FROM client_record_vw 
                        WHERE client_name='{fname} {lname}' 
                        AND client_class='{class_}' 
                        AND client_house='{house}'
                        AND RETURNED=FALSE"""))

    @staticmethod
    def formatText(text: str) -> str:
        """Cleans user input by removing trailing whitespaces 
        and capitalizes first letter of each word"""

        return text.strip().title()

    @staticmethod
    def clear_book_entry(title_le, category_cb, quantity_sb):
        """Gives book input fields their default values"""
        title_le.clear()
        index = category_cb.findText("Unknown")
        category_cb.setCurrentIndex(index)
        quantity_sb.setValue(0)

    @staticmethod
    def clear_client_entry(fname_le, lname_le, class_cb, house_cb):
        """Gives client input fields their default values"""
        fname_le.clear()
        lname_le.clear()
        class_cb.setCurrentIndex(-1)
        house_cb.setCurrentIndex(-1)

    def loadTransactionData(self) -> list[list, list]:
        """Loads transactions from transaction_acc_vw and returns them according to type.

        Returns:
            list[list, list]: [[[lent_quantities], [lent_dates]], [[retrieved_quantities], [retrieved_dates]]]
        """
        query.exec_("SELECT * FROM transaction_acc_vw")
        lend_xy = [[], []]
        retrieve_xy = [[], []]
        while query.next():
            if query.value(1) == 'RETRIEVE':
                retrieve_xy[0].append(query.value(2))
                retrieve_xy[1].append(query.value(0))
            elif query.value(1) == 'LEND':
                lend_xy[0].append(query.value(2))
                lend_xy[1].append(query.value(0))
            else:
                retrieve_xy[0].append(query.value(2))
                retrieve_xy[1].append(query.value(0))
                lend_xy[0].append(query.value(2))
                lend_xy[1].append(query.value(0))

        return lend_xy, retrieve_xy

    def transactionGraph(self):
        """Creates transactions graph and populates it with
        data from the loadTransactionData function.
        """
        def appendTransDataToSeries(trans_data, series):
            """Traverses over transactions' dates, sets to a DateTime format
            then adds each to the lent series"""
            for i in range(len(trans_data[0])):
                year, month, date_ = [int(data) for data in trans_data[0][i].split('-')]
                date = QDateTime()
                date.setDate(QDate(year, month, date_))
                series.append(date.toMSecsSinceEpoch(), trans_data[1][i])
            
        lent_trans, retrieved_trans = self.loadTransactionData() #Gets transactions from database by type
        l_series = QLineSeries()
        r_series = QLineSeries()
        l_series.setName('Lent')
        r_series.setName('Retrieved')

        appendTransDataToSeries(lent_trans, l_series)
        appendTransDataToSeries(retrieved_trans, r_series)

        self.chart = QChart()
        self.chart.addSeries(l_series)
        self.chart.addSeries(r_series)

        self.axis_x = QDateTimeAxis()
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        l_series.attachAxis(self.axis_x)
        r_series.attachAxis(self.axis_x)
        self.axis_x.setTickCount(10)
        self.axis_x.setFormat('dd MMM')

        self.axis_y = QValueAxis()
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        l_series.attachAxis(self.axis_y)
        r_series.attachAxis(self.axis_y)
        self.axis_y.setTickType(0)
        self.axis_y.setMax(max(max(lent_trans[1]), max(retrieved_trans[1]))+2)
        self.axis_y.setTickInterval(4)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.report_layout.addChildWidget(self.chart_view)

    def categorySelected(self):
        """Searches for a book of the category selected. User can only select 
        the category when she/he had first searched for the book in another category.
        A list of other category that the book appears in is shown after the search.
        """
        book_title = self.edit_extra_label.text().split('"')[1]
        category = self.category_lw.selectedItems()[0].data(0)
        self.searchBook(book_title, category)

    def bookSelected(self):
        """
        * Displays book to be returned and its Category.
        * It gets the quantity of the book borrowed and sets it as the maximum number of the
        book to be returned by the client
        """
        row = self.client_record_tv.currentIndex().row()
        book_title = self.client_record_tv.currentIndex().sibling(row, 0).data()
        category = self.client_record_tv.currentIndex().sibling(row, 1).data()
        quantity = int(
            self.client_record_tv.currentIndex().sibling(row, 2).data())
        self.book_title_category_label.setText(
            f'"{book_title}" | "{category}"')
        self.quantity_spin_box_4.setMaximum(quantity)

    def handleButtons(self):
        """Connects buttons to functions that are invoked when the buttons are triggered"""
        
        self.close_btn.clicked.connect(lambda: btn_close_clicked(self))
        self.min_btn.clicked.connect(lambda: btn_min_clicked(self))
        self.max_btn.clicked.connect(lambda: btn_max_clicked(self))
        self.b_group = QButtonGroup()
        self.b_group.addButton(self.checkBox_21)
        self.b_group.addButton(self.checkBox_22)
        self.b_group.buttonClicked.connect(self.checkPermissions)
        self.logout_btn.clicked.connect(self.handleLogout)
        self.dashboard_btn.clicked.connect(self.open_dashboard_tab)
        self.books_btn.clicked.connect(self.open_books_tab)
        self.issue_book_btn.clicked.connect(self.open_issue_book_tab)
        self.report_btn.clicked.connect(self.open_report_tab)
        self.history_btn.clicked.connect(self.open_history_tab)
        self.settings_btn.clicked.connect(self.open_settings_tab)
        self.users_btn.clicked.connect(self.open_users_tab)
        self.add_book_btn.clicked.connect(
            lambda: self.addBook(self.formatText(self.book_title_le.text()),
                                 self.formatText(
                                     self.category_combo_box.currentText()),
                                 self.quantity_spin_box.value()))
        self.delete_book_btn.clicked.connect(
            lambda: self.deleteBook(self.formatText(self.book_title_le_2.text()),
                                    self.formatText(self.category_combo_box_2.currentText())))
        self.search_book_btn.clicked.connect(
            lambda: self.searchBook(self.formatText(self.book_title_le_2.text()),
                                    self.formatText(self.category_combo_box_2.currentText())))
        self.edit_book_btn.clicked.connect(
            lambda: self.editBook(self.formatText(self.book_title_le_2.text()),
                                  self.formatText(
                                      self.category_combo_box_2.currentText()),
                                  self.quantity_spin_box_2.value()))
        self.add_category_btn.clicked.connect(
            lambda: self.addCategory(self.formatText(self.add_category_le.text()), self.category_info_label))
        self.search_category_btn.clicked.connect(
            lambda: self.searchCategory(self.formatText(self.add_category_le.text())))
        self.lend_book_btn.clicked.connect(
            lambda: self.lendBook(self.formatText(self.book_title_le_3.text()),
                                  self.formatText(
                                      self.category_combo_box_3.currentText()),
                                  self.quantity_spin_box_3.value()))
        self.client_search_btn.clicked.connect(
            lambda: self.showClientRecord(self.formatText(self.fname_le_2.text()),
                                          self.formatText(self.lname_le_2.text(
                                          )), self.class_combo_box_2.currentText(),
                                          self.house_combo_box_2.currentText()))
        self.return_book_btn.clicked.connect(
            lambda: self.retrieveBook(self.book_title_category_label.text(), self.quantity_spin_box_4.value()))
        self.password_le_2.textChanged.connect(self.confirmPassword)
        self.password_le.textChanged.connect(self.confirmPassword)
        self.username_le.textChanged.connect(self.usernameConfirm)
        self.create_user_btn.clicked.connect(self.createUser)
        self.delete_user_btn.clicked.connect(self.deleteUser)
        self.users_tv.selectionModel().selectionChanged.connect(self.userSelected)
        self.clear_btn.clicked.connect(
            lambda: self.clear_client_entry(
                self.fname_le_2, self.lname_le_2, self.class_combo_box_2, self.house_combo_box_2)
        )
        self.load_permissions_btn.clicked.connect(self.loadUserPermssions)
        self.give_permissions_btn.clicked.connect(self.giveUserPermissions)
        self.username_le_2.textChanged.connect(self.enablePermissionSearch)

        self.category_lw.itemClicked.connect(self.categorySelected)
        self.client_record_tv.selectionModel().selectionChanged.connect(self.bookSelected)
        self.show_password_cb.stateChanged.connect(self.showPassword)

    def handleLogout(self):
        self.close()
        login_window.show()

    def closeEvent(self, event):
        query.exec_(
            f"""INSERT INTO history(user_name, [action]) VALUES('{self.username}', 'LOGGED OUT')""")
        event.accept()

    def checkPermissions(self, cb):
        permissions = self.tab_permissions.children() + self.other_permissions.children()
        if cb.text() == 'Admin Permissions':
            for permission in permissions:
                permission.setChecked(True)
        elif cb.text() == 'Standard Permissions':
            for permission in permissions:
                if permission.text() in ['History', 'Users', 'Delete book', 'Create User', 'Delete User',
                                         'Give Permissions']:
                    permission.setChecked(False)
                else:
                    permission.setChecked(True)

    def enablePermissionSearch(self):
        username = self.username_le_2.text().strip()
        if username in self.usernames:
            self.load_permissions_btn.setEnabled(True)
            self.username_label_2.clear()
        elif not username:
            self.username_label_2.clear()
        else:
            self.username_label_2.setText(f'"{username}" is not a user.')
            self.load_permissions_btn.setEnabled(False)

    def loadUserPermssions(self):
        username = self.username_le_2.text().strip()
        permissions = self.tab_permissions.children() + self.other_permissions.children()
        
        if username[-1] == "s":
            """Check if the last letter of the usernae is 's', if so then don't add 's' after
            apostrophe"""
            self.permission_gb.setTitle(f"{username}' permissions")
        else:
            self.permission_gb.setTitle(f"{username}'s permissions")

        query.exec_(
            f"""SELECT * FROM user_permissions WHERE user_name='{username}'""")
        self.username_label.setText(username)

        index = 1
        while query.next():
            for permission in permissions:
                if query.value(index) == 1:
                    permission.setChecked(True)
                else:
                    permission.setChecked(False)
                index += 1
        self.username_le_2.clear()
        self.give_permissions_btn.setEnabled(True)
        self.load_permissions_btn.setEnabled(False)

    def giveUserPermissions(self):
        username = self.username_label.text()
        permissions = self.tab_permissions.children() + self.other_permissions.children()
        self.permission_gb.setTitle(f"User Permissions")
        query.prepare(
            "INSERT INTO user_permissions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)")
        query.addBindValue(username)

        for permission in permissions:
            if permission.isChecked():
                query.addBindValue(1)
            else:
                query.addBindValue(0)
            permission.setChecked(False)
        query.exec_()
        query.exec_(
            f"""INSERT INTO history(user_name, [action], [table]) VALUES('{self.username}', 'EDITED "{username}" permissions.', 'user_permissions')""")
        self.history_table_model.submitAll()
        self.username_label.clear()
        self.give_permissions_btn.setEnabled(False)
        QMessageBox.information(
            self, 'Operation Successful',
            "Permissions applied successfully.\n\nChanges will take effect on user's next login.")

    def showPassword(self, state):
        if state == Qt.Checked:
            self.password_le.setEchoMode(QLineEdit.Normal)
            self.password_le_2.setEchoMode(QLineEdit.Normal)
        else:
            self.password_le.setEchoMode(QLineEdit.Password)
            self.password_le_2.setEchoMode(QLineEdit.Password)

    def showUsers(self):
        self.users_table_model = QSqlTableModel()
        self.users_table_model.setTable('users')
        self.users_tv.setModel(self.users_table_model)
        self.users_tv.horizontalHeader(
        ).setSectionResizeMode(QHeaderView.Stretch)
        self.users_table_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.users_table_model.select()
        self.users_tv.hideColumn(0)
        self.users_tv.hideColumn(3)

    def createUser(self):
        name = self.formatText(self.fname_le_3.text()) + \
            " " + self.formatText(self.lname_le_3.text())
        username = self.username_le.text()
        password = self.password_le.text()

        hashed_user_password = str(hashPassword(password))
        query.prepare(
            'INSERT INTO users(user_name, name, user_password) VALUES(?, ?, ?)')
        query.addBindValue(username)
        query.addBindValue(name)
        query.addBindValue(hashed_user_password)
        query.exec_()
        self.users_table_model.submitAll()
        query.exec_(
            f"""INSERT INTO history(user_name, [action], [table]) VALUES('{self.username}', 'ADDED "{name}, {username}."', 'users')""")
        query.exec_(
            f"INSERT INTO user_permissions VALUES('{username}',1,1,1,1,0,1,0,1,1,0,1,1,1,0,0,0)")
        query.exec_(
            f"""INSERT INTO history(user_name, [action], [table]) VALUES('{self.username}', 'GAVE "{username} Standard permissions."', 'user_permissions')""")
        self.usernames.append(username)
        self.history_table_model.submitAll()
        self.fname_le_3.clear()
        self.lname_le_3.clear()
        self.username_le.clear()
        self.password_le.clear()
        self.password_le_2.clear()
        self.username_taken_le.clear()

    def userSelected(self):
        row = self.users_tv.currentIndex().row()
        username = self.users_tv.currentIndex().sibling(row, 1).data()
        self.username_label.setText(username)
        self.delete_user_btn.setEnabled(True)

    def deleteUser(self):
        username = self.username_label.text()
        response = QMessageBox.warning(
            self, 'Delete User', f'Are you sure you want to delete "{username}?\n\nThis cannot be undone."',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

        if response == QMessageBox.Yes:
            query.exec_(f"DELETE FROM users WHERE user_name='{username}'")
            self.users_table_model.submitAll()
            query.exec_(
                f"""INSERT INTO history(user_name, [action], [table]) VALUES('{self.username}', 'DELETED "{username}."', 'users')""")
            query.exec_(
                f"DELETE FROM user_permissions WHERE user_name='{username}'")
            query.exec_(
                f"""INSERT INTO history(user_name, [action], [table]) VALUES('{self.username}', 'REMOVED "{username} permissions."', 'user_permissions')""")
            self.usernames.remove(username)
            self.history_table_model.submitAll()
            self.username_label.clear()
            self.delete_user_btn.setEnabled(False)
            QMessageBox.information(
                self, 'Operation Successful', 'Deleted user successfully.', QMessageBox.Ok, QMessageBox.Ok)

    def usernameConfirm(self):
        username = self.username_le.text().strip()

        if not username:
            self.username_taken_le.setText(f'"NO VALID INPUT GIVEN"')
            self.create_user_btn.setEnabled(False)
        elif username in self.usernames:
            self.username_taken_le.setText(f'"{username}" is already taken.')
            self.create_user_btn.setEnabled(False)
        else:
            self.username_taken_le.clear()
            self.confirmCreateUser()

    def confirmPassword(self):
        password1 = self.password_le.text()
        password2 = self.password_le_2.text()

        if not password1 and not password2:
            self.conf_password_info_le.setText("NO INPUT GIVEN")
            self.create_user_btn.setEnabled(False)

        elif password1 == password2:
            self.conf_password_info_le.setText("Passwords match!")
            self.confirmCreateUser()

        else:
            self.conf_password_info_le.setText("Passwords do not match!")
            self.create_user_btn.setEnabled(False)

    def confirmCreateUser(self):
        username = self.username_le.text().strip()
        password1 = self.password_le.text()
        password2 = self.password_le_2.text()

        if username and password1 and password2 and username not in self.usernames and password1 == password2:
            self.create_user_btn.setEnabled(True)

    def open_dashboard_tab(self):
        self.main_tab_widget.setCurrentIndex(0)

    def open_books_tab(self):
        self.main_tab_widget.setCurrentIndex(1)

    def open_issue_book_tab(self):
        self.main_tab_widget.setCurrentIndex(2)

    def open_report_tab(self):
        self.main_tab_widget.setCurrentIndex(3)

    def open_history_tab(self):
        self.main_tab_widget.setCurrentIndex(4)

    def open_settings_tab(self):
        self.main_tab_widget.setCurrentIndex(5)

    def open_users_tab(self):
        self.main_tab_widget.setCurrentIndex(6)

    def showBookSearchResults(self, data):
        self.edit = data
        self.edit_info_label.setText(f'"{data[0][1]}" found!')
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
                row = [query.value(0), query.value(
                    1), query.value(2), query.value(3)]
                data.append(tuple(row))

            if not data:
                query.exec_(
                    f"SELECT * FROM books WHERE book_title = '{book_title}'")
                while query.next():
                    row = [query.value(0), query.value(
                        1), query.value(2), query.value(3)]
                    data.append(tuple(row))

                if not data:
                    QMessageBox.information(
                        self, 'Not Found', f'"{book_title}" not found.', QMessageBox.Ok, QMessageBox.Ok)
                    self.edit_info_label.clear()
                    self.edit_extra_label.clear()
                    self.clear_book_entry(
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
                f"INSERT INTO books(book_title, category, quantity) VALUES('{book_title}', '{category}', {quantity})")

            self.book_table_model.submitAll()
            self.booksTableSort()
            if query.lastError().isValid():
                QMessageBox.information(
                    self, 'Book exists', f'"{book_title}" already exists in "{category}" category', QMessageBox.Ok,
                    QMessageBox.Ok)

            else:
                query.exec_(
                    f"""INSERT INTO history(user_name, [action], [table]) VALUES('{self.username}', 'ADDED "{book_title}, {category}, {quantity}"', 'books')""")
                self.history_table_model.submitAll()
                if res != 'exists':
                    QMessageBox.information(
                        self, 'Operation Successful',
                        f'"{book_title}" and "{category}" category were successfully added!',
                        QMessageBox.Ok, QMessageBox.Ok)
                else:
                    QMessageBox.information(
                        self, 'Operation Successful', f'"{book_title}" was successfully added!', QMessageBox.Ok,
                        QMessageBox.Ok)
            self.clear_book_entry(
                self.book_title_le, self.category_combo_box, self.quantity_spin_box)

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
                query.exec_(
                    f"""INSERT INTO history(user_name, [action], [table]) VALUES('{self.username}', 'DELETED "{book_title}, {category}"', 'books')""")
                self.history_table_model.submitAll()
                self.clear_book_entry(
                    self.book_title_le_2, self.category_combo_box_2, self.quantity_spin_box_2)
                self.edit = []
                self.updateCategoryList([(None, book_title, None, None)])
                self.book_table_model.submitAll()
                self.booksTableSort()
        if found == 'Try different category':
            QMessageBox.information(
                self, 'Book Not found', f'"{book_title}" is not in "{category}" category.\n\nTry different category.',
                QMessageBox.Ok, QMessageBox.Ok)

    def editBook(self, book_title, category, quantity):
        def completeBookEdit(book_title, category, quantity):

            query.exec_(
                f"UPDATE books SET book_title='{book_title}', category='{category}', quantity={quantity} WHERE book_id={int(self.edit[0][0])}")
            query.exec_(
                f"""INSERT INTO history(user_name, [action], [table]) 
                VALUES('{self.username}', 'EDITED FROM "{self.edit[0][1]}, {self.edit[0][2]}, {self.edit[0][3]}" TO "{book_title}, {category}, {quantity}"', 'books')""")
            self.history_table_model.submitAll()
            QMessageBox.information(
                self, 'Changes Successful', 'Book successfully edited!', QMessageBox.Ok, QMessageBox.Ok)

            self.book_table_model.submitAll()
            self.booksTableSort()
            self.category_cb_model.submitAll()
            self.edit = []
            self.clear_book_entry(
                self.book_title_le_2, self.category_combo_box_2, self.quantity_spin_box_2)
            index = self.category_combo_box.findText("Unknown")
            self.category_combo_box.setCurrentIndex(index)
            self.category_combo_box_3.setCurrentIndex(index)
            self.edit_info_label.clear()
            self.edit_extra_label.clear()
            self.category_lw.clear()
        if not self.edit:
            QMessageBox.information(
                self, 'Search First',
                'You have not searched for book.\n\nFirst search for book in library to obtain it\'s data before you can edit it.',
                QMessageBox.Ok, QMessageBox.Ok)
        elif self.edit == [(int(self.edit[0][0]), book_title, category, quantity)]:
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
                    completeBookEdit(book_title, category, quantity)
            else:
                completeBookEdit(book_title, category, quantity)

    def addClient(self, fname, lname, class_, house):
        if fname == "" or lname == "" or class_ == "" or house == "":
            QMessageBox.information(
                self, 'Invalid', 'Fill out all entries.', QMessageBox.Ok, QMessageBox.Ok)

        else:
            name = fname + ' ' + lname
            query.exec_(
                f"""INSERT INTO clients(client_name, client_class, client_house) VALUES('{name}', '{class_}', '{house}')""")

            if query.lastError().isValid() is False:
                query.exec_(
                    f"""INSERT INTO history(user_name, [action], [table]) VALUES('{self.username}', 'ADDED "{name}, {class_}, {house}"', 'clients')""")
                self.history_table_model.submitAll()

            query.exec_(
                f"""SELECT client_id FROM clients WHERE client_name = '{name}' AND client_class = '{class_}' AND client_house = '{house}'""")

            while query.next():
                client_id = query.value(0)
                return client_id

    def retrieveBook(self, book, quantity):
        if book == "":
            QMessageBox.information(self, 'Book Not Selected',
                                    'You have not selected a book to retrieve.\nFirst search for student, then select a book to retrieve.',
                                    QMessageBox.Ok, QMessageBox.Ok)
        else:
            client_name, client_class, client_house = self.client_info_label.text().split('\t')
            book_title, category = book.split(' | ')
            book_title = book_title.strip('"')
            category = category.strip('"')
            query.exec_(
                f"""SELECT client_id FROM clients WHERE client_name='{client_name}' AND client_class='{client_class}' AND client_house='{client_house}'""")

            while query.next():
                client_id = query.value(0)

            query.exec_(
                f"""SELECT book_id FROM books WHERE book_title='{book_title}' AND category='{category}'""")

            while query.next():
                book_id = query.value(0)

            query.exec_(
                f"""UPDATE client_records SET quantity=quantity-{quantity}, 
                    returned=(case when quantity-{quantity}=0 then TRUE else FALSE END) 
                    WHERE client_id={client_id} AND book_id={book_id}""")

            if self.today_transac_count > 0:
                query.exec_(
                    f"""INSERT INTO transactions(client_id, book_id, quantity, type, user_id)
                    VALUES({client_id}, {book_id}, {quantity}, 'RETRIEVE', {self.user_id})""")
                self.today_transac_count += 1

            else:
                # If no transaction have been performed today, perform transaction and an obligatory zero quantity transaction of day
                query.exec_(
                    f"""INSERT INTO transactions(client_id, book_id, quantity, type, user_id)
                    VALUES({client_id}, {book_id}, {quantity}, 'RETRIEVE', {self.user_id})""")
                query.exec_(
                    f"""INSERT INTO transactions(type, user_id)
                    VALUES('LEND', {self.user_id})""")  # Zero quantity transaction of day
                self.today_transac_count += 1  # Increase transaction count, exclusive of zero quantity transaction of day

            query.exec_(
                f"""UPDATE books SET quantity=quantity+{quantity} WHERE book_id={book_id}""")

            self.increase_dash_val(self.retrieved_today_val, quantity)
            self.increase_dash_val(self.total_retrieved_val, quantity)
            self.decrease_dash_val(self.outstanding_val, quantity)
            self.book_table_model.submitAll()
            self.book_title_category_label.clear()
            self.quantity_spin_box_4.setValue(0)
            self.client_record_table_model.setQuery(
                QSqlQuery(f"""SELECT BOOK_TITLE, CATEGORY, OWING_QUANTITY, RETURNED FROM client_record_vw 
                                    WHERE client_name='{client_name}' 
                                    AND client_class='{client_class}' 
                                    AND client_house='{client_house}'
                                    AND RETURNED=FALSE"""))

    def lendBook(self, book_title, category, quantity):
        def completeLendBook(book_id, quantity):
            client_id = self.addClient(self.formatText(self.fname_le.text()), self.formatText(self.lname_le.text()),
                                       self.class_combo_box.currentText(
            ), self.house_combo_box.currentText())

            if client_id:
                query.exec_(
                    f"""INSERT INTO client_records(client_id, book_id, quantity, returned) VALUES({client_id}, {book_id}, {quantity}, FALSE)""")

                if query.lastError().isValid():
                    query.exec_(
                        f"""UPDATE client_records SET quantity=quantity+{quantity}, returned=FALSE WHERE client_id={client_id} AND book_id={book_id}""")

                if self.today_transac_count > 0:
                    query.exec_(
                        f"""INSERT INTO transactions(client_id, book_id, quantity, type, user_id) 
                        VALUES({client_id}, {book_id}, {quantity}, 'LEND', {self.user_id})""")
                    self.today_transac_count += 1

                else:
                    # If no transaction have been performed today, perform transaction and an obligatory zero quantity transaction of day
                    query.exec_(
                        f"""INSERT INTO transactions(client_id, book_id, quantity, type, user_id) 
                        VALUES({client_id}, {book_id}, {quantity}, 'LEND', {self.user_id})""")
                    query.exec_(
                        f"""INSERT INTO transactions(type, user_id) 
                            VALUES('RETRIEVE', {self.user_id})""")  # Zero quantity transaction of day
                    self.today_transac_count += 1  # Increase transaction count, exclusive of zero quantity transaction of day

                query.exec_(
                    f"""UPDATE books SET quantity=quantity-{quantity} WHERE book_id={book_id}""")
                self.increase_dash_val(self.lent_today_val,quantity)
                self.increase_dash_val(self.total_lent_val,quantity)
                self.increase_dash_val(self.outstanding_val,quantity)
                self.book_table_model.submitAll()
                self.booksTableSort()
                self.clear_book_entry(
                    self.book_title_le_3, self.category_combo_box_3, self.quantity_spin_box_3)
                self.clear_client_entry(
                    self.fname_le, self.lname_le, self.class_combo_box, self.house_combo_box)
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
                    quantity = int(data['quantity'])
                    completeLendBook(int(data['book_id']), quantity)

            else:
                completeLendBook(data['book_id'], quantity)

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

            if query.lastError().isValid():
                if label is not None:
                    label.setText(
                        f'"{category}" category already exists in library.')
                return 'exists'
            else:
                query.exec_(
                    f"""INSERT INTO history(user_name, [action], [table]) VALUES('{self.username}', 'ADDED "{category}"', 'categories')""")
                self.history_table_model.submitAll()

            if label is not None:
                label.setText(
                    f'"{category}" category successfully added to library.')
                self.add_category_le.clear()

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
    screen_width = QDesktopWidget().screenGeometry().width()
    screen_height = QDesktopWidget().screenGeometry().height()
    style = open('themes/dark.css', 'r')
    style = style.read()
    app.setStyleSheet(style)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())
