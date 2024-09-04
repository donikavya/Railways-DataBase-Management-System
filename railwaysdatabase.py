from http.server import BaseHTTPRequestHandler, HTTPServer
import cgi
import cx_Oracle
from datetime import datetime
import random
import os

DB_USER = 'system'
DB_PASSWORD = 'yourpassword'
DB_DSN = 'yourhostname'

def get_db_connection():
    try:
        return cx_Oracle.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
    except cx_Oracle.DatabaseError as e:
        print(f"Database connection error: {e}")
        raise

def setup_database():
    try:
        con = get_db_connection()
        cur = con.cursor()
        
        # Create the accounts table if it does not exist
        cur.execute("""
            BEGIN
                EXECUTE IMMEDIATE 'CREATE TABLE accounts (
                    id INT PRIMARY KEY,
                    pass VARCHAR2(16),
                    name VARCHAR2(100),
                    sex CHAR(1),
                    age VARCHAR2(3),
                    dob DATE,
                    ph_no CHAR(10)
                )';
            EXCEPTION
                WHEN OTHERS THEN
                    IF SQLCODE != -955 THEN
                        RAISE;
                    END IF;
            END;
        """)

        # Create the tickets table if it does not exist
        cur.execute("""
            BEGIN
                EXECUTE IMMEDIATE 'CREATE TABLE tickets (
                    id INT,
                    PNR INT,
                    train VARCHAR2(25),
                    doj DATE,
                    tfr VARCHAR2(100),
                    tto VARCHAR2(100)
                )';
            EXCEPTION
                WHEN OTHERS THEN
                    IF SQLCODE != -955 THEN
                        RAISE;
                    END IF;
            END;
        """)

        # Ensure 'doj' column is of type DATE
        cur.execute("""
            BEGIN
                EXECUTE IMMEDIATE 'ALTER TABLE tickets MODIFY doj DATE';
            EXCEPTION
                WHEN OTHERS THEN
                    IF SQLCODE != -1461 THEN
                        RAISE;
                    END IF;
            END;
        """)

        cur.close()
        con.close()
    except cx_Oracle.DatabaseError as e:
        print(f"Database setup error: {e}")

class RequestHandler(BaseHTTPRequestHandler):
    session_data = {}

    def do_GET(self):
        if self.path == '/':
            self.send_login_page()
        elif self.path == '/style.css':
            self.send_css()
        elif self.path.startswith('/static/'):
            self.send_static_file()
        else:
            self.send_error(404, 'File not found')

    def do_POST(self):
        if self.path == '/login':
            self.handle_login()
        elif self.path == '/purchase_ticket':
            self.handle_ticket_purchase()
        elif self.path == '/show_ticket':
            self.handle_show_ticket()
        elif self.path == '/cancel_ticket':
            self.handle_cancel_ticket()
        elif self.path == '/account_settings':
            self.handle_account_settings()
        elif self.path == '/logout':
            self.handle_logout()
        else:
            self.send_error(404, 'File not found')

    def send_login_page(self, message=""):
        content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Railway Management System - Login</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
                    .container {{ width: 80%; margin: auto; padding: 20px; background: white; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }}
                    h1 {{ color: #333; }}
                    p {{ color: #555; }}
                    a {{ text-decoration: none; color: #0066cc; }}
                    a:hover {{ text-decoration: underline; }}
                    form {{ margin: 20px 0; }}
                    input {{ display: block; margin-bottom: 10px; padding: 10px; width: 100%; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Railway Management System</h1>
                    <p>{message}</p>
                    <form action="/login" method="post">
                        <input type="text" name="id" placeholder="ID" required>
                        <input type="password" name="password" placeholder="Password" required>
                        <input type="submit" value="Login">
                    </form>
                </div>
            </body>
            </html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode())

    def send_css(self):
        css_content = """
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }
            .container { width: 80%; margin: auto; padding: 20px; background: white; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }
            h1 { color: #333; }
            p { color: #555; }
            a { text-decoration: none; color: #0066cc; }
            a:hover { text-decoration: underline; }
            form { margin: 20px 0; }
            input { display: block; margin-bottom: 10px; padding: 10px; width: 100%; }
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/css')
        self.end_headers()
        self.wfile.write(css_content.encode())

    def send_static_file(self):
        file_path = self.path[8:]
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'rb') as file:
                    content = file.read()
                self.send_response(200)
                self.send_header('Content-type', 'application/octet-stream')
                self.end_headers()
                self.wfile.write(content)
            except IOError:
                self.send_error(500, 'Internal Server Error')
        else:
            self.send_error(404, 'File not found')

    def send_main_menu(self, message=""):
        content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Railway Management System - Main Menu</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
                    .container {{ width: 80%; margin: auto; padding: 20px; background: white; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }}
                    h1 {{ color: #333; }}
                    p {{ color: #555; }}
                    a {{ text-decoration: none; color: #0066cc; }}
                    a:hover {{ text-decoration: underline; }}
                    form {{ margin: 20px 0; }}
                    input {{ display: block; margin-bottom: 10px; padding: 10px; width: 100%; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Railway Management System</h1>
                    <p>{message}</p>
                    <form action="/purchase_ticket" method="post">
                        <h2>Purchase Ticket</h2>
                        <input type="text" name="train" placeholder="Train" required>
                        <input type="date" name="doj" placeholder="Date of Journey" required>
                        <input type="text" name="departure" placeholder="Departure Station" required>
                        <input type="text" name="destination" placeholder="Destination Station" required>
                        <input type="submit" value="Purchase Ticket">
                    </form>
                    <form action="/show_ticket" method="post">
                        <h2>Check Ticket Status</h2>
                        <input type="text" name="pnr" placeholder="PNR Number" required>
                        <input type="submit" value="Check Ticket Status">
                    </form>
                    <form action="/cancel_ticket" method="post">
                        <h2>Request a Refund</h2>
                        <input type="text" name="pnr" placeholder="PNR Number" required>
                        <input type="submit" value="Cancel Ticket">
                    </form>
                    <form action="/account_settings" method="post">
                        <input type="submit" value="Account Settings">
                    </form>
                    <form action="/logout" method="post">
                        <input type="submit" value="Logout">
                    </form>
                </div>
            </body>
            </html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode())

    def handle_login(self):
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
        user_id = form.getvalue('id')
        password = form.getvalue('password')

        if user_id and password:
            con = get_db_connection()
            cur = con.cursor()
            cur.execute('SELECT * FROM accounts WHERE id = :id AND pass = :pass', {'id': user_id, 'pass': password})
            account = cur.fetchone()
            cur.close()
            con.close()

            if account:
                self.session_data['user_id'] = user_id
                self.send_main_menu("Login successful")
            else:
                self.send_login_page("Invalid ID or Password")
        else:
            self.send_login_page("ID and Password are required")

    def handle_ticket_purchase(self):
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
        train = form.getvalue('train')
        doj = form.getvalue('doj')
        departure = form.getvalue('departure')
        destination = form.getvalue('destination')

        if 'user_id' in self.session_data and train and doj and departure and destination:
            try:
                # Convert the doj to the correct format
                doj_date = datetime.strptime(doj, "%Y-%m-%d").date()
                
                con = get_db_connection()
                cur = con.cursor()
                pnr = random.randint(100000, 999999)
                query = """
                    INSERT INTO tickets (id, PNR, train, doj, tfr, tto)
                    VALUES (:1, :2, :3, :4, :5, :6)
                """
                cur.execute(query, (self.session_data['user_id'], pnr, train, doj_date, departure, destination))
                con.commit()

                self.send_main_menu(f"Ticket purchased successfully! Your PNR is {pnr}.")

                cur.close()
                con.close()
            except cx_Oracle.DatabaseError as e:
                self.send_main_menu(f"Database error: {e}")
        else:
            self.send_main_menu("Please fill in all fields.")

    def handle_show_ticket(self):
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
        pnr = form.getvalue('pnr')

        if pnr:
            con = get_db_connection()
            cur = con.cursor()
            cur.execute('SELECT * FROM tickets WHERE PNR = :pnr', {'pnr': pnr})
            ticket = cur.fetchone()
            cur.close()
            con.close()

            if ticket:
                content = f"""
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Ticket Status</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
                            .container {{ width: 80%; margin: auto; padding: 20px; background: white; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }}
                            h1 {{ color: #333; }}
                            p {{ color: #555; }}
                            a {{ text-decoration: none; color: #0066cc; }}
                            a:hover {{ text-decoration: underline; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>Ticket Status</h1>
                            <p><strong>PNR:</strong> {ticket[1]}</p>
                            <p><strong>Train:</strong> {ticket[2]}</p>
                            <p><strong>Date of Journey:</strong> {ticket[3]}</p>
                            <p><strong>From:</strong> {ticket[4]}</p>
                            <p><strong>To:</strong> {ticket[5]}</p>
                            <a href="/">Back to Main Menu</a>
                        </div>
                    </body>
                    </html>
                """
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(content.encode())
            else:
                self.send_main_menu("No ticket found with the given PNR")
        else:
            self.send_main_menu("PNR is required to check ticket status")

    def handle_cancel_ticket(self):
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
        pnr = form.getvalue('pnr')

        if pnr:
            con = get_db_connection()
            cur = con.cursor()
            cur.execute('DELETE FROM tickets WHERE PNR = :pnr', {'pnr': pnr})
            con.commit()
            cur.close()
            con.close()
            self.send_main_menu("Ticket cancellation request processed")
        else:
            self.send_main_menu("PNR is required to cancel a ticket")

    def handle_account_settings(self):
        self.send_main_menu("Account settings feature is not implemented yet.")

    def handle_logout(self):
        self.session_data.clear()
        self.send_login_page("You have been logged out")

    def send_error(self, code, message=None):
        self.send_response(code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Error {code}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
                    .container {{ width: 80%; margin: auto; padding: 20px; background: white; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }}
                    h1 {{ color: #333; }}
                    p {{ color: #555; }}
                    a {{ text-decoration: none; color: #0066cc; }}
                    a:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Error {code}</h1>
                    <p>{message if message else 'An error occurred'}</p>
                    <a href="/">Back to Main Menu</a>
                </div>
            </body>
            </html>
        """
        self.wfile.write(content.encode())

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8081):
    setup_database()
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd server on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    run()
