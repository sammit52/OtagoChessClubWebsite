import re
import json
import pandas as pd
import datetime
from flask import Flask, render_template, url_for, flash, request, redirect, session, g, send_from_directory, jsonify, render_template_string
from googleapiclient.discovery import build
import os


from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "ballz123"

HTML_UPLOAD_FOLDER = 'uploads/htmls'
PDF_UPLOAD_FOLDER = 'uploads/pdfs'
ALLOWED_PDF_EXTENSIONS = {'pdf'}
ALLOWED_HTML_EXTENSIONS = {'html'}

app.config['UPLOAD_FOLDER_PDFS'] = PDF_UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_HTMLS'] = HTML_UPLOAD_FOLDER

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/admin/upload_file', methods=['GET', 'POST'])
def admin_upload_file():
    if not g.admin_logged_in:
        return redirect(url_for("admin_login"))
    
    if request.method == 'POST':
        pdf_file = request.files.get('pdf_file')
        html_file = request.files.get('html_file')

        if pdf_file and allowed_file(pdf_file.filename, ALLOWED_PDF_EXTENSIONS):
            pdf_filename = os.path.join(app.config['UPLOAD_FOLDER_PDFS'], pdf_file.filename)
            pdf_file.save(pdf_filename)
            flash("PDF file uploaded successfully.", "success")
            return redirect(url_for('admin_dashboard'))

        if html_file and allowed_file(html_file.filename, ALLOWED_HTML_EXTENSIONS):
            html_filename = os.path.join(app.config['UPLOAD_FOLDER_HTMLS'], html_file.filename)
            html_file.save(html_filename)
            flash("HTML file uploaded successfully.", "success")
            return redirect(url_for('admin_dashboard'))

    return render_template('admin_upload_file.html')

    
# Makes it so admin can mention the file in the code with the url_for function
# Code so the admin can generate links for CMS
@app.route('/<page_name>/<filename>')
def link_file(page_name, filename):
    if allowed_file(filename, ALLOWED_PDF_EXTENSIONS):
        folder = os.path.join(app.config['UPLOAD_FOLDER_PDFS'])

    elif allowed_file(filename, ALLOWED_HTML_EXTENSIONS):
        folder = os.path.join(app.config['UPLOAD_FOLDER_HTMLS'])
    
    else:
        return "Error: Not a valid file"
    
    return send_from_directory(folder, filename)





# Simulate admin user for demonstration
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"

# Define g context middleware
@app.before_request
def before_request():
    g.admin_logged_in = session.get("admin_logged_in", False)

# ... other routes ...

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error_message = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            g.admin_logged_in = True
            flash("Logged in as admin.", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            error_message="Wrong username or password"
            flash("Invalid username or password.", "danger")
            return render_template('admin_login.html', error_message=error_message)

    return render_template("admin_login.html")

@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    g.pop("admin_logged_in", None)
    flash("Logged out.", "success")
    return redirect(url_for("admin_login"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if not g.admin_logged_in:
        return redirect(url_for("admin_login"))
    
    uploaded_pdf_files = os.listdir(app.config['UPLOAD_FOLDER_PDFS'])
    uploaded_html_files = os.listdir(app.config['UPLOAD_FOLDER_HTMLS'])



    return render_template("admin_dashboard.html", uploaded_pdf_files=uploaded_pdf_files, uploaded_html_files=uploaded_html_files)


@app.route("/admin/edit/<page>", methods=["GET", "POST"])
def admin_edit_page(page):
    if not g.admin_logged_in:
        return redirect(url_for("admin_login"))

    content_file_path = f"static/{page}_content.txt"
    content = ""  # Initialize content with an empty string

    if request.method == "POST":
        content = request.form.get("content")
        
        # Render the content using Jinja2 to process the template variables
        rendered_content = render_template_string(content)
        
        # Write the rendered content to the file
        with open(content_file_path, "w", newline='') as content_file:
            content_file.write(rendered_content)
        
        flash(f"{page.capitalize()} content saved.", "success")

    # Load the current content from the file and render it
    with open(content_file_path, "r") as content_file:
        content = content_file.read()

    rendered_content = render_template_string(content)

    return render_template("admin_edit.html", page=page, content=rendered_content)




# Replace with your API key and calendar ID
API_KEY = 'AIzaSyByyOAVN9RlcCs3NoQVLqa2gdmhrJPt558'
CALENDAR_ID = 'otagochess@gmail.com'

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

def get_upcoming_events(max_results=4):
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # Current UTC time
    events_result = service.events().list(calendarId=CALENDAR_ID, timeMin=now,
                                          maxResults=max_results, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    return events

# Need to make it so it doesn't show events in the past and only in the future!!!!

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


@app.route("/calendar")
def calendar():
    return render_template("calendar.html")

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


@app.route("/news")
def news():
    with open('static/news_content.txt', 'r') as news_file:
        news_content = news_file.read()
    return render_template("news.html", news_content=news_content)

@app.route("/notices")
def notices():
    with open('static/notices_content.txt', 'r') as notices_file:
        notices_content = notices_file.read()
    return render_template("notices.html", notices_content=notices_content)

@app.route("/tournaments")
def tournaments():
    with open('static/tournaments_content.txt', 'r') as tournaments_file:
        tournaments_content = tournaments_file.read()
    return render_template("tournament.html", tournaments_content=tournaments_content)


@app.route('/news/club_championship_ratings')
def club_championship_ratings():
    return render_template('club_championship_ratings.html')

@app.route('/news/blitz_championship_2023')
def blitz_championship_2023():
    return render_template('blitz_championship_2023.html')

@app.route('/news/graham_haase_2023')
def graham_haase_2023():
    return render_template('graham_haase_2023.html')

@app.route('/news/intercollege_chess_2023.html')
def intercollege_chess_2023():
    return render_template('intercollege_chess_2023.html')

if __name__ == "__main__":
    app.run(debug=True)


