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
