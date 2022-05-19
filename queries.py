create_users_table_query = '''CREATE TABLE IF NOT EXISTS users (
                                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_name   VARCHAR (30)    NOT NULL
                                                            UNIQUE,
                                name        VARCHAR (30),
                                user_password   VARCHAR  NOT NULL
                            );'''

create_books_table_query = '''CREATE TABLE IF NOT EXISTS books (
                                book_id    INTEGER  PRIMARY KEY AUTOINCREMENT,
                                book_title VARCHAR NOT NULL,
                                category   VARCHAR NOT NULL
                                                    DEFAULT Unknown,
                                quantity   INTEGER NOT NULL,
                                UNIQUE (book_title, category), 
                                CONSTRAINT category FOREIGN KEY(category) REFERENCES categories (category)
                            );'''

create_clients_table_query = '''CREATE TABLE IF NOT EXISTS clients (
                                    client_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                                    client_first_name VARCHAR(30)    NOT NULL,
                                    client_last_name VARCHAR(30)    NOT NULL,
                                    client_class    VARCHAR(4)    NOT NULL,
                                    client_house    VARCHAR(4)    NOT NULL,
                                    UNIQUE (client_first_name, client_last_name, client_class, client_house),
                                    CONSTRAINT client_class FOREIGN KEY(client_class) REFERENCES classes (class),
                                    CONSTRAINT client_house FOREIGN KEY(client_house) REFERENCES houses (house)
                                    );'''

create_client_records_table_query = '''CREATE TABLE IF NOT EXISTS client_records (
                                        client_id  INTEGER  NOT NULL,
                                        book_id    INTEGER REFERENCES books (book_id) 
                                                        NOT NULL,
                                        quantity INTEGER NOT NULL,
                                        returned    BOOLEAN NOT NULL,
                                        UNIQUE (client_id, book_id),
                                        CONSTRAINT client FOREIGN KEY(client_id) REFERENCES clients (client_id),
                                        CONSTRAINT book FOREIGN KEY(book_id) REFERENCES books (book_id)
                            );'''

create_transactions_table_query = '''CREATE TABLE IF NOT EXISTS transactions (
                                    client_id   INTEGER,
                                    book_id INTEGER,
                                    quantity INTEGER DEFAULT (0),
                                    type    VARCHAR(30)    NOT NULL,
                                    user_id INTEGER NOT NULL,
                                    datetime    datetime NOT NULL
                                                         DEFAULT (DATETIME('now', 'localtime')),
                                    CONSTRAINT book FOREIGN KEY(book_id) REFERENCES books (book_id),
                                    CONSTRAINT client FOREIGN KEY(client_id) REFERENCES clients (client_id),
                                    CONSTRAINT user FOREIGN KEY(user_id) REFERENCES Users (user_id));'''

create_categories_table_query = '''CREATE TABLE IF NOT EXISTS categories (
                                category VARCHAR PRIMARY KEY
                                );'''

create_client_record_view_query = '''CREATE VIEW IF NOT EXISTS client_record_vw AS
                                        SELECT  client_first_name AS FIRST_NAME,
                                                client_last_name AS LAST_NAME,
                                                client_class AS CLASS,
                                                client_house AS HOUSE,
                                                books.book_title AS BOOK_TITLE,
                                                books.category AS CATEGORY,
                                                client_records.quantity AS OWING_QUANTITY,
                                                returned AS RETURNED
                                                FROM clientS
                                                INNER JOIN client_records ON
                                                clients.client_id = client_records.client_id
                                                INNER JOIN
                                                books ON client_records.book_id = books.book_id;'''

create_transaction_acc_view_query = '''CREATE VIEW IF NOT EXISTS transaction_acc_vw AS
                                        SELECT coalesce(sum(quantity), 0) AS QUANTITY,
                                        type AS TYPE, 
                                        date FROM dates
                                            LEFT JOIN
                                            transactions ON date(transactions.datetime) = dates.date
                                        WHERE date <= date('now', 'localtime') 
                                        GROUP BY date,
                                                type;'''

create_history_table_query = '''CREATE TABLE IF NOT EXISTS history (
                                user_name   VARCHAR(30) NOT NULL,
                                [action]    VARCHAR(30) NOT NULL,
                                [table] VARCHAR(30),
                                datetime    NOT NULL
                                                DEFAULT (DATETIME('now', 'localtime')),
                                CONSTRAINT user FOREIGN KEY(user_name)REFERENCES users (user_name)
                            );'''

create_user_permissions_table_query = '''CREATE TABLE IF NOT EXISTS user_permissions (
                                            user_name        VARCHAR    PRIMARY KEY ON CONFLICT REPLACE NOT NULL,
                                            dashboard_tab    BOOLEAN NOT NULL,
                                            books_tab        BOOLEAN NOT NULL,
                                            books_tab__add_book         BOOLEAN NOT NULL,
                                            books_tab__edit_book        BOOLEAN NOT NULL,
                                            books_tab__delete_book      BOOLEAN NOT NULL,
                                            books_tab__add_category     BOOLEAN NOT NULL,
                                            issue_book_tab   BOOLEAN NOT NULL,
                                            issue_book_tab__lend_book        BOOLEAN NOT NULL,
                                            issue_book_tab__retrieve_book    BOOLEAN NOT NULL,
                                            reports_tab       BOOLEAN NOT NULL,
                                            history_tab      BOOLEAN NOT NULL,
                                            history_tab__users_history   BOOLEAN NOT NULL,
                                            history_tab__transactions_history    BOOLEAN NOT NULL,
                                            settings_tab     BOOLEAN NOT NULL,
                                            settings_tab__add_class        BOOLEAN NOT NULL,
                                            settings_tab__delete_class        BOOLEAN NOT NULL,
                                            settings_tab__change_class_name        BOOLEAN NOT NULL,
                                            settings_tab__add_house        BOOLEAN NOT NULL,
                                            settings_tab__delete_house        BOOLEAN NOT NULL,
                                            settings_tab__change_house_name        BOOLEAN NOT NULL,
                                            users_tab        BOOLEAN NOT NULL,
                                            users_tab__create_user      BOOLEAN NOT NULL,
                                            users_tab__delete_user      BOOLEAN NOT NULL,
                                            users_tab__give_permissions BOOLEAN NOT NULL,
                                            CONSTRAINT user FOREIGN KEY(user_name)REFERENCES users (user_name)
                                        );'''

create_houses_table_query = '''CREATE TABLE IF NOT EXISTS houses (
                                    house VARCHAR UNIQUE ON CONFLICT IGNORE
                                );'''

create_classes_table_query = '''CREATE TABLE IF NOT EXISTS classes (
                                    class VARCHAR UNIQUE ON CONFLICT IGNORE
                                );'''
