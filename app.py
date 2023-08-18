import re
import json
import pandas as pd
import datetime
from flask import Flask, render_template, url_for, flash, request, redirect, session, g, send_from_directory, jsonify, render_template_string
from googleapiclient.discovery import build
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import jinja2
from jinja2.exceptions import TemplateSyntaxError

app = Flask(__name__)
app.secret_key = "ballz123"

""" 
CMS ADMIN SECTION OF CODE

"""

HTML_UPLOAD_FOLDER = 'static/uploads/htmls'
PDF_UPLOAD_FOLDER = 'static/uploads/pdfs'
IMAGE_UPLOAD_FOLDER = 'static/uploads/images'
EXCEL_UPLOAD_FOLDER = 'static/uploads/excels'
ALLOWED_EXCEL_EXTENSIONS = {'xlsx'}
ALLOWED_PDF_EXTENSIONS = {'pdf'}
ALLOWED_HTML_EXTENSIONS = {'html'}
ALLOWED_IMAGE_EXTENSIONS = {'png','jpg','jpeg'}

app.config['UPLOAD_FOLDER_PDFS'] = PDF_UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_HTMLS'] = HTML_UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_IMAGES'] = IMAGE_UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_EXCELS'] = EXCEL_UPLOAD_FOLDER

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/admin/upload_file', methods=['GET', 'POST'])
def admin_upload_file():
    if not g.admin_logged_in:
        return redirect(url_for("admin_login"))
    
    if request.method == 'POST':
        pdf_file = request.files.get('pdf_file')
        html_file = request.files.get('html_file')
        image_file = request.files.get('image_file')
        excel_file = request.files.get('excel_file')

        if image_file and allowed_file(image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
            image_filename = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], image_file.filename)
            image_file.save(image_filename)
            flash("Image file uploaded successfully.", "success")
            return redirect(url_for('admin_dashboard'))

        elif pdf_file and allowed_file(pdf_file.filename, ALLOWED_PDF_EXTENSIONS):
            pdf_filename = os.path.join(app.config['UPLOAD_FOLDER_PDFS'], pdf_file.filename)
            pdf_file.save(pdf_filename)
            flash("PDF file uploaded successfully.", "success")
            return redirect(url_for('admin_dashboard'))
        
        elif html_file and allowed_file(html_file.filename, ALLOWED_HTML_EXTENSIONS):
            html_filename = os.path.join(app.config['UPLOAD_FOLDER_HTMLS'], html_file.filename)
            html_file.save(html_filename)
            flash("HTML file uploaded successfully.", "success")
            return redirect(url_for('admin_dashboard'))
        
        elif excel_file and allowed_file(excel_file.filename, ALLOWED_EXCEL_EXTENSIONS):
            excel_filename = os.path.join(app.config['UPLOAD_FOLDER_EXCELS'], excel_file.filename)
            if os.path.exists(excel_filename):
                os.remove(excel_filename)
            excel_file.save(excel_filename)
            flash("Excel file uploaded successfully.", "success")

            # UPDATE CURRENT DATABASE
            # Load new Excel data
            new_data_df = pd.read_excel(excel_filename, usecols=[0, 1, 2, 3, 4, 5, 6, 7])
            new_data_df.columns = ['Game Type', 'Date', 'White Name', 'White Rating', 'White Result', 'Black Name', 'Black Rating', 'Black Result']
            
            # Convert the date column to strings, did this because idk ima see if it works
            new_data_df['Date'] = new_data_df['Date'].astype(str)           

            # Convert new data DataFrame to JSON and append to existing data
            new_data_json = new_data_df.to_dict(orient='records')

            # Update the JSON file with the updated data
            if excel_file.filename == "results.xlsx":
                with open('static/results.json', 'w') as json_file:
                    json.dump(new_data_json, json_file, indent=4)
            elif excel_file.filename == "ratings.xlsx":
                with open('static/ratings.json', 'w') as json_file:
                    json.dump(new_data_json, json_file, indent=4)

            return redirect(url_for('admin_dashboard'))
        
        else:
            return "Error: Only accepted file types are: xlsx, pdf, html, png, jpeg and jpg" 
 

    return render_template('admin_upload_file.html')

    
# Code so the admin can generate links for CMS
@app.route('/<page_name>/<filename>')
def link_file(page_name, filename):
    if allowed_file(filename, ALLOWED_PDF_EXTENSIONS):
        folder = os.path.join(app.config['UPLOAD_FOLDER_PDFS'])

    elif allowed_file(filename, ALLOWED_HTML_EXTENSIONS):
        folder = os.path.join(app.config['UPLOAD_FOLDER_HTMLS'])

    elif allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS):
        folder = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'])
    
    else:
        return "Error: The file is not valid, the only accepted file types are: pdf, html, png, jpeg and jpg"
    
    return send_from_directory(folder, filename)

# Simulate admin user for demonstration
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"


# Define g context middleware
@app.before_request
def before_request():
    g.admin_logged_in = session.get("admin_logged_in", False)

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
    uploaded_image_files = os.listdir(app.config['UPLOAD_FOLDER_IMAGES'])


    return render_template("admin_dashboard.html", uploaded_pdf_files=uploaded_pdf_files, uploaded_html_files=uploaded_html_files, uploaded_image_files=uploaded_image_files)


@app.route("/admin/edit/<page>", methods=["GET", "POST"])
def admin_edit_page(page):
    if not g.admin_logged_in:
        return redirect(url_for("admin_login"))

    content_file_path = f"static/{page}_content.txt"
    content = ""  # Initialize content with an empty string

    if request.method == "POST":
        content = request.form.get("content")
        
        try:
            # Try to render the template to check for errors
            rendered_content = render_template_string(content)
            
            # If no errors, save the content
            with open(content_file_path, "w", newline='') as content_file:
                content_file.write(rendered_content)
            
            flash(f"{page.capitalize()} content saved.", "success")

        except jinja2.exceptions.UndefinedError as e:
            flash("Warning: There is some sort of error with your Jinja code, variable is undefined or incorrect syntax")

        except TemplateSyntaxError as e:
            # Template contains errors, display a warning message to the admin
            flash("Warning: The content contains template syntax errors. It may not render correctly.", "warning")

    # Load the current content from the file and render it
    with open(content_file_path, "r") as content_file:
        content = content_file.read()

    rendered_content = render_template_string(content)

    return render_template("admin_edit.html", page=page, content=rendered_content)


"""
ACCESSING EXCEL SHEET AND GETTING DATA

"""

# LOAD RESULTS DATA

# Get the excel file
results_excel_file = 'static/uploads/excels/results.xlsx'

df = pd.read_excel(results_excel_file, usecols=[0, 1, 2, 3, 4, 5, 6, 7])

# Rename columns for clarity
df.columns = ['Game Type', 'Date', 'White Name', 'White Rating', 'White Result', 'Black Name', 'Black Rating', 'Black Result']

# Convert the date column to strings, did this because idk ima see if it works
df['Date'] = df['Date'].astype(str)

# Convert to JSON
results_json_data = df.to_json(orient='records', indent=4)

results_json_file = 'static/results.json'
with open(results_json_file, 'w') as f:
    f.write(results_json_data)

# Load the JSON data
with open('static/results.json', 'r') as json_file:
    game_data = json.load(json_file)

# UPDATE DATABASE WHEN NEW FILE ADDED

























# LOAD RATINGS DATA



ratings_excel_file = 'static/uploads/excels/ratings.xlsx'

df2 = pd.read_excel(ratings_excel_file, usecols=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])

df2.columns = ['Game Type',	'Rank', 'Name',	'Jan',	'Feb',	'Mar',	'Apr',	'May',	'Jun',	'Jul',	'Aug',	'Sep',	'Oct',	'Nov',	'Dec',	'Gain']

# Convert to JSON
ratings_json_data = df2.to_json(orient='records', indent=4)

ratings_json_file = 'static/ratings.json'
with open(ratings_json_file, 'w') as f:
    f.write(ratings_json_data)

# Load the JSON data
with open('static/ratings.json', 'r') as json_file:
    results_data = json.load(json_file)





"""
GOOGLE API SECTION OF CODE

"""

API_KEY = "AIzaSyByyOAVN9RlcCs3NoQVLqa2gdmhrJPt558"
CALENDAR_ID = 'otagochess@gmail.com'

service = build('calendar', 'v3', developerKey=API_KEY)


def get_upcoming_events(max_results=4):
    now = datetime.datetime.utcnow().isoformat() + 'Z'  
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


"""
MAIN PAGES OF WEBSITE

"""


"""
@app.route("/about")
def about():
    return render_template("about.html")
"""

@app.route("/calendar")
def calendar():
    return render_template("calendar.html")

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


"""
PAGES THAT ACCESS DATABASES

"""


with open('static/LibraryBooks.json', 'r', encoding='utf-8') as json_file:
    chess_books = json.load(json_file)   


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


@app.route("/ratings", methods=['GET','POST'])
def ratings():
    game_types = set(entry['Game Type'] for entry in results_data)
    
    
    if request.method == 'POST':
        selected_type = request.form.get('game_type')
    else:
        selected_type = request.args.get('game_type')
    
    if selected_type == None:
        selected_type = 'Standard' # Set default display
    
    filtered_data = [entry for entry in results_data if entry['Game Type'] == selected_type]

    sorted_data = sorted(filtered_data, key=lambda x: x['Rank'], reverse=False)

    return render_template("ratings.html", game_types=game_types, selected_type=selected_type, results_data=sorted_data)



if __name__ == "__main__":
    app.run(debug=True)


