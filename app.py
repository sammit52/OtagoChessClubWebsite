import re
import json
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, url_for, flash, request, redirect
from googleapiclient.discovery import build


app = Flask(__name__)

# Replace with your API key and calendar ID
API_KEY = 'AIzaSyBrSepztiiinJcyMsWfUjhjcLK9qA8Cm14'
CALENDAR_ID = 'f87833500104928c8fe435ceb2db6f55e81db34f8af20624b565005f8f51eafe@group.calendar.google.com'

# Build the Google Calendar API service using the API key
service = build('calendar', 'v3', developerKey=API_KEY)

# Load the JSON data
with open('static/results.json', 'r') as json_file:
    game_data = json.load(json_file)

# Get the excel file
excel_file = 'static/results.xlsx'

df = pd.read_excel(excel_file, usecols=[0, 1, 2, 3, 4, 5, 6, 7])

# Rename columns for clarity
df.columns = ['Game Type', 'Date', 'White Name', 'White Rating', 'White Result', 'Black Name', 'Black Rating', 'Black Result']

# Convert the date column to strings, did this because idk ima see if it works
df['Date'] = df['Date'].astype(str)


# Convert to JSON
json_data = df.to_json(orient='records', indent=4)

json_file = 'static/results.json'
with open(json_file, 'w') as f:
    f.write(json_data)

with open('static/LibraryBooks.json', 'r', encoding='utf-8') as json_file:
    chess_books = json.load(json_file)

def get_upcoming_events(max_results=5):
    events_result = service.events().list(calendarId=CALENDAR_ID, maxResults=max_results,
                                          singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])
    return events

def format_date(date_str):
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    date_parts = date_str.split('-')
    month = months[int(date_parts[1]) - 1]
    day = date_parts[2].lstrip('0')  # Remove leading zero from the day
    formatted_date = f"{month} {day}"
    return formatted_date

@app.route("/")
def home():
    upcoming_events = get_upcoming_events(max_results=5)
    event_data = []
    for event in upcoming_events:
        event_name = event['summary']
        event_start = event['start'].get('dateTime', event['start'].get('date'))
        formatted_date = format_date(event_start.split("T")[0])  # Format the date
        event_data.append((event_name, formatted_date))

    return render_template("home.html", events=event_data)


@app.route("/hello/")
@app.route("/hello/<name>")
def hello_there(name = None):
    print(name)
    return render_template(
        "hello_there.html",
        name=name,
        date=datetime.now()
    )
    
@app.route("/api/data")
def get_data():
    return app.send_static_file("data.json")


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/news")
def news():
    return render_template("news.html")

@app.route("/notices")
def notices():
    return render_template("notices.html")

@app.route("/calendar")
def calendar():

    return render_template("calendar.html")

@app.route("/tournaments")
def tournaments():
    return render_template("tournament.html")

@app.route('/library', methods=['GET', 'POST'])
def library():
    if request.method == 'POST':
        search_type = request.form.get('Search_type')
        category = request.form.get('Category')
        notation = request.form.get('Notation')
        query = request.form.get('Query')

        if query is not None:
            query = query.lower()  # Convert query to lowercase

        search_results = []
        for book in chess_books:
            if (search_type == 'Title' and query in book.get('Title', '').lower()) or \
               (search_type == 'Author' and query in book.get('Author', '').lower()):
                if (not category or book.get('Category') == category) and \
                   (not notation or book.get('Notation') == notation):
                    search_results.append(book)

        return render_template('library.html', chess_books=chess_books, search_results=search_results, query=query)
    else:
        return render_template('library.html', chess_books=chess_books)

@app.route("/ratings")
def ratings():
    return render_template("ratings.html")


@app.route('/results', methods=['GET', 'POST'])
def results():
    game_types = set(entry['Game Type'] for entry in game_data)
    
    if request.method == 'POST':
        selected_type = request.form.get('game_type')
    else:
        selected_type = request.args.get('game_type')
    
    if selected_type and selected_type != 'All':
        filtered_data = [entry for entry in game_data if entry['Game Type'] == selected_type]
    else:
        filtered_data = game_data

    sorted_data = sorted(filtered_data, key=lambda x: x['Date'], reverse=True)

    return render_template('results.html', game_types=game_types, selected_type=selected_type, game_data=sorted_data)

if __name__ == "__main__":
    app.run(debug=True)