from flask import Flask, jsonify, request, session, send_file, render_template
from flask_swagger_ui import get_swaggerui_blueprint
import requests
import mysql.connector
import getpass
import sys
import os
import secrets

app1 = Flask(__name__)
app1.secret_key = secrets.token_hex(16)
app1.template_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))


@app1.route('/')
def show_welcome():
    return "Welcome to the web app, navigate to the correct endpoints for your responses 👍"


@app1.route('/static/<path:path>')
def send_static(path):
    return send_file(f'static/{path}')


SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'


@app1.route(SWAGGER_URL)
def swagger_ui():
    return render_template('swagger_ui.html')


@app1.route('/api/connect_db', methods=['POST'])
def connect_db():
    data = request.get_json()

    hostname = data.get('hostname')
    username = data.get('username')
    user_password = data.get('password')
    database_name = data.get('database')

    session['hostname'] = hostname
    session['username'] = username
    session['password'] = user_password
    session['database'] = database_name

    response = {
        'message': 'User inputs stored successfully'
    }
    return jsonify(response)


@app1.route('/api/fetch_data', methods=['GET', 'POST'])
def fetch_data():
    url = 'https://api.bittrex.com/v3/markets/summaries'
    response = requests.get(url)
    data = response.json()
    return jsonify(data)


@app1.route('/api/store_data', methods=['GET', 'POST'])
def store_data():
    hostname = session.get('hostname')
    username = session.get('username')
    user_password = session.get('password')
    database_name = session.get('database')

    conn = mysql.connector.connect(
        host=hostname,
        user=username,
        password=user_password,
        database=database_name
    )

    if conn.is_connected():
        print("Connected to MySQL database")
    else:
        print("Failed to connect to MySQL database")
        sys.exit(1)

    cursor = conn.cursor(prepared=True)
    cursor.execute("SELECT VERSION()")
    result = cursor.fetchone()
    print("MySQL Server Version:", result[0])

    create_table_query = '''
        CREATE TABLE IF NOT EXISTS market_data (
            symbol VARCHAR(255) PRIMARY KEY,
            high DECIMAL(18, 8),
            low DECIMAL(18, 8),
            volume DECIMAL(18, 8),
            quotevolume DECIMAL(18, 8),
            percentchange DECIMAL(18, 8),
            updatedtime VARCHAR(255)
        );
    '''
    cursor.execute(create_table_query)
    url = "https://api.bittrex.com/v3/markets/summaries"
    response = requests.get(url)
    data = response.json()

    insert_query = """
        INSERT INTO market_data (symbol, high, low, volume, quotevolume, percentchange, updatedtime)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    for row in data:
        symbol = row.get('symbol', None)
        high = row.get('high', None)
        low = row.get('low', None)
        volume = row.get('volume', None)
        quotevolume = row.get('quoteVolume', None)
        percentchange = row.get('percentChange', None)
        updatedtime = row.get('updatedAt', None)

        cursor.execute(insert_query, (symbol, high, low, volume, quotevolume, percentchange, updatedtime))

    conn.commit()
    conn.close()
    return jsonify({'message': 'Data stored successfully'})


if __name__ == '__main__':
    app1.run()
