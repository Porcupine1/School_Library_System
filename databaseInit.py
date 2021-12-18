



# BOOKS


def addBook(book_title, quantity, category=None):
    add_book_query = f'''INSERT INTO BOOKS VALUES({book_title}, {category}, {quantity})'''
    cursor.execute(add_book_query)


def deleteBook(book_title):
    delete_book_query = f'''DELETE FROM BOOKS WHERE BOOK_TITLE={book_title}'''
    cursor.execute(delete_book_query)


def editBook(book_title, quantity, category=None):
    update_book_query = f'''UPDATE BOOKS SET BOOK_TITLE={book_title}, QUANTITY = {quantity}, BOOK_CATEGORY = {category} WHERE BOOK_TITLE={book_title}'''
    cursor.execute(update_book_query)


def returnBook(book_title, num=1):
    update_book_query = f'''UPDATE BOOKS SET QUANTITY = QUANTITY+{num} WHERE BOOK_TITLE={book_title}'''
    cursor.execute(update_book_query)


def lendBook(book_title, num=1):
    update_book_query = f'''UPDATE BOOKS SET QUANTITY = QUANTITY-{num} WHERE BOOK_TITLE={book_title}'''
    cursor.execute(update_book_query)

# USERS


def addUser(user_name, hashed_user_password):
    add_user_query = f'''INSERT INTO USERS(USER_NAME, USER_PASSWORD) VALUES({user_name}, {hashed_user_password})'''
    cursor.execute(add_user_query)


def deleteUser(user_id):
    delete_user_query = f'''DELETE FROM USERS WHERE USER_ID={user_id}'''
    cursor.execute(delete_user_query)


def editUser(user_id, user_name, hashed_user_password):
    update_user_query = f'''UPDATE USERS SET USER_NAME={user_name}, USER_PASSWORD = {hashed_user_password} WHERE USER_ID={user_id}'''
    cursor.execute(update_user_query)

def handle_transaction(type, client, book_id, user__id, datetime):
    transaction_query = f'''INSERT INTO TRANSACTIONS VALUES({type}, {client}, {book_id}, {user__id}, {datetime})'''
    cursor.execute(transaction_query)
