import re
from datetime import datetime
from flask import Flask, render_template, url_for, flash, request, redirect
from googleapiclient.discovery import build

app = Flask(__name__)

# Replace with your API key and calendar ID
API_KEY = 'AIzaSyBrSepztiiinJcyMsWfUjhjcLK9qA8Cm14'
CALENDAR_ID = 'f87833500104928c8fe435ceb2db6f55e81db34f8af20624b565005f8f51eafe@group.calendar.google.com'

# Build the Google Calendar API service using the API key
service = build('calendar', 'v3', developerKey=API_KEY)


def get_upcoming_events(max_results=4):
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

@app.route("/library")
def library():
    return render_template("library.html")



@app.route("/ratings")
def ratings():
    return render_template("ratings.html")

@app.route("/results")
def results():
    return render_template("results.html")

if __name__ == "__main__":
    app.run(debug=True)