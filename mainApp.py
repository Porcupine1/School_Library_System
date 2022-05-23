from datetime import datetime
import hashlib
import hmac
import os
import sys
from ast import literal_eval

from PyQt5 import uic
from PyQt5.QtChart import (QChart,
                           QChartView, QDateTimeAxis, QLineSeries, QValueAxis)
from PyQt5.QtCore import QDate, QDateTime, QPoint, Qt, QRegularExpression
from PyQt5.QtGui import QEnterEvent, QPainter, QPixmap, QIcon, QColor
from PyQt5.QtSql import (QSqlDatabase, QSqlQuery, QSqlRelation,
                         QSqlRelationalTableModel, QSqlTableModel, QSqlQueryModel)
from PyQt5.QtWidgets import (QApplication, QButtonGroup, QDesktopWidget,
                             QHeaderView, QLabel, QLineEdit, QMainWindow,
                             QMessageBox, QPushButton, QWidget, QCompleter, QCheckBox,
                             QTreeWidgetItemIterator, QTreeWidgetItem, QGraphicsDropShadowEffect, 
                             QFrame, QSpinBox, QComboBox)
from threading import Timer

from queries import *


basedir = os.path.dirname(__file__)

try:
    from ctypes import windll  # Only exists on Windows.
    myappid = 'thomasjournals.Library.1.0'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


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

    # Create database tables if they don't exist
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
    query.exec_(create_classes_table_query)
    query.exec_(create_houses_table_query)

    # check for classes in classes table
    query.exec_('SELECT COUNT(*) FROM classes')
    # if no class in classes table, insert default ones from classes.txt
    if query.next() and query.value(0) == 0:
        with open('classes.txt') as fh:
            classes = fh.readlines()
            for class_ in classes:
                # removes \n at the end of each class
                class_ = class_.strip('\n')
                query.exec_(f'INSERT INTO classes VALUES("{class_}")')

    # check for houses in houses table
    query.exec_('SELECT COUNT(*) FROM houses')
    # if no house in houses table, insert default ones from houses.txt
    if query.next() and query.value(0) == 0:
        with open('houses.txt') as fh:
            houses = fh.readlines()
            for house in houses:
                # removes \n at the end of each house
                house = house.strip('\n')
                query.exec_(f'INSERT INTO houses VALUES("{house}")')

    # Creates default category, 'Unknown'.
    query.exec_("INSERT INTO categories VALUES('Unknown')")

    # check if any user exits
    query.exec_("SELECT COUNT(*) FROM users")
    # if no user exists, create admin user
    if query.next():
        hashed_user_password = str(hashPassword('admin'))
        query.prepare(
            'INSERT INTO users(user_name, user_password) VALUES(?, ?)')
        query.addBindValue('admin')
        query.addBindValue(hashed_user_password)
        query.exec_()

        query.exec_(
            "SELECT user_name FROM user_permissions WHERE user_name='admin'")
        if not query.next():
            query.exec_(
                "INSERT INTO user_permissions VALUES('admin',2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2)")


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
    """closes program
    """
    self.close()


def btn_max_clicked(self):
    """Maximizes or restores down window
    """
    # if window is maximized, restore down
    if self.isMaximized():
        self.max_btn.setIcon(QIcon(QPixmap(os.path.join(basedir, "icons/maximize.png"))))
        self.showNormal()
        self.title_bar_2.resize(self.widget_2.width(), 40)
        self.title_bar.move(self.title_bar_pos, 0)

    # if window is restored down, maximize it
    else:
        QPushButton().setIcon(QIcon())
        self.title_bar.move(screen_width - 283, 0)
        self.title_bar_2.resize(screen_width - 178, 40)
        self.max_btn.setIcon(QIcon(QPixmap(os.path.join(basedir, "icons/restore_down.png"))))
        self.showMaximized()


def btn_min_clicked(self):
    """Minimizes window
    """
    self.showMinimized()


def centerWindow(self):
    """Centres window on the screen
    """
    self.move((screen_width - self.width()) // 2,
              (screen_height - self.height()) // 2)


login, _ = uic.loadUiType('login.ui')
main, _ = uic.loadUiType('main.ui')


class LoginWindow(QWidget, login):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self.setWindowTitle('Library login')
        centerWindow(self)
        initializeDatabase()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.close_btn.clicked.connect(lambda: btn_close_clicked(self))
        self.min_btn.clicked.connect(lambda: btn_min_clicked(self))
        self.login_btn.clicked.connect(self.handleLogin)
        self.show_password_cb.stateChanged.connect(self.showPassword)
        self.label.setVisible(False)
        for child in self.widget.findChildren((QLineEdit, QPushButton)):
            shadow = QGraphicsDropShadowEffect(
                blurRadius=10, xOffset=0, yOffset=4, color=QColor('black'))
            child.setGraphicsEffect(shadow)

    def showPassword(self, state):
        """Hides when the check box is unchecked and shows password when it is checked
        """
        # if check box is checked
        if state == Qt.Checked:
            self.password_le.setEchoMode(QLineEdit.Normal)

        # unchecked
        else:
            self.password_le.setEchoMode(QLineEdit.Password)

    def handleLogin(self):
        """Checks for the user in the database the checks if the entered password is correct.
        If the username does not exist or password is incorrect, a response is displayed.
        If both username and password are correct, login window is closed and main window opens(Logged in)."""

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
            # if passwords match
            if password_check(password, literal_eval(data[1])):
                self.username_le.clear()
                self.show_password_cb.setChecked(False)
                self.label.setVisible(False)
                self.main_window = MainApp(data[0], username)
                self.close()  # close login window
                self.main_window.show()  # show main window
                query.exec_(
                    f"""INSERT INTO history(user_name, [action]) VALUES('{username}', 'LOGGED IN')""")
            else:
                self.label.setVisible(True)  # show error message
                self.label.adjustSize()

        # When entered username does not exist
        except IndexError:
            self.label.setVisible(True)  # show error message
            self.label.adjustSize()


class MainApp(QMainWindow, main):

    def __init__(self, user_id, username):
        QWidget.__init__(self)
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle('Library')
        self.user_id = user_id
        self.username = username
        self.searched_user = None
        self.handleUi()
        self.initDashVals()
        self.widget_2.installEventFilter(self)
        self.main_tab_widget.installEventFilter(self)
        self.main_tabs.installEventFilter(self)
        self.handleButtons()
        self._initDrag()
        self.setMouseTracking(True)
        self.edit_book_data = []  # Contains record of book to be edited
        query.exec_(f"SELECT user_name FROM users")
        self.usernames = []  # List of existing user names
        while query.next():
            self.usernames.append(query.value(0))

        query.exec_(
            f"SELECT count(*) FROM transactions WHERE user_id={self.user_id} AND DATE(datetime)='{datetime.today().date()}'")
        if query.next():
            # Number of transactions performed today
            self.today_transac_count = query.value(0)

        self.book_title_model = QSqlQueryModel()
        self.book_title_model.setQuery(
            "SELECT DISTINCT book_title FROM books")  # all book titles

        # auto completes book title entires
        self.book_title_completer = QCompleter()
        self.book_title_completer.setModel(self.book_title_model)
        self.book_title_completer.setCaseSensitivity(
            Qt.CaseInsensitive)  # makes title entries case insensitive
        # searches by checking if entry is contained in any title
        self.book_title_completer.setFilterMode(Qt.MatchFlag.MatchContains)

        self.book_title_le_2.setCompleter(self.book_title_completer)
        self.book_title_le_3.setCompleter(self.book_title_completer)
        # book title auto completion end

        self.first_name_model = QSqlQueryModel()
        self.first_name_model.setQuery(
            "SELECT DISTINCT client_first_name FROM clients")  # client first names

        # auto completes first entires
        self.first_name_completer = QCompleter()
        self.first_name_completer.setModel(self.first_name_model)
        self.first_name_completer.setCaseSensitivity(
            Qt.CaseInsensitive)  # makes title entries case insensitive

        self.fname_le.setCompleter(self.first_name_completer)
        self.fname_le_2.setCompleter(self.first_name_completer)

        self.last_name_model = QSqlQueryModel()
        self.last_name_model.setQuery(
            "SELECT DISTINCT client_last_name FROM clients")  # all client last names

        # auto completes first entires
        self.last_name_completer = QCompleter()
        self.last_name_completer.setModel(self.last_name_model)
        self.last_name_completer.setCaseSensitivity(
            Qt.CaseInsensitive)  # makes title entries case insensitive

        self.lname_le.setCompleter(self.last_name_completer)
        self.lname_le_2.setCompleter(self.last_name_completer)

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
        # There is no definition of the left and top five directions, mainly because the implementation is not difficult, but the effect is very poor.
        # When dragging and dropping, the window flickers, and then study whether there is a better implementation
        if Qt.LeftButton and self._right_drag:
            # Right adjust window width
            self.resize(QMouseEvent.pos().x(), self.height())
            self.title_bar_2.resize(self.widget_2.width(), 40)
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

        self.handlePermissions()
        self.username_label_3.setText(self.username)
        centerWindow(self)
        #make dashboard tab default current tab
        self.dashboard_btn.setProperty('class', 'current_tab_btn')
        self.dashboard_btn.style().unpolish(self.dashboard_btn)
        self.dashboard_btn.style().polish(self.dashboard_btn)
        self.dashboard_btn.update()
        self.title_bar_pos = 917
        self.setMaximumSize(screen_width, screen_height)
        self.setupHouseComboBox()
        self.setupClassComboBox()
        self.class_combo_box.setCurrentIndex(-1)
        self.house_combo_box.setCurrentIndex(-1)
        self.class_combo_box_2.setCurrentIndex(-1)
        self.house_combo_box_2.setCurrentIndex(-1)
        self.delete_class_cb.setCurrentIndex(-1)
        self.current_class_name_cb.setCurrentIndex(-1)
        self.delete_house_cb.setCurrentIndex(-1)
        self.current_house_name_cb.setCurrentIndex(-1)
        self.main_tab_widget.tabBar().setVisible(False)
        self.setupCategoryComboBox()
        self.setupBooksTableView()
        self.setupClientRecordView()
        self.setupAllClientRecordsView()
        self.showUsers()
        self.showHistory()
        self.plotTransactionGraph()
        self.setupTransactionsTableView()
        self.change_username_le.setPlaceholderText(self.username)
        self.current_tab_btn = self.dashboard_btn

        # add shadows to all LineEdits, SpinBoxes and ComboBoxes
        for child in self.main_tab_widget.findChildren((QPushButton, QLineEdit, QSpinBox, QComboBox)):
            shadow = QGraphicsDropShadowEffect(
                blurRadius=10, xOffset=0, yOffset=4, color=QColor('black'))
            child.setGraphicsEffect(shadow)
        self.category_combo_box.lineEdit().setGraphicsEffect(None)

        # add shadows to dashboard holders (frames)
        for child in self.dashboard_tab.findChildren(QFrame, QRegularExpression('frame')):
            shadow = QGraphicsDropShadowEffect(
                blurRadius=15, xOffset=0, yOffset=5, color=QColor('black'))
            child.setGraphicsEffect(shadow)

        # add shadows to dashboard holders' (frames) children
        for child in self.dashboard_tab.findChildren(QLabel):
            shadow = QGraphicsDropShadowEffect(
                blurRadius=5, xOffset=0, yOffset=2, color=QColor('black'))
            child.setGraphicsEffect(shadow)

        # add shadow the main tab widget
        self.main_tab_widget.setGraphicsEffect(QGraphicsDropShadowEffect(
            blurRadius=30, xOffset=0, yOffset=10, color=QColor('black')))

        # add shadows to main tab buttons
        for child in self.main_tabs.findChildren(QPushButton):
            shadow = QGraphicsDropShadowEffect(
                blurRadius=15, xOffset=0, yOffset=4, color=QColor('black'))
            child.setGraphicsEffect(shadow)

        # permissions tree
        # get alltable column names (permissions)
        query.exec_("SELECT name FROM PRAGMA_TABLE_INFO('user_permissions')")
        permissions = []
        while query.next():
            permissions.append(query.value(0))

        dic_permissions = {}
        # start from second index, the first is not a permission
        for permission in permissions[1:]:
            try:
                """child permission names start with parent permission name.
                They are slipt by '__' """
                parent, child = permission.split('__')
                dic_permissions[parent].append(child)
            except ValueError:
                # parent permission only
                dic_permissions[permission] = []

        for parent_text, children_text in dic_permissions.items():
            parent = QTreeWidgetItem(self.permissions_tree_widget)
            parent.setText(0, parent_text.replace('_', ' ').title())

            # if permission has no children
            if len(children_text) == 0:
                parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
                parent.setCheckState(0, Qt.Unchecked)
            # if permission has children, give tristate
            else:
                parent.setFlags(parent.flags() |
                                Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            # remove the last four characters (_tab)
            parent.setIcon(
                0, QIcon(QPixmap(os.path.join(basedir, f"icons/{parent_text[:-4]}.png"))))
            for child_text in children_text:
                child = QTreeWidgetItem(parent)
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setText(0, child_text.replace('_', ' ').title())
                child.setCheckState(0, Qt.Unchecked)
                
        #Table header shadow
        table_headers = self.findChildren(QHeaderView)
        for header in table_headers:
            shadow = QGraphicsDropShadowEffect(
                blurRadius=15, xOffset=0, yOffset=5, color=QColor('black'))
            header.setGraphicsEffect(shadow)

    def handlePermissions(self):
        """Checks user's permissions to appropriately to alter what is accessible by the user.
        """

        permission_affectees = [(self.dashboard_btn, self.dashboard_tab), (self.books_btn, self.books_tab), self.add_book_tab,
                                self.edit_book_btn, self.delete_book_btn, self.add_category_btn, (self.issue_book_btn, self.issue_book_tab),
                                self.lend_book_tab, self.retrieve_book_btn, (self.report_btn, self.report_tab), (self.history_btn, self.history_tab),
                                self.users_history_tab, self.transactions_history_tab, (self.settings_btn, self.settings_tab), 
                                (self.add_class_btn, self.add_class_le, self.add_class_label), (self.delete_class_btn, self.delete_class_cb, self.deleted_class_label),
                                (self.change_class_name_btn, (self.new_class_name, self.current_class_name_cb), self.change_class_name_label),
                                (self.add_house_btn, self.add_house_le, self.add_house_label), (self.delete_house_btn, self.delete_house_cb, self.delete_house_label),
                                (self.change_house_name_btn, (self.new_house_name, self.current_house_name_cb), self.change_house_labe), (self.users_btn, self.users_tab),
                                self.create_user_tab, self.delete_user_btn, self.permissions_tab]

        query.exec_(
            f"SELECT * FROM user_permissions WHERE user_name='{self.username}'")
        index = 1
        while query.next():
            for i, permission_affectee in enumerate(permission_affectees):
                if i in (0, 1, 2, 5, 6, 7, 9, 10, 11, 12, 13, 20, 21, 22):
                    if query.value(index) not in (2, 1):
                        try:
                            permission_affectee.deleteLater()
                        except:
                            permission_affectee[0].deleteLater()
                            permission_affectee[1].deleteLater()

                else:
                    if query.value(index) not in (2, 1):
                        try:
                            permission_affectee.setEnabled(False)
                        except:
                            label_index = len(permission_affectee) - 1 #last element is a label, this stores the index
                            for index_, widget in enumerate(permission_affectee):
                                if index_ == label_index:
                                    widget.setStyleSheet("color: grey") #change color of label
                                else:
                                    #when a tuple is encountered
                                    try:
                                        widget.setEnabled(False)
                                        #if widget is a line edit
                                        if isinstance(widget, QLineEdit) or isinstance(widget, QComboBox):
                                            widget.setStyleSheet("background-color: grey; border-color: grey")
                                            
                                    except:
                                        for each in widget:
                                            each.setEnabled(False)
                                            each.setStyleSheet("background-color: grey; border-color: grey")

                index += 1

    def initDashVals(self):
        """Displays the number of total books lent and retrieved all times and current
        date, as well as the unretrieved books and number od users.
        """
        query.exec_("SELECT sum(quantity) FROM transactions WHERE type='LEND'")
        if query.next():
            total_lent = query.value(0)
            if total_lent == '':
                total_lent = 0

        query.exec_(
            "SELECT sum(quantity) FROM transactions WHERE type='RETRIEVE'")
        if query.next():
            total_retrieved = query.value(0)
            if total_retrieved == '':
                total_retrieved = 0

        query.exec_(
            "SELECT sum(quantity) FROM transactions WHERE type='LEND' AND date(datetime) = date('now', 'localtime')")
        if query.next():
            lent_today = query.value(0)
            if lent_today == '':
                lent_today = 0

        query.exec_(
            "SELECT sum(quantity) FROM transactions WHERE type='RETRIEVE' AND date(datetime) = date('now', 'localtime')")
        if query.next():
            retrieved_today = query.value(0)
            if retrieved_today == '':
                retrieved_today = 0

        query.exec_("SELECT count(*) FROM users")
        if query.next():
            users_val = query.value(0)
            if users_val == '':
                users_val = 0

        self.total_lent_val.setText(str(total_lent))
        self.total_retrieved_val.setText(str(total_retrieved))
        self.lent_today_val.setText(str(lent_today))
        self.retrieved_today_val.setText(str(retrieved_today))
        self.unretrieved_val.setText(str(total_lent - total_retrieved))
        self.users_val.setText(str(users_val))

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
        """Loads categories from category table as items in the combo-box
        """
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

    def setupClassComboBox(self):
        """Loads houses from houses table as items in the combo-box
        """
        self.classes_cb_model = QSqlTableModel()
        self.classes_cb_model.setTable('classes')
        self.classes_cb_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        column = self.classes_cb_model.fieldIndex('class')
        self.classes_cb_model.setSort(column, Qt.AscendingOrder)
        self.classes_cb_model.select()
        self.class_combo_box.setModel(self.classes_cb_model)
        self.class_combo_box_2.setModel(self.classes_cb_model)
        self.delete_class_cb.setModel(self.classes_cb_model)
        self.current_class_name_cb.setModel(self.classes_cb_model)
        
    def updateClassComboBoxes(self):
        """submits manual changes and set combobox current index to -1
        """
        self.classes_cb_model.submitAll()
        self.class_combo_box.setCurrentIndex(-1)
        self.class_combo_box_2.setCurrentIndex(-1)
        self.delete_class_cb.setCurrentIndex(-1)
        self.current_class_name_cb.setCurrentIndex(-1)

    def setupHouseComboBox(self):
        """Loads houses from houses table as items in the combo-box
        """
        self.houses_cb_model = QSqlTableModel()
        self.houses_cb_model.setTable('houses')
        self.houses_cb_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        column = self.houses_cb_model.fieldIndex('house')
        self.houses_cb_model.setSort(column, Qt.AscendingOrder)
        self.houses_cb_model.select()
        self.house_combo_box.setModel(self.houses_cb_model)
        self.house_combo_box_2.setModel(self.houses_cb_model)
        self.delete_house_cb.setModel(self.houses_cb_model)
        self.current_house_name_cb.setModel(self.houses_cb_model)
        
    def updateHouseComboBoxes(self):
        """submits manual changes and set combobox current index to -1
        """
        self.houses_cb_model.submitAll()
        self.house_combo_box.setCurrentIndex(-1)
        self.house_combo_box_2.setCurrentIndex(-1)
        self.delete_house_cb.setCurrentIndex(-1)
        self.current_house_name_cb.setCurrentIndex(-1)

    def booksTableSort(self):
        """
        Sorts the book table data first by category then book title
        """
        self.book_table_model.setQuery(
            QSqlQuery("SELECT * FROM books ORDER BY category, book_title"))

    def setupBooksTableView(self):
        """Loads and displays all books from books table, and sorts them first according to category the book-title
        """

        self.book_table_model = QSqlRelationalTableModel()
        self.book_table_model.setTable('books')
        self.book_table_model.setRelation(self.book_table_model.fieldIndex('category'), QSqlRelation(
            'categories', 'category', 'category'))
        self.all_books_table_view.setModel(self.book_table_model)
        self.all_books_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.all_books_table_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.book_table_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.all_books_table_view.hideColumn(0)
        self.booksTableSort()

    def setTransactionTableQuery(self):
        """set the transaction table model query
        """
        self.transactions_table_model.setQuery(QSqlQuery('''SELECT
                                                    coalesce(name, 'USER ID '||users.user_id) AS user,
                                                    book_title || ', ' || category AS book,
                                                    transactions.type, 
                                                    transactions.quantity,
                                                    client_first_name || ' ' || client_last_name AS client,
                                                    datetime
                                                    from transactions INNER JOIN clients ON transactions.client_id == clients.client_id
                                                    INNER JOIN books ON books.book_id == transactions.book_id
                                                    INNER JOIN users ON users.user_id == transactions.user_id'''))

    def setupTransactionsTableView(self):
        """Creates a table with all user transactions
        """
        self.transactions_table_model = QSqlTableModel()
        self.transactions_table_view.setModel(self.transactions_table_model)
        self.setTransactionTableQuery()
        self.transactions_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.transactions_table_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.transactions_table_model.setEditStrategy(
            QSqlTableModel.OnManualSubmit)

    def setupClientRecordView(self):
        """Creates table to load books a client has not returned."""
        self.client_record_table_model = QSqlTableModel()
        self.client_record_table_model.setTable('client_record_vw')
        self.client_record_tv.setModel(self.client_record_table_model)
        self.client_record_tv.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.client_record_tv.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        for column_hidden in (0, 1, 2, 3):
            self.client_record_tv.hideColumn(column_hidden)
            
    def setupAllClientRecordsView(self):
        """Creates table to load clients' records."""
        self.clients_records_table_model = QSqlTableModel()
        self.clients_records_table_model.setTable('client_record_vw')
        self.client_record_tv_2.setModel(self.clients_records_table_model)
        self.client_record_tv_2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.client_record_tv_2.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.clients_records_table_model.setQuery(QSqlQuery('SELECT * FROM client_record_vw WHERE returned=0'))
        self.client_record_tv_2.hideColumn(7)
        
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
        self.history_tv.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_tv.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        column = self.history_table_model.fieldIndex('datetime')
        self.history_table_model.setSort(column, Qt.DescendingOrder)
        self.history_table_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.history_table_model.select()

    def setClientRecordTableQuery(self, fname, lname, class_, house):
        """ sets the client record table model query
        """
        self.client_record_table_model.setQuery(
            QSqlQuery(f"""SELECT BOOK_TITLE, CATEGORY, OWING_QUANTITY, RETURNED FROM client_record_vw 
                        WHERE first_name='{fname}'
                        AND last_name='{lname}'
                        AND class='{class_}' 
                        AND house='{house}'
                        AND RETURNED=FALSE"""))

    def showClientRecord(self, fname: str, lname: str, class_: str, house: str):
        """Loads and displays books a client has not returned
        """

        self.client_info_label.setText(
            f"{fname}\t{lname}\t{class_}\t{house}")  # Displays client information

        for column_hidden in (0, 1, 2, 3):
            self.client_record_tv.setColumnHidden(
                column_hidden, False)  # Hides unnecessary columns

        self.setClientRecordTableQuery(fname, lname, class_, house)

    @staticmethod
    def formatText(text: str) -> str:
        """Cleans user input by removing trailing whitespaces 
        and capitalizes first letter of each word

        *NOT TO BE USED ON USERNAMES AND PASSWORDS"""

        return text.strip().title()

    @staticmethod
    def clear_book_entry(title_le: QLineEdit, category_cb: QComboBox, quantity_sb: QSpinBox):
        """Gives book input fields their default values
        """
        title_le.clear()
        index = category_cb.findText("Unknown")
        category_cb.setCurrentIndex(index)
        quantity_sb.setValue(0)

    @staticmethod
    def clear_client_entry(fname_le: QLineEdit, lname_le: QLineEdit, class_cb: QComboBox, house_cb: QComboBox):
        """Gives client input fields their default values"""
        fname_le.clear()
        lname_le.clear()
        class_cb.setCurrentIndex(-1)
        house_cb.setCurrentIndex(-1)

    @staticmethod
    def changeProperty(widget, property: str, value: str):
        """Changes the value of a property of a object
        """
        widget.setProperty(property, value)
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

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

    def plotTransactionGraph(self):
        """Creates transactions graph and populates it with
        data from the loadTransactionData function.
        """
        def appendTransDataToSeries(trans_data, series):
            """Traverses over transactions' dates, sets to a DateTime format
            then adds each to the lent series.
            """

            for i in range(len(trans_data[0])):
                year, month, date_ = [int(data)
                                      for data in trans_data[0][i].split('-')]
                date = QDateTime()
                date.setDate(QDate(year, month, date_))
                series.append(date.toMSecsSinceEpoch(), trans_data[1][i])

        # Gets transactions from database by type
        lent_trans, retrieved_trans = self.loadTransactionData()
        l_series = QLineSeries()
        r_series = QLineSeries()
        l_series.setName('Lent')
        r_series.setName('Retrieved')

        appendTransDataToSeries(lent_trans, l_series)
        appendTransDataToSeries(retrieved_trans, r_series)

        self.chart = QChart()
        self.chart.addSeries(l_series)
        self.chart.addSeries(r_series)
        self.chart.setTheme(2)  # Dark Theme

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
        self.graph_layout.addWidget(self.chart_view)

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

    def confirmUsernameChange(self):
        """Changes border color of change username line edit as a response to whether the username is taken.
        *Orange means taken
        *Lime means available"""

        new_username = self.change_username_le.text().strip()

        if not new_username:
            self.change_username_le.setStyleSheet("border-color: #394453;")

        elif new_username in self.usernames:
            self.change_username_le.setStyleSheet(
                "border-color: orange;")  # set border color to red

        else:
            self.changeProperty(self.username_taken_l, "class", None)
            self.change_username_le.setStyleSheet("border-color: lime;")

    def changeUsername(self):
        """Changes username of the user currently logged in

        *changes username label text to new username

        *changes change username line edit placeholder text to new username
        """
        new_username = self.change_username_le.text().strip()
        old_username = self.username
        if new_username:
            # if inputted username is already taken
            if new_username in self.usernames:
                QMessageBox.information(
                    self, 'Error', f"""<p style='color:#2020e6; font-size: 13px;'><span style='color:#13589e'>{new_username}</span> is already taken.</p>
                                    <p>Can't change username.</p>""")
            # if inputted username is not already taken
            else:
                query.exec_(
                    f"UPDATE users SET user_name='{new_username}' WHERE user_id={self.user_id}")

                self.change_username_le.setPlaceholderText(new_username)
                self.username_label_3.setText(new_username)
                self.username = new_username
                self.usernames[self.usernames.index(
                    old_username)] = new_username
                query.exec_(
                    f"""INSERT INTO history(user_name, [action], [table]) VALUES("{old_username}", "Changed user_name to '{self.username}'", "users")""")
                self.history_table_model.submitAll()

                QMessageBox.information(
                    self, 'Changed', "<p style='color:#2020e6; font-size: 13px;'>Successfully Changed username.</p>")
        else:
            QMessageBox.warning(self, 'Error', "<p style='color:#842029; font-size: 13px;'>No valid input given.</p>")

        self.change_username_le.clear()
        self.change_username_le.setStyleSheet("border-color: #394453;")

    def confirmPasswordChange(self):
        """Changes border color of change password line edit as a response to whether both passwords match.
        *Crimson means taken
        *Lime means match"""
        password1 = self.change_password_le.text()
        password2 = self.change_password_le_2.text()

        # if not input is given in both line edits
        if not password1 and not password2:
            self.change_password_le_2.setStyleSheet("border-color: crimson;")
            self.change_password_le.setStyleSheet("border-color: #394453;")

        # if both passwords match
        elif password1 == password2:
            self.change_password_le.setStyleSheet("border-color: lime;")
            self.change_password_le_2.setStyleSheet("border-color: lime;")

        # if passwords don't match
        else:
            self.change_password_le_2.setStyleSheet("border-color: crimson;")
            self.change_password_le.setStyleSheet("border-color: #394453;")

    def changePassword(self):
        """Changes password of user currently logged in
        """
        password_1 = self.change_password_le.text()
        password_2 = self.change_password_le_2.text()

        # if no input is given in one or both password line edit
        if not password_1 or not password_2:
            QMessageBox.warning(
                self, 'Error', "<p style='color:#842029; font-size: 13px;'>No input given in one or both fields.</p>")
        # if passwords match
        elif password_1 == password_2:
            hashed_password = str(hashPassword(password_1))  # encrypt password
            query.prepare("UPDATE users SET user_password=? WHERE user_id=?")
            query.addBindValue(hashed_password)
            query.addBindValue(self.user_id)
            query.exec_()
            QMessageBox.information(
                self, 'Changed', "<p style='color:#2020e6; font-size: 13px;'>Password change successful.</p>")
            query.exec_(
                f"""INSERT INTO history(user_name, [action], [table]) VALUES('{self.username}', 'Changed password', 'users')""")
            self.history_table_model.submitAll()
            self.change_password_le.setStyleSheet("border-color: #394453;")
            self.change_password_le_2.setStyleSheet("border-color: #394453;")

        # if don't passwords match
        else:
            QMessageBox.warning(self, 'Error', "<p style='color:#842029; font-size: 13px;'>Passwords don't match!</p>")

        self.change_password_le.clear()
        self.change_password_le_2.clear()

    def addClass(self):
        """Adds class to classes table
        """
        class_name = self.add_class_le.text().strip().upper()

        # if input is given
        if class_name:
            query.exec_(f"INSERT INTO classes VALUES('{class_name}')")
            #if class already exists
            if query.lastError().isValid():
                    QMessageBox.critical(
                        self, 'Error', f"""<p style='color:crimson; font-size: 13px;'>Failed to change class name.</p>
                                            <p><span style='color:#13589e'>{class_name}</span> already exists.</p>""")
            else:
                QMessageBox.information(self, 'Added', "<p style='color:#2020e6; font-size: 13px;'>Class successfully added.</p>")
                query.exec_(
                    f"""INSERT INTO history(user_name, [action], [table]) VALUES("{self.username}", "Added '{class_name}'", "classes")""")

                self.updateClassComboBoxes()
                self.history_table_model.submitAll()
        else:
            QMessageBox.warning(self, 'Error', "<p style='color:#842029; font-size: 13px;'>No valid input given.</p>")

        self.add_class_le.clear()

    def deleteClass(self):
        """Deletes existing class that does not have a client in it that has not returned owing books
        """
        class_name = self.delete_class_cb.currentText()

        # if input is given
        if class_name:
            
            # check if any client from inputted class has not returned books
            query.exec_(
                f"SELECT FIRST_NAME, LAST_NAME, CLASS, HOUSE from client_record_vw WHERE class='{class_name}' AND returned=0")
            print(query.lastError().text())
            clients = []
            while query.next():
                    clients.append(((query.value(
                        0) + ' ' + query.value(1) + ' ' + query.value(2) + ' ' + query.value(3))))
            # if owing clients exist
            print(clients)
            if clients:
                    num_left = len(clients) - 2
                    if num_left > 0:
                        # only display two clients of many that haven't returned the book
                        QMessageBox.information(
                            self, 'Error', f"""<p style='color:#2020e6; font-size: 13px;'>The follwing clients from <span style='color:#13589e'>{class_name}</span> have unreturned books:</p>
                                                <p style='color:#13589e'>{', '.join(clients[:2])} and {num_left} more.</p>
                                                <p>Can't delete this class.</p>""")
                    elif num_left == 0:
                        # display the two clients that haven't returned the book
                        QMessageBox.information(
                            self, 'Error', f"""<p style='color:#2020e6; font-size: 13px;'>The follwing clients from <span style='color:#13589e'>{class_name}</span> have unreturned books:</p>
                                                <p style='color:#13589e'>{' and '.join(clients)}.</p>
                                                <p>Can't delete this class.</p>""")
                    else:
                        # display the client that hasn't returned the book
                        QMessageBox.information(
                            self, 'Error', f"""<p style='color:#2020e6; font-size: 13px;'>The follwing client from <span style='color:#13589e'>{class_name}</span> has unreturned books:</p>
                                                <p style='color:#13589e'>{''.join(clients)}.</p>
                                                <p>Can't delete this class.</p>""")

            # if owing clients don't exist
            else:
                query.exec_(
                    f"DELETE FROM classes WHERE class='{class_name}'")
                print('class: ', query.lastError().text())
                QMessageBox.information(
                    self, 'Deleted', "<p style='color:#2020e6; font-size: 13px;'>Class successfully deleted.</p>")
                query.exec_(
                    f"""INSERT INTO history(user_name, [action], [table]) VALUES("{self.username}", "Deleted '{class_name}'", "classes")""")

                self.updateClassComboBoxes()
                self.history_table_model.submitAll()

        else:
            QMessageBox.warning(self, 'Error', "<p style='color:#842029; font-size: 13px;'>No valid input given.</p>")

        self.delete_class_cb.setCurrentIndex(-1)

    def changeClassName(self):
        """Changes class name of existing class and updates classes of clients that belong to it to the new class name
        """
        current_class_name = self.current_class_name_cb.currentText()
        new_class_name = self.new_class_name.text().strip().upper()

        # if input fields are filled out
        if new_class_name and current_class_name:
            
            query.exec_(
                f"UPDATE classes SET class='{new_class_name}' WHERE class='{current_class_name}'")
            print(query.lastError().text())

            # if class unique constraint error(class already exists)
            if query.lastError().isValid():
                    QMessageBox.critical(
                        self, 'Error', f"""<p style='color:crimson; font-size: 13px;'>Failed to change house name.</p>
                                            <p><span style='color:#13589e'>{new_class_name}</span> already exists.</p>""")
            else:
                    # manual cascade on update
                    query.exec_(
                        f"UPDATE clients SET client_class='{new_class_name}' WHERE client_class='{current_class_name}'")
                    QMessageBox.information(
                        self, 'Changed', "<p style='color:#2020e6; font-size: 13px;'>Class name successfully changed.</p>")
                    query.exec_(
                        f"""INSERT INTO history(user_name, [action], [table]) VALUES("{self.username}", "Changed '{current_class_name}' to '{new_class_name}'", "classes")""")

                    self.updateClassComboBoxes()
                    self.history_table_model.submitAll()

        # No valid input given
        else:
            QMessageBox.warning(
                self, 'Error', "<p style='color:#842029; font-size: 13px;'>No valid input given.</p>")

        self.current_class_name_cb.setCurrentIndex(-1)
        self.new_class_name.clear()

    def addHouse(self):
        """Adds house to houses table
        """
        house_name = self.add_house_le.text().strip().upper()

        # if input is given
        if house_name:
            query.exec_(f"INSERT INTO houses VALUES('{house_name}')")
            if query.lastError().isValid():
                    QMessageBox.critical(
                        self, 'Error', f"""<p style='color:crimson; font-size: 13px;'>Failed to change house name.</p>
                                            <p><span style='color:#13589e'>{house_name}</span> already exists.</p>""")
            else:
                QMessageBox.information(self, 'Added', "<p style='color:#2020e6; font-size: 13px;'>House successfully added.</p>")
                query.exec_(
                    f"""INSERT INTO history(user_name, [action], [table]) VALUES("{self.username}", "Added '{house_name}'", "houses")""")

                self.updateHouseComboBoxes()
                self.history_table_model.submitAll()
                
        else:
            QMessageBox.warning(self, 'Error', "<p style='color:#842029; font-size: 13px;'>No valid input given.</p>")
        self.add_house_le.clear()

    def deleteHouse(self):
        """Deletes existing house that does not have a client in it that has not returned owing books
        """

        house_name = self.delete_house_cb.currentText()

        # if input is given
        if house_name:
            # check if any client from inputted house has not returned books
            query.exec_(
                f"SELECT FIRST_NAME, LAST_NAME, CLASS, HOUSE from client_record_vw WHERE house='{house_name}' AND returned=0")
            print(query.lastError().text())
            clients = []
            while query.next():
                clients.append(((query.value(
                    0) + ' ' + query.value(1) + ' ' + query.value(2) + ' ' + query.value(3))))
                
            # if owing clients exist
            print(clients)
            if clients:
                num_left = len(clients) - 2
                if num_left > 0:
                    # only display two clients of many that haven't returned the book
                    QMessageBox.information(
                        self, 'Error', f"""<p style='color:#2020e6; font-size: 13px;'>The follwing clients from <span style='color:#13589e'>{house_name}</span> have unreturned books:</p>
                                            <p style='color:#13589e'>{', '.join(clients[:2])} and {num_left} more.</p>
                                            <p>Can't delete this class.</p>""")
                elif num_left == 0:
                    # display the two clients that haven't returned the book
                    QMessageBox.information(
                        self, 'Error', f"""<p style='color:#2020e6; font-size: 13px;'>The follwing clients from <span style='color:#13589e'>{house_name}</span> have unreturned books:</p>
                                            <p style='color:#13589e'>{' and '.join(clients)}.</p>
                                            <p>Can't delete this class.</p>""")
                else:
                    # display the client that hasn't returned the book
                    QMessageBox.information(
                        self, 'Error', f"""<p style='color:#2020e6; font-size: 13px;'>The follwing client from <span style='color:#13589e'>{house_name}</span> has unreturned books:</p>
                                            <p style='color:#13589e'>{''.join(clients)}.</p>
                                            <p>Can't delete this class.</p>""")

            # if owing clients don't exist
            else:
                query.exec_(
                    f"DELETE FROM houses WHERE house='{house_name}'")
                print('house: ', query.lastError().text())
                QMessageBox.information(
                    self, 'Deleted', "<p style='color:#2020e6; font-size: 13px;'>House successfully deleted.</p>")
                query.exec_(
                    f"""INSERT INTO history(user_name, [action], [table]) VALUES("{self.username}", "Deleted '{house_name}'", "houses")""")

                self.updateHouseComboBoxes()
                self.history_table_model.submitAll()
            
        else:
            QMessageBox.warning(self, 'Error', "<p style='color:#842029; font-size: 13px;'>No valid input given</p>")

        self.delete_house_cb.setCurrentIndex(-1)

    def changeHouseName(self):
        """Changes house name of existing house and updates houses of clients that belong to it to the new house name
        """
        current_house_name = self.current_house_name_cb.currentText()
        new_house_name = self.new_house_name.text().strip().upper()

        # if input fields are filled out
        if new_house_name and current_house_name:

            query.exec_(
                f"UPDATE houses SET house='{new_house_name}' WHERE house='{current_house_name}'")

            # if unique constraint error
            if query.lastError().isValid():
                    QMessageBox.critical(
                        self, 'Error', f"""<p style='color:crimson; font-size: 13px;'>Failed to change house name.</p>
                                            <p><span style='color:#13589e'>{new_house_name}</span> already exists.</p>""")
            else:
                    # manual cascade on update
                    query.exec_(
                        f"UPDATE clients SET client_house='{new_house_name}' WHERE client_house='{current_house_name}'")
                    QMessageBox.information(
                        self, 'Changed', "<p style='color:#2020e6; font-size: 13px;'>House name successfully changed.</p>")
                    query.exec_(
                        f"""INSERT INTO history(user_name, [action], [table]) VALUES("{self.username}", "Changed '{current_house_name}' to '{new_house_name}'", "houses")""")

                    self.updateHouseComboBoxes()
                    self.history_table_model.submitAll()
            
        else:
            QMessageBox.warning(
                self, 'Error', "<p style='color:#842029; font-size: 13px;'>No valid input given.</p>")

        self.current_house_name_cb.setCurrentIndex(-1)
        self.new_house_name.clear()

    def handleButtons(self):
        """Connects buttons to functions that are invoked when the buttons are triggered
        """
        #About
        
        self.about_btn.clicked.connect(self.showAbout)

        # Close, Minimise, Maximize connections
        self.close_btn.clicked.connect(lambda: btn_close_clicked(self))
        self.min_btn.clicked.connect(lambda: btn_min_clicked(self))
        self.max_btn.clicked.connect(lambda: btn_max_clicked(self))
        ###################################

        # Permissions Group Box connections
        self.b_group = QButtonGroup()
        self.b_group.addButton(self.checkBox_21)
        self.b_group.addButton(self.checkBox_22)
        self.b_group.addButton(self.checkBox)
        self.b_group.buttonClicked.connect(self.checkPermissions)
        ###################################

        self.logout_btn.clicked.connect(self.handleLogout)  # logout connection

        # Main Tab Buttons' connections
        self.dashboard_btn.clicked.connect(self.open_dashboard_tab)
        self.books_btn.clicked.connect(self.open_books_tab)
        self.issue_book_btn.clicked.connect(self.open_issue_book_tab)
        self.report_btn.clicked.connect(self.open_report_tab)
        self.history_btn.clicked.connect(self.open_history_tab)
        self.settings_btn.clicked.connect(self.open_settings_tab)
        self.users_btn.clicked.connect(self.open_users_tab)
        ###################################

        ############Books Tab connections START#############
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
        self.category_lw.itemClicked.connect(self.categorySelected)
        self.client_record_tv.selectionModel().selectionChanged.connect(self.bookSelected)
        ############Books Tab connections END#############

        ############Issue Books Tab connections START#############
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
        self.retrieve_book_btn.clicked.connect(
            lambda: self.retrieveBook(self.book_title_category_label.text(), self.quantity_spin_box_4.value()))
        ############Issue Books Tab connections END#############

        ############Users Tab connections START#############
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
        self.show_password_cb.stateChanged.connect(
            lambda: self.showPassword(self.password_le, self.password_le_2, self.show_password_cb.checkState()))
        ############Users Tab connections END#############

        ############Settings Tab connections START#############
        # user connections
        self.change_username_le.textChanged.connect(
            self.confirmUsernameChange)
        self.change_username_btn.clicked.connect(self.changeUsername)
        self.change_password_le.textChanged.connect(
            self.confirmPasswordChange)
        self.change_password_le_2.textChanged.connect(
            self.confirmPasswordChange)
        self.change_password_btn.clicked.connect(self.changePassword)
        self.show_password_cb_2.stateChanged.connect(
            lambda: self.showPassword(self.change_password_le, self.change_password_le_2, self.show_password_cb_2.checkState()))

        # class connections
        self.add_class_btn.clicked.connect(self.addClass)
        self.delete_class_btn.clicked.connect(self.deleteClass)
        self.change_class_name_btn.clicked.connect(self.changeClassName)

        # house connections
        self.add_house_btn.clicked.connect(self.addHouse)
        self.delete_house_btn.clicked.connect(self.deleteHouse)
        self.change_house_name_btn.clicked.connect(self.changeHouseName)
        ############Settings Tab connections END#############

    def showAbout(self):
        QMessageBox.about(self, 'About', '''<p style='color:#13589e; font-size: 14px; font-weight: bold'>HILLCREST LIBRARY MANAGEMENT SYSTEM</p>
                                            <p>By:\t <a style='text-decoration: none;'href='https://github.com/Porcupine1'>Thomas Ngulube</a></p>
                                            <p>Project GitHub repo: <a style='text-decoration: none;'href='https://github.com/Porcupine1/School_Library_System'> Source Code</a> version 1.0</p>
                                            <p>Blog: <a style='text-decoration: none;'href='https://thomasngulube.wordpress.com'>thomasngulube.wordpress.com</a></p>''')
    
    def handleLogout(self):
        """closes main window and then shows login window
        """

        self.close()
        login_window.show()

    def closeEvent(self, event):
        """Closes main window and records log out in history table
        """

        query.exec_(
            f"""INSERT INTO history(user_name, [action]) VALUES('{self.username}', 'LOGGED OUT')""")
        event.accept()

    def checkPermissions(self, cb: QCheckBox):
        """checks admin or standard permissions

        Args:
            cb (QCheckBox): admin or standard permissions checkbox
        """

        permissions = QTreeWidgetItemIterator(self.permissions_tree_widget)

        # if admin permissions checkbox is checked, check all permissions
        if cb.text() == 'Admin Permissions':
            while permissions.value():
                permissions.value().setCheckState(0, Qt.Checked)
                permissions += 1

        # if standard permissions checkbox is checked
        elif cb.text() == 'Standard Permissions':
            while permissions.value():
                # if current permission is an admin permission, don't check it
                if permissions.value().text(0) in ['Edit Book', 'Delete Book', 'Users History', 'Delete Class',  'Change Class Name',
                                                   'Delete House', 'Change House Name', 'Users', 'Delete User', 'Create User',
                                                   'Give Permissions']:
                    permissions.value().setCheckState(0, Qt.Unchecked)

                # if current permission is a standard permission, check it
                else:
                    permissions.value().setCheckState(0, Qt.Checked)
                permissions += 1

        # uncheck all permissions
        else:
            while permissions.value():
                permissions.value().setCheckState(0, Qt.Unchecked)
                permissions += 1

    def enablePermissionSearch(self):
        """Enables permission search button when user enters an existing user
        """
        username = self.username_le_2.text().strip()
        if username in self.usernames:
            self.load_permissions_btn.setEnabled(True)
            self.username_label_2.clear()
            self.changeProperty(self.username_label_2, "class", None)
        elif not username:
            self.username_label_2.clear()
            self.changeProperty(self.username_label_2, "class", None)
        else:
            self.username_label_2.setText(f'"{username}" is not a user.')
            self.changeProperty(self.username_label_2,
                                "class", "alert alert-danger")
            self.load_permissions_btn.setEnabled(False)

    def loadUserPermssions(self):
        """Loads permissions of searched user and checks the check boxes respectively
        """
        self.searched_user = self.username_le_2.text().strip()
        permissions = QTreeWidgetItemIterator(self.permissions_tree_widget)

        # show searched user's name
        self.permission_gb.setTitle(f"{self.searched_user}'s permissions")

        query.exec_(
            f"""SELECT * FROM user_permissions WHERE user_name='{self.searched_user}'""")

        index = 1  # does not start from zero because it is the user's user_name
        while query.next():
            while permissions.value():
                # if searched user has permission
                if query.value(index) == 2:
                    permissions.value().setCheckState(0, Qt.Checked)
                elif query.value(index) == 1:
                    permissions.value().setCheckState(0, Qt.PartiallyChecked)
                # if searched user doesn't have permission
                else:
                    permissions.value().setCheckState(0, Qt.Unchecked)
                index += 1  # next permission
                permissions += 1

        self.username_le_2.clear()
        self.give_permissions_btn.setEnabled(True)
        self.load_permissions_btn.setEnabled(False)

    def giveUserPermissions(self):
        """Gives searched user permission respective of checked user permissions check boxes
        """

        permissions = QTreeWidgetItemIterator(self.permissions_tree_widget)
        self.permission_gb.setTitle(f"User's Permissions")
        query.prepare(
            "INSERT INTO user_permissions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)")
        query.addBindValue(self.searched_user)

        # bind all permission values
        while permissions.value():
            query.addBindValue(permissions.value().checkState(0))
            permissions += 1

        query.exec_()  # commit query

        permissions_2 = QTreeWidgetItemIterator(self.permissions_tree_widget)
        # uncheck all permissions
        while permissions_2.value():
            permissions_2.value().setCheckState(0, Qt.Unchecked)
            permissions_2 += 1

        query.exec_(
            f"""INSERT INTO history(user_name, [action], [table]) VALUES("{self.username}", "EDITED '{self.searched_user}' permissions.", "user_permissions")""")
        self.history_table_model.submitAll()
        self.searched_user = None
        self.give_permissions_btn.setEnabled(
            False)  # disabled give_permissions_btn
        QMessageBox.information(
            self, 'Operation Successful',
            """<p style='color:#2020e6; font-size: 13px;'>Permissions applied successfully.</p>
                </p>Changes will take effect on user's next login.</p>""")

    @staticmethod
    def showPassword(password_le: QLineEdit, password_le_2: QLineEdit, state):
        """hides both password is show passwordcheck box is unchecked and shows them if it is checked

        Args:
            password_le (QLineEdit): password line edit
            password_le_2 (QLineEdit): confirm password lined edit
            state (_type_): show_password check box state(checked or unchecked)
        """

        # if checked, show
        if state == Qt.Checked:
            password_le.setEchoMode(QLineEdit.Normal)
            password_le_2.setEchoMode(QLineEdit.Normal)

        # if unchecked, hide
        else:
            password_le.setEchoMode(QLineEdit.Password)
            password_le_2.setEchoMode(QLineEdit.Password)

    def showUsers(self):
        """loads all users and shows them in a table
        """

        self.users_table_model = QSqlTableModel()
        self.users_table_model.setTable('users')
        self.users_tv.setModel(self.users_table_model)
        self.users_tv.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_tv.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.users_table_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.users_table_model.select()
        self.users_tv.hideColumn(0)
        self.users_tv.hideColumn(3)

    def createUser(self):
        """Creates user, give them permissions and records the action in the history table
        """
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
            f"""INSERT INTO history(user_name, [action], [table]) VALUES("{self.username}", "ADDED '{name}, {username}'", "users")""")
        self.history_table_model.submitAll()
        query.exec_(
            f"INSERT INTO user_permissions VALUES('{username}',2,1,2,0,0,2,2,2,2,2,1,0,2,1,2,0,0,2,0,0,0,0,0,0)")
        query.exec_(
            f"""INSERT INTO history(user_name, [action], [table]) VALUES("{self.username}", "GAVE '{username} Standard permissions'", "user_permissions")""")
        self.history_table_model.submitAll()
        self.usernames.append(username)
        self.increase_dash_val(self.users_val, 1)
        self.fname_le_3.clear()
        self.lname_le_3.clear()
        self.username_le.clear()
        self.password_le.clear()
        self.password_le_2.clear()
        self.username_taken_l.clear()
        self.changeProperty(self.username_taken_l, "class", None)
        self.username_le.setStyleSheet("border-color: #394453;")
        self.password_le.setStyleSheet("border-color: #394453;")
        self.password_le_2.setStyleSheet("border-color: #394453;")

    def userSelected(self):
        """shows the user name of te selected user in username_label line edit
        """

        row = self.users_tv.currentIndex().row()
        username = self.users_tv.currentIndex().sibling(row, 1).data()
        self.username_label.setText(username)
        self.delete_user_btn.setEnabled(True)

    def deleteUser(self):
        """Removes permissions, deletes user and records the action in the history table
        """

        username = self.username_label.text()
        response = QMessageBox.question(
            self, 'Delete User', f"""<p style='color:#2020e6; font-size: 13px;'>Are you sure you want to delete <span style='color:#13589e'>{username}</span>?</p>
                                    <p>This cannot be undone.</p>""", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

        if response == QMessageBox.Yes:
            query.exec_(
                f"DELETE FROM user_permissions WHERE user_name='{username}'")
            query.exec_(
                f"""INSERT INTO history(user_name, [action], [table]) VALUES("{self.username}", "REMOVED '{username} permissions'", "user_permissions")""")
            query.exec_(f"DELETE FROM users WHERE user_name='{username}'")
            self.users_table_model.submitAll()
            query.exec_(
                f"""INSERT INTO history(user_name, [action], [table]) VALUES("{self.username}", "DELETED '{username}'", "users")""")
            self.history_table_model.submitAll()
            self.usernames.remove(username)
            self.decrease_dash_val(self.users_val, 1)
            self.username_label.clear()
            self.delete_user_btn.setEnabled(False)
            QMessageBox.information(
                self, 'Operation Successful', "<p style='color:#2020e6; font-size: 13px;'>Deleted user successfully.</p>", QMessageBox.Ok, QMessageBox.Ok)

    def usernameConfirm(self):
        """checks username line edit for inputted text. if none is give, lets the user know a response is given (red
        border around the line edit and some explanation text). if the entered username is already taken, a response
        is given (orange border around the line edit and some explanation text). Else, a green border is set around
        the line edit.
        """
        username = self.username_le.text().strip()

        # if not input is given
        if not username:
            self.username_taken_l.setText(f'"NO VALID INPUT GIVEN"')
            self.changeProperty(self.username_taken_l,
                                "class", "alert alert-danger")
            self.username_le.setStyleSheet(
                "border-color: crimson;")  # set border color to red
            self.create_user_btn.setEnabled(False)

        # if username is already taken
        elif username in self.usernames:
            self.username_taken_l.setText(f'"{username}" is already taken.')
            self.changeProperty(self.username_taken_l,
                                "class", "alert alert-warning")
            self.username_le.setStyleSheet(
                "border-color: orange;")  # set border color to red
            self.create_user_btn.setEnabled(False)

        else:
            self.username_taken_l.clear()
            self.changeProperty(self.username_taken_l, "class", None)
            self.username_le.setStyleSheet("border-color: lime;")
            self.confirmCreateUser()

    def confirmPassword(self):
        """Checks if both passeord line edits in create user tab text match. If not a response is given (red
        border around the line edit and some explanation text) for both no entry and entry mismatch.
        Else, a different response is given (green border around the line edit and some explanation text)
        """
        password1 = self.password_le.text()
        password2 = self.password_le_2.text()

        # if not input is given in both line edits
        if not password1 and not password2:
            self.conf_password_info_le.setText("NO INPUT GIVEN")
            self.changeProperty(self.conf_password_info_le,
                                "class", "alert alert-danger")
            self.password_le_2.setStyleSheet("border-color: crimson;")
            self.password_le.setStyleSheet("border-color: #394453;")
            self.create_user_btn.setEnabled(False)

        # if both passwords match
        elif password1 == password2:
            self.conf_password_info_le.setText("Passwords match!")
            self.changeProperty(self.conf_password_info_le,
                                "class", "alert alert-success")
            self.password_le.setStyleSheet("border-color: lime;")
            self.password_le_2.setStyleSheet("border-color: lime;")
            self.confirmCreateUser()

        else:
            self.conf_password_info_le.setText("Passwords do not match!")
            self.changeProperty(self.conf_password_info_le,
                                "class", "alert alert-danger")
            self.password_le_2.setStyleSheet("border-color: crimson;")
            self.password_le.setStyleSheet("border-color: #394453;")
            self.create_user_btn.setEnabled(False)

    def confirmCreateUser(self):
        """Enables the create user button if both both password line edits are filled and match and inputted user name is filled and is 
        not already taken
        """

        username = self.username_le.text().strip()
        password1 = self.password_le.text()
        password2 = self.password_le_2.text()

        if username and password1 and password2 and username not in self.usernames and password1 == password2:
            self.create_user_btn.setEnabled(True)

    def styleCurrentTabBtn(self, prev: QPushButton, current: QPushButton):
        """Changes background color of selected main tab button and reverts the change of the previous one.

        Args:
            prev (QPushButton): previous selected tab button
            current (QPushButton): current selected tab button
        """
        prev.setProperty('class', 'main_tabs')
        prev.style().unpolish(prev)
        prev.style().polish(prev)
        prev.update()
        
        current.setProperty('class', 'current_tab_btn')
        current.style().unpolish(current)
        current.style().polish(current)
        current.update()
    
    def open_dashboard_tab(self):
        # set dashboard tab current tab
        self.styleCurrentTabBtn(self.current_tab_btn,self.dashboard_btn)
        self.main_tab_widget.setCurrentIndex(0)
        self.current_tab_btn = self.dashboard_btn

    def open_books_tab(self):
        # set books tab current tab
        self.styleCurrentTabBtn(self.current_tab_btn,self.books_btn)
        self.main_tab_widget.setCurrentIndex(1)
        self.current_tab_btn = self.books_btn

    def open_issue_book_tab(self):
        # set issue book tab current tab
        self.styleCurrentTabBtn(self.current_tab_btn,self.issue_book_btn)
        self.main_tab_widget.setCurrentIndex(2)
        self.current_tab_btn = self.issue_book_btn

    def open_report_tab(self):
        # set report tab current tab
        self.styleCurrentTabBtn(self.current_tab_btn,self.report_btn)
        self.main_tab_widget.setCurrentIndex(3)
        self.current_tab_btn = self.report_btn

    def open_history_tab(self):
        # set history tab current tab
        self.styleCurrentTabBtn(self.current_tab_btn,self.history_btn)
        self.main_tab_widget.setCurrentIndex(4)
        self.current_tab_btn = self.history_btn

    def open_settings_tab(self):
        # set settings tab current tab
        self.styleCurrentTabBtn(self.current_tab_btn,self.settings_btn)
        self.main_tab_widget.setCurrentIndex(5)
        self.current_tab_btn = self.settings_btn

    def open_users_tab(self):
        # set users tab current tab
        self.styleCurrentTabBtn(self.current_tab_btn,self.users_btn)
        self.main_tab_widget.setCurrentIndex(6)
        self.current_tab_btn = self.users_btn

    def showBookSearchResults(self, data: list):
        """Show details of searched book

        Args:
            data (list): [id, title, category, quantity]
        """
        
        timer = Timer
        timer.daemon = True #interupt program cleanly by finishing main thread
        
        self.edit_book_data = data
        self.edit_info_label.setText(f'"{data[0][1]}" found!')
        self.changeProperty(self.edit_info_label, "class",
                            "alert alert-success")
        timer(5.0, self.vanishResponse, [self.edit_info_label]).start()
        self.book_title_le_2.setText(data[0][1])
        self.category_combo_box_2.setCurrentIndex(
            self.category_combo_box_2.findText(data[0][2]))
        self.quantity_spin_box_2.setValue(data[0][3])

        self.edit_extra_label.setText(
            f'"{data[0][1]}" appeared in the following categories:')
        self.updateCategoryList(data)
    
    def vanishResponse(self, label: QLabel):
        """vanishes labbel response

        Args:
            label (QLabel): response label
        """
        label.clear()
        self.changeProperty(label, 'class', None)
    
    def searchBook(self, book_title: str, category=None):
        """
        Checks if no book title input is given. If yes an error message is displayed.
        Else, it checks for book title in inputted category and returns (True, book_id) if yes.
        Else, it checks if it is at all in any category (in the database) if yes, returns
        ('Try different category', None) (leting the user know that it appeared in another category).
        Else, returns (False, None) (it is not in the database)
        """
        if book_title == "":
            QMessageBox.warning(
                self, 'Invalid Entry', "<p style='color:#842029; font-size: 13px;'>Book title is required!</p>", QMessageBox.Ok, QMessageBox.Ok)
            return (False, None)
        else:
            query.exec_(
                f"SELECT * FROM books WHERE book_title = '{book_title}' AND category = '{category}'")

            timer = Timer
            timer.daemon = True #interupt program cleanly by finishing main thread
        
            data = []
            if query.next():
                row = [query.value(0), query.value(
                    1), query.value(2), query.value(3)]
                data.append(row)
                self.showBookSearchResults(data)
                return (True, row[0])

            # if book is not in inputted category, check if it is at all in the database
            else:
                query.exec_(
                    f"SELECT * FROM books WHERE book_title = '{book_title}'")
                while query.next():
                    row = [query.value(0), query.value(
                        1), query.value(2), query.value(3)]
                    data.append(tuple(row))

                # if book is not in database, let the user know (returns false)
                if not data:
                    QMessageBox.warning(
                        self, 'Not Found', 
                        f"<p style='color:#842029; font-size: 13px;'><span style='color:#13589e'>{book_title}</span> not found.</p>",
                        QMessageBox.Ok, QMessageBox.Ok)
                    self.edit_extra_label.clear()
                    self.clear_book_entry(
                        self.book_title_le_2, self.category_combo_box_2, self.quantity_spin_box_2)

                    self.category_lw.clear()
                    self.edit_extra_label.setText(
                        f'"{book_title}" did not appear in any category.')
                    self.edit_info_label.setText(f'"{book_title}" not found.')
                    self.changeProperty(
                        self.edit_info_label, "class", "alert alert-danger")
                    timer(5.0, self.vanishResponse, [self.edit_info_label]).start()
                    return (False, None)

                else:
                    self.showBookSearchResults(data)
                    return ('Try different category', None)

    def addBook(self, book_title: str, category: str, quantity: int):
        """Adds book and or category to the database if it does not exist.
        """

        # if input field is empty
        if book_title == "" or category == "":
            QMessageBox.warning(
                self, 'Invalid Entry', "<p style='color:#842029; font-size: 13px;'>Book title is required!</p>",
                QMessageBox.Ok, QMessageBox.Ok)

        # if all input fields are filled
        else:
            result = self.addCategory(category, None)
            query.exec_(
                f"INSERT INTO books(book_title, category, quantity) VALUES('{book_title}', '{category}', {quantity})")

            self.book_table_model.submitAll()
            self.booksTableSort()

            # if book already exists
            if query.lastError().isValid():
                QMessageBox.warning(
                    self, 'Book exists',
                    f"<p style='color:#842029; font-size: 13px;'><span style='color:#13589e'>{book_title}</span> already exists in <span style='color:#13589e'>{category}</span> category.</p>",
                    QMessageBox.Ok, QMessageBox.Ok)

            # if book doesn't exist
            else:
                query.exec_(
                    f"""INSERT INTO history(user_name, [action], [table]) VALUES("{self.username}", "ADDED '{book_title}, {category}, {quantity}'", "books")""")
                self.history_table_model.submitAll()

                # if category didn't exists(now it does)
                if result != 'exists':
                    QMessageBox.information(
                        self, 'Operation Successful',
                        f"<p style='color:#842029; font-size: 13px;'><span style='color:#13589e'>{book_title}</span> and <span style='color:#13589e'>{category}</span> category were successfully added!</p>",
                        QMessageBox.Ok, QMessageBox.Ok)

                # if category already existed
                else:
                    QMessageBox.information(
                        self, 'Operation Successful', f"<p style='color:#2020e6; font-size: 13px;'><span style='color:#13589e'>{book_title}</span> was successfully added!</p>", 
                        QMessageBox.Ok, QMessageBox.Ok)
            self.clear_book_entry(
                self.book_title_le, self.category_combo_box, self.quantity_spin_box)
            # updates book title completer
            # update book title completer data
            self.book_title_model.setQuery("SELECT DISTINCT book_title FROM books")

    def deleteBook(self, book_title: str, category: str):
        """Deletes book from database if no client is owing any quantity/number of the book
        """

        # check if book exists in specified catgory
        found, book_id = self.searchBook(book_title, category)

        timer = Timer
        timer.daemon = True #interupt program cleanly by finishing main thread
        
        # if book is found
        if found:
            # check if client/s has/have not returned it
            query.exec_(
                f"SELECT client_id FROM client_records WHERE book_id={book_id} AND returned=0")
            client_ids = []
            while query.next():
                client_ids.append(query.value(0))
            print(client_ids)
            # if has not been returned by one or more clients
            if client_ids:
                data = []
                for client_id in client_ids:
                    query.exec_(
                        f"SELECT client_first_name, client_last_name, client_class, client_house FROM clients WHERE client_id={client_id}")
                    while query.next():
                        data.append((query.value(0) + ' ' + query.value(1) +
                                    ' ' + query.value(2) + ' ' + query.value(3)))
                    num_left = len(data) - 2
                if num_left > 0:
                    # only display two clients of many that haven't returned the book
                    QMessageBox.information(
                        self, 'Error', f"""<p style='color:#2020e6; font-size: 13px;'>The follwing clients have not returned this book:</p>
                                            <p style='color:#13589e'>{', '.join(data[:2])} and {num_left} more.</p>
                                            <p>Can't delete this book.</p>""")
                elif num_left == 0:
                    # display the two clients that haven't returned the book
                    QMessageBox.information(
                        self, 'Error', f"""<p style='color:#2020e6; font-size: 13px;'>The follwing clients have not returned this book:</p>
                                            <p style='color:#13589e'>{' and '.join(data)}.</p>
                                            <p>Can't delete this book.</p>""")
                else:
                    # display the client that hasn't returned the book
                    QMessageBox.information(
                        self, 'Error', f"""<p style='color:#2020e6; font-size: 13px;'>The follwing client has not returned this book:</p>
                                            <p style='color:#13589e'>{''.join(data)}.</p>
                                            <p>Can't delete this book.</p>""")

                self.edit_info_label.setText('Delete failed')
                self.changeProperty(self.edit_info_label,
                                    "class", "alert alert-danger")
                timer(5.0, self.vanishResponse, [self.edit_info_label]).start()

            # if has been returned
            else:
                response = QMessageBox.question(
                    self, 'Delete book',
                    f"""<p style='color:#2020e6; font-size: 13px;'>Are you sure you want to delete all books titled <span style='color:#13589e'>{book_title}</span> in <span style='color:#13589e'>{category}</span> category from the library?</p>
                        <p>Click No to change category.</p>
                        <p style='font-weight:bold'>NB: This can\'t be undone.</p>""",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

                # if user is sure to delete book
                if response == QMessageBox.Yes:
                    query.exec_(
                        f"""DELETE FROM books WHERE book_title='{book_title}' AND category='{category}'""")
                    print(query.lastError().text())
                    self.edit_info_label.setText(
                        f'"{book_title}" deleted from "{category}" category.')
                    self.changeProperty(self.edit_info_label,
                                        "class", "alert alert-success")
                    timer(5.0, self.vanishResponse, [self.edit_info_label]).start()
                    query.exec_(
                        f"""INSERT INTO history(user_name, [action], [table]) VALUES("{self.username}", "DELETED '{book_title}, {category}'", "books")""")
                    self.history_table_model.submitAll()
                    self.clear_book_entry(
                        self.book_title_le_2, self.category_combo_box_2, self.quantity_spin_box_2)
                    self.edit_book_data = []  # reset self.edit_book_data
                    self.updateCategoryList([(None, book_title, None, None)])
                    self.book_table_model.submitAll()  # update all books table
                    self.booksTableSort()  # sort the all books table
                    # update book title completer data
                    self.book_title_model.setQuery(
                        "SELECT DISTINCT book_title FROM books")
        if found == 'Try different category':
            QMessageBox.warning(
                self, 'Book Not found', 
                f"""<p style='color:#842029; font-size: 13px;'><span style='color:#13589e'>{book_title}</span> is not in <span style='color:#13589e'>{category}</span> category.</p>
                    <p>Try different category.</p>""",
                    QMessageBox.Ok, QMessageBox.Ok)

    def editBook(self, book_title: str, category: str, quantity: int):
        """Edits book data of book data in self.edit_book_data with new data passed as parameters. 
        a book has to be searched first to edit it.
        """

        def completeBookEdit(book_title: str, category: str, quantity: int):
            """Completes edit book function
            """
            query.exec_(
                f"UPDATE books SET book_title='{book_title}', category='{category}', quantity={quantity} WHERE book_id={int(self.edit_book_data[0][0])}")
            self.book_table_model.submitAll()
            self.booksTableSort()
            query.exec_(
                f"""INSERT INTO history(user_name, [action], [table]) 
                VALUES("{self.username}", "EDITED FROM '{self.edit_book_data[0][1]}, {self.edit_book_data[0][2]}, {self.edit_book_data[0][3]}' TO '{book_title}, {category}, {quantity}'", "books")""")
            self.history_table_model.submitAll()
            QMessageBox.information(
                self, 'Changes Successful', "<p style='color:#2020e6; font-size: 13px;'>Book successfully edited!</p>", QMessageBox.Ok, QMessageBox.Ok)

            self.category_cb_model.submitAll()
            self.edit_book_data = []
            self.clear_book_entry(
                self.book_title_le_2, self.category_combo_box_2, self.quantity_spin_box_2)
            index = self.category_combo_box.findText("Unknown")
            self.category_combo_box.setCurrentIndex(index)
            self.category_combo_box_3.setCurrentIndex(index)
            self.edit_info_label.clear()
            self.changeProperty(self.edit_info_label, "class", None)
            self.edit_extra_label.clear()
            self.category_lw.clear()

        # if no book has been searched
        if not self.edit_book_data:
            QMessageBox.information(
                self, 'Search First',
                """<p style='color:#2020e6; font-size: 13px;'>You have not searched for book.</p>
                    <p>First search for book in library to obtain it's data before you can edit it.</p>""",
                QMessageBox.Ok, QMessageBox.Ok)

        # if no changes have been made
        elif self.edit_book_data == [(int(self.edit_book_data[0][0]), book_title, category, quantity)]:
            QMessageBox.information(
                self, 'No Change Detected', "<p style='color:#2020e6; font-size: 13px;'>You have not made any change to book</p>",
                QMessageBox.Ok, QMessageBox.Ok)

        # if book has been searched and changes have been made
        else:
            if self.edit_book_data[0][2] != category:
                found = self.searchBook(book_title, category)

                # if book with same title already exists in the inputted category
                if found is True:
                    QMessageBox.information(
                        self, 'Exists', 
                        f"<p style='color:#2020e6; font-size: 13px;'><span style='color:#13589e'>{book_title}</span> already exists in <span style='color:#13589e'>{category}</span></p>",
                        QMessageBox.Ok, QMessageBox.Ok)
                else:
                    completeBookEdit(book_title, category, quantity)
            else:
                completeBookEdit(book_title, category, quantity)

    def addClient(self, fname: str, lname: str, class_: str, house: str):
        """creates client if they don't already exist and returns the client's id
        """

        # if client input fields  are empty
        if fname == "" or lname == "" or class_ == "" or house == "":
            QMessageBox.warning(
                self, 'Invalid', "<p style='color:#842029; font-size: 13px;'>Fill out all entries.</p>", QMessageBox.Ok, QMessageBox.Ok)

        else:
            query.exec_(
                f"""INSERT INTO clients(client_first_name, client_last_name, client_class, client_house) VALUES('{fname}', '{lname}', '{class_}', '{house}')""")

            # if query is successful(client didn't already exist)
            if query.lastError().isValid() is False:
                query.exec_(
                    f"""INSERT INTO history(user_name, [action], [table]) VALUES("{self.username}", "ADDED '{fname} {lname}, {class_}, {house}'", "clients")""")
                self.history_table_model.submitAll()

            query.exec_(
                f"""SELECT client_id FROM clients WHERE client_first_name = '{fname}' AND client_last_name = '{lname}' AND client_class = '{class_}' AND client_house = '{house}'""")

            # updates clients' first name completer
            self.first_name_model.setQuery(
                "SELECT DISTINCT client_first_name FROM clients")
            # updates clients' last name completer
            self.last_name_model.setQuery(
                "SELECT DISTINCT client_last_name FROM clients")

            while query.next():
                client_id = query.value(0)
                return client_id

    def retrieveBook(self, book: str, quantity: int):
        """Retrieves books from client

        Args:
            book (str): "book_title" | "category"
            quantity (int): book quantity retrieved
        """

        # if no book is selected
        if book == "":
            QMessageBox.information(self, 'Book Not Selected',
                                    """<p style='color:#2020e6; font-size: 13px;'>You have not selected a book to retrieve.</p>
                                        <p>First search for student, then select a book to retrieve.</p>""",
                                    QMessageBox.Ok, QMessageBox.Ok)
        # if book is selected
        else:
            fname, lname, class_, house = self.client_info_label.text().split('\t')
            book_title, category = book.split(' | ')
            book_title = book_title.strip('"')
            category = category.strip('"')
            query.exec_(
                f"""SELECT client_id FROM clients WHERE client_first_name='{fname}' AND client_last_name='{lname}' AND client_class='{class_}' AND client_house='{house}'""")

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

            # if transaction has already been made today, only insert given quantity
            if self.today_transac_count > 0:
                query.exec_(
                    f"""INSERT INTO transactions(client_id, book_id, quantity, type, user_id)
                    VALUES({client_id}, {book_id}, {quantity}, 'RETRIEVE', {self.user_id})""")
                self.today_transac_count += 1  # increase today's transaction count

            # If no transaction have been performed today, add an obligatory zero quantity transaction of the day
            else:
                query.exec_(
                    f"""INSERT INTO transactions(client_id, book_id, quantity, type, user_id)
                    VALUES({client_id}, {book_id}, {quantity}, 'RETRIEVE', {self.user_id})""")
                query.exec_(
                    f"""INSERT INTO transactions(type, user_id)
                    VALUES('LEND', {self.user_id})""")  # Zero quantity transaction of day
                self.today_transac_count += 1  # Increase transaction count, exclusive of zero quantity transaction of day

            query.exec_(
                f"""UPDATE books SET quantity=quantity+{quantity} WHERE book_id={book_id}""")
            QMessageBox.information(self, 'Retrieved', "<p style='color:#2020e6; font-size: 13px;'>Book retrieved.</p>")

            self.increase_dash_val(self.retrieved_today_val, quantity)
            self.increase_dash_val(self.total_retrieved_val, quantity)
            self.decrease_dash_val(self.unretrieved_val, quantity)
            self.book_table_model.submitAll()
            self.booksTableSort()
            self.clients_records_table_model.setQuery(QSqlQuery('SELECT * FROM client_record_vw WHERE returned=0'))
            self.setTransactionTableQuery()
            self.book_title_category_label.clear()
            self.quantity_spin_box_4.setValue(0)
            self.setClientRecordTableQuery(fname, lname, class_, house)
            # close chart
            self.chart.close()
            self.chart_view.close()
            self.plotTransactionGraph()  # Recreate graph

    def lendBook(self, book_title: str, category: str, quantity: int):
        """Lends book to client. If client doesn't exist, they are created. if client is already owing that book, it added to the owing quantity.if the client has borrowed the book before client's recrds is set to returned=0(False) and quantity is updated

        Args:
            book_title (str): book title
            category (str): category
            quantity (int): quantity
        """
        def completeLendBook(book_id: int, quantity: int):
            """Completes lend book function
            """
            client_id = self.addClient(self.formatText(self.fname_le.text()), self.formatText(self.lname_le.text()),
                                       self.class_combo_box.currentText(
            ), self.house_combo_box.currentText())

            # if clients now exists(didn't exists and now added), record transaction
            if client_id:
                query.exec_(
                    f"""INSERT INTO client_records(client_id, book_id, quantity, returned) VALUES({client_id}, {book_id}, {quantity}, FALSE)""")

                # if client has borrowed the same book before
                if query.lastError().isValid():
                    query.exec_(
                        f"""UPDATE client_records SET quantity=quantity+{quantity}, returned=FALSE WHERE client_id={client_id} AND book_id={book_id}""")

                # if transaction has already been made today, only insert given quantity
                if self.today_transac_count > 0:
                    query.exec_(
                        f"""INSERT INTO transactions(client_id, book_id, quantity, type, user_id) 
                        VALUES({client_id}, {book_id}, {quantity}, 'LEND', {self.user_id})""")
                    self.today_transac_count += 1

                else:
                    # If no transaction have been performed today, add obligatory zero quantity transaction of day
                    query.exec_(
                        f"""INSERT INTO transactions(client_id, book_id, quantity, type, user_id) 
                        VALUES({client_id}, {book_id}, {quantity}, 'LEND', {self.user_id})""")
                    query.exec_(
                        f"""INSERT INTO transactions(type, user_id) 
                            VALUES('RETRIEVE', {self.user_id})""")  # Zero quantity transaction of day
                    self.today_transac_count += 1  # Increase transaction count, exclusive of zero quantity transaction of day

                query.exec_(
                    f"""UPDATE books SET quantity=quantity-{quantity} WHERE book_id={book_id}""")
                QMessageBox.information(self, 'Lent', "<p style='color:#2020e6; font-size: 13px;'>Book lent</p>")
                self.increase_dash_val(self.lent_today_val, quantity)
                self.increase_dash_val(self.total_lent_val, quantity)
                self.increase_dash_val(self.unretrieved_val, quantity)
                self.book_table_model.submitAll()
                self.booksTableSort()
                self.setTransactionTableQuery()
                self.clients_records_table_model.setQuery(QSqlQuery('SELECT * FROM client_record_vw WHERE returned=0'))
                self.clear_book_entry(
                    self.book_title_le_3, self.category_combo_box_3, self.quantity_spin_box_3)
                self.clear_client_entry(
                    self.fname_le, self.lname_le, self.class_combo_box, self.house_combo_box)

                # close chart
                self.chart.close()
                self.chart_view.close()
                self.plotTransactionGraph()  # Recreate graph

        query.exec_(
            f"""SELECT * FROM books WHERE book_title='{book_title}' AND category='{category}'""")
        data = {}
        while query.next():
            data['book_id'] = int(query.value(0))
            data['quantity'] = int(query.value(3))
        if not data:
            QMessageBox.warning(
                self, 'Not Found',
                f"""<p style='color:#842029; font-size: 13px;'><span style='color:#13589e'>{book_title}</span> is not in <span style='color:#13589e'>{category}</span> category.</p>
                    <p>Make sure you have spelled them correctly or search using the Edit/Delete tab.</p>""",
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
                                                f"""<p style='color:#2020e6; font-size: 13px;'>There {quantity_words[0]} only {data["quantity"]} {quantity_words[1]} titled <span style='color:#13589e'>{book_title}</span> in <span style='color:#13589e'>{category}</span> category left.</p>
                                                    <p>Do you want to get all of them?</p>""",
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if response == QMessageBox.Yes:
                    print("collect all")
                    quantity = int(data['quantity'])
                    completeLendBook(int(data['book_id']), quantity)

            else:
                completeLendBook(data['book_id'], quantity)

    def addCategory(self, category: str, label: QLabel or None) -> str or None:
        """
        Adds category to database if it does not exist.
        """
        timer = Timer
        timer.daemon = True #interupt program cleanly by finishing main thread
        if category:
            query.exec_(
                f"INSERT INTO categories VALUES('{category}')")
            self.category_cb_model.submitAll()
            index = self.category_combo_box.findText('Unknown')
            self.category_combo_box.setCurrentIndex(index)
            self.category_combo_box_2.setCurrentIndex(index)
            self.category_combo_box_3.setCurrentIndex(index)

            # if category already exists
            if query.lastError().isValid():
                if label is not None:
                    label.setText(
                        f'"{category}" category already exists in library.')
                    self.changeProperty(label, "class", "alert alert-warning")
                    timer(5.0, self.vanishResponse,[label]).start()
                return 'exists'

            else:
                query.exec_(
                    f"""INSERT INTO history(user_name, [action], [table]) VALUES("{self.username}", "ADDED '{category}'", "categories")""")
                self.history_table_model.submitAll()

            if label is not None:
                label.setText(
                    f'"{category}" category successfully added to library.')
                self.changeProperty(label, "class", "alert alert-success")
                timer(5.0, self.vanishResponse,[label]).start()
                self.add_category_le.clear()

        else:
            if label is not None:
                label.setText("NO INPUT GIVEN!")
                self.changeProperty(label, "class", "alert alert-danger")
                timer(5.0, self.vanishResponse,[label]).start()
        query.clear()

    def searchCategory(self, category: str) -> None:
        """
        Checks if category already exists.

        """
        timer = Timer
        timer.daemon = True #interupt program cleanly by finishing main thread
        if category:
            query.exec_(
                f"SELECT * FROM categories WHERE category = '{category}'")

            data = []
            while query.next():
                data.append(query.value(0))

            # if category does not exist
            if not data:
                self.category_info_label.setText(
                    f'"{category}" category does not exist in library.')
                self.changeProperty(self.category_info_label,
                                    "class", "alert alert-warning")
                timer(5.0, self.vanishResponse,[self.category_info_label]).start()

            else:
                self.category_info_label.setText(
                    f'"{category}" category exists in library.')
                self.changeProperty(self.category_info_label,
                                    "class", "alert alert-success")
                self.add_category_le.clear()
                timer(5.0, self.vanishResponse,[self.category_info_label]).start()

        else:
            self.category_info_label.setText("NO INPUT GIVEN!")
            self.changeProperty(self.category_info_label,
                                "class", "alert alert-danger")
            timer(5.0, self.vanishResponse,[self.category_info_label]).start()
            

if __name__ == '__main__':
    database = QSqlDatabase.addDatabase("QSQLITE")
    database.setDatabaseName(os.path.join(basedir, "Library.db"))

    if not database.open():
        print("Unable to open data source file.")
        sys.exit(1)
    query = QSqlQuery(database)
    query.setForwardOnly(True)
    app = QApplication(sys.argv)
    screen_width = QDesktopWidget().screenGeometry().width()
    screen_height = QDesktopWidget().screenGeometry().height()
    main_style = open(os.path.join(basedir, 'themes/main.css'), 'r')
    login_style = open(os.path.join(basedir, 'themes/login.css'), 'r')
    main_style = main_style.read()
    login_style = login_style.read()
    app.setStyleSheet(main_style + login_style)
    app.setWindowIcon(QIcon(os.path.join(basedir, "icons/app_icon.png")))
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())
