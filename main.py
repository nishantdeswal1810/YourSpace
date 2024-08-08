from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from flask_mail import Mail, Message
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image,PageBreak, Table, TableStyle,KeepTogether
from reportlab.lib.units import inch
import requests
from io import BytesIO
import pandas as pd
from pymongo import MongoClient, ASCENDING
import datetime
import secrets
import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from reportlab.pdfgen import canvas
from fpdf import FPDF
from PyPDF2 import PdfReader, PdfWriter, PageObject


# Import the OTPLessAuthSDK library
import OTPLessAuthSDK

load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'project.propques@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = 'project.propques@gmail.com'

mail = Mail(app)

# MongoDB configuration
client = MongoClient(os.environ.get('MONGO_URI'))
db = client['FindYourSpace']

# Create indexes for efficient querying
db.email_logs.create_index([('email', ASCENDING), ('date', ASCENDING)])

# Load the cleaned CSV data
coworking_data = pd.read_csv('data/coworking_spaces.csv')

def check_email_limit(email):
    if "@gmail.com" in email:
        limit_date = datetime.datetime.now() - datetime.timedelta(days=30)
        email_count = db.email_logs.count_documents({
            'email': email,
            'date': {'$gte': limit_date}
        })
        return email_count < 10
    return True

# def send_email(to_email, name, properties):
#     if not check_email_limit(to_email):
#         print(f"Email limit reached for {to_email}")
#         return False

#     try:
#         pdf_buffer = BytesIO()
#         doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
#         styles = getSampleStyleSheet()
#         styles.add(ParagraphStyle(name='Bold', fontName='Helvetica-Bold'))
#         elements = []

#         for p in properties:
#             for img_url in [p['img1'], p['img2']]:
#                 if isinstance(img_url, str) and (img_url.startswith('http://') or img_url.startswith('https://')):
#                     try:
#                         response = requests.get(img_url)
#                         img = Image(BytesIO(response.content), width=4*inch, height=3*inch)
#                         elements.append(img)
#                     except Exception as e:
#                         print(f"Error processing image {img_url}: {e}")
#                 else:
#                     print(f"Invalid URL: {img_url}")

#             elements.append(Paragraph(f"Name: {p['name']}", styles['Bold']))
#             elements.append(Paragraph(f"Address: {p['micromarket']}, {p['city']}", styles['Bold']))
#             elements.append(Paragraph("Details:", styles['Bold']))
#             elements.append(Paragraph(str(p['details']), styles['Normal']))
#             elements.append(Spacer(1, 12))
#             elements.append(Paragraph("About:", styles['Bold']))
#             elements.append(Paragraph(str(p['about']), styles['Normal']))
#             elements.append(Spacer(1, 12))

#         doc.build(elements)
#         pdf_buffer.seek(0)

#         message = Message(subject='Your Property Data',
#                           recipients=[to_email],
#                           cc=['buzz@propques.com', 'enterprise.propques@gmail.com'],
#                           html=f"<strong>Dear {name},</strong><br>"
#                                "<strong>Please find attached the details of the properties you requested:</strong><br><br>"
#                                "If you're interested in maximizing the benefits of the above properties at no cost, please reply to this email with 'Deal.' We will assign an account manager to coordinate with you.")
#         message.attach("property_data.pdf", "application/pdf", pdf_buffer.read())

#         mail.send(message)
#         print("Email sent successfully.")
#         return Truea
#     except Exception as e:
#         print(f"Failed to send email: {e}")
#         return False


#send_email for staic pdf
# def send_email(to_email, name, properties):
#     if not check_email_limit(to_email):
#         print(f"Email limit reached for {to_email}")
#         return False

#     try:
#         pdf_path = os.path.join('static', 'pdffin.pdf')

#         message = Message(subject='Your Property Data',
#                           recipients=[to_email],
#                           cc=['buzz@propques.com', 'enterprise.propques@gmail.com'],
#                           html=f"<strong>Dear {name},</strong><br>"
#                                "<strong>Please find attached the details of the properties you requested:</strong><br><br>"
#                                "If you're interested in maximizing the benefits of the above properties at no cost, please reply to this email with 'Deal.' We will assign an account manager to coordinate with you.")
#         with open(pdf_path, 'rb') as pdf_file:
#             message.attach("property_data.pdf", "application/pdf", pdf_file.read())

#         mail.send(message)
#         print("Email sent successfully.")
#         return True
#     except Exception as e:
#         print(f"Failed to send email: {e}")
#         return False


#send_email function sending correct mail with correct width but not styling
# def send_email(to_email, name, properties):
#     if not check_email_limit(to_email):
#         print(f"Email limit reached for {to_email}")
#         return False

#     try:
#         # Load the predesigned PDF and extract static pages
#         static_pdf_path = os.path.join('static', 'pdffin.pdf')
#         static_pdf = PdfReader(static_pdf_path)

#         custom_page_size = (925 * 72 / 96, 527 * 72 / 96)
        
#         # Create a new PDF for the dynamic content
#         dynamic_pdf_buffer = BytesIO()
#         doc = SimpleDocTemplate(dynamic_pdf_buffer, pagesize=custom_page_size, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
#         styles = getSampleStyleSheet()
#         styles.add(ParagraphStyle(name='Bold', fontName='Helvetica-Bold'))
#         elements = []

#         for p in properties:
#             for img_url in [p['img1'], p['img2']]:
#                 if isinstance(img_url, str) and (img_url.startswith('http://') or img_url.startswith('https://')):
#                     try:
#                         response = requests.get(img_url)
#                         img = Image(BytesIO(response.content), width=4*inch, height=3*inch)
#                         elements.append(img)
#                     except Exception as e:
#                         print(f"Error processing image {img_url}: {e}")
#                 else:
#                     print(f"Invalid URL: {img_url}")

#             elements.append(Paragraph(f"Name: {p['name']}", styles['Bold']))
#             elements.append(Paragraph(f"Address: {p['micromarket']}, {p['city']}", styles['Bold']))
#             elements.append(Paragraph("Details:", styles['Bold']))
#             elements.append(Paragraph(str(p['details']), styles['Normal']))
#             elements.append(Spacer(1, 12))
#             elements.append(Paragraph("About:", styles['Bold']))
#             elements.append(Paragraph(str(p['about']), styles['Normal']))
#             elements.append(Spacer(1, 12))
#             elements.append(PageBreak())

#         doc.build(elements)
#         dynamic_pdf_buffer.seek(0)
#         dynamic_pdf = PdfReader(dynamic_pdf_buffer)

#         # Merge static and dynamic PDFs
#         output_pdf = PdfWriter()

#         # Add static pages (pages 1, 2, and 5 from the original PDF)
#         output_pdf.add_page(static_pdf.pages[0])
#         output_pdf.add_page(static_pdf.pages[1])

#         # Add dynamic content as page 4
#         for page in dynamic_pdf.pages:
#             output_pdf.add_page(page)

#         # Add static page 5 from the original PDF
#         output_pdf.add_page(static_pdf.pages[4])

#         # Save the combined PDF to a buffer
#         combined_pdf_buffer = BytesIO()
#         output_pdf.write(combined_pdf_buffer)
#         combined_pdf_buffer.seek(0)

#         # Create email message and attach the combined PDF
#         message = Message(subject='Your Property Data',
#                           recipients=[to_email],
#                           cc=['buzz@propques.com', 'enterprise.propques@gmail.com'],
#                           html=f"<strong>Dear {name},</strong><br>"
#                                "<strong>Please find attached the details of the properties you requested:</strong><br><br>"
#                                "If you're interested in maximizing the benefits of the above properties at no cost, please reply to this email with 'Deal.' We will assign an account manager to coordinate with you.")
#         message.attach("property_data.pdf", "application/pdf", combined_pdf_buffer.read())

#         mail.send(message)
#         print("Email sent successfully.")
#         return True
#     except Exception as e:
#         print(f"Failed to send email: {e}")
#         return False
    

def send_email(to_email, name, properties):
    if not check_email_limit(to_email):
        print(f"Email limit reached for {to_email}")
        return False

    try:
        # Load the predesigned PDF and extract static pages
        static_pdf_path = os.path.join('static', 'pdffin.pdf')
        static_pdf = PdfReader(static_pdf_path)

        static_page = static_pdf.pages[0]
        static_page_size = (static_page.mediabox.width, static_page.mediabox.height)

        # Create a new PDF for the dynamic content
        dynamic_pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(dynamic_pdf_buffer, pagesize=static_page_size, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36,allowSplitting=0)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='OptionTitle', fontName='Helvetica-Bold', fontSize=64, spaceAfter=70))
        styles.add(ParagraphStyle(name='SubHeading', fontName='Helvetica-Bold', fontSize=20, spaceAfter=32))
        styles.add(ParagraphStyle(name='Content', fontName='Helvetica', fontSize=24, spaceAfter=32))
        styles.add(ParagraphStyle(name='SubHeadingContent', fontName='Helvetica', fontSize=12, spaceAfter=32,leading=24))
        elements = []

        for i, p in enumerate(properties, start=1):
            property_elements = []
            property_elements.append(Paragraph(f"Option {i}", styles['OptionTitle']))
            property_elements.append(Spacer(1, 12))

           # Add property name
            property_elements.append(Paragraph(f"Name:", styles['SubHeading']))
            property_elements.append(Paragraph(f"<font size=18>{p['name']}</font>", styles['SubHeadingContent']))
            property_elements.append(Spacer(1, 20))

            # Add property address
            property_elements.append(Paragraph(f"Address:", styles['SubHeading']))
            property_elements.append(Paragraph(f"<font size=18>{p['address']}</font>", styles['SubHeadingContent']))
            property_elements.append(Spacer(1, 20))

            # Add property details
            property_elements.append(Paragraph(f"Details:", styles['SubHeading']))
            property_elements.append(Paragraph(f"<font size=18>{p['details']}</font>", styles['SubHeadingContent']))
            property_elements.append(Spacer(1, 20))

            # Add property images
            for img_url in [p['img1'], p['img2']]:
                if isinstance(img_url, str) and (img_url.startswith('http://') or img_url.startswith('https://')):
                    try:
                        response = requests.get(img_url)
                        img = Image(BytesIO(response.content), width=7*inch, height=5*inch)
                        property_elements.append(img)
                        property_elements.append(Spacer(1, 20))
                    except Exception as e:
                        print(f"Error processing image {img_url}: {e}")
                else:
                    print(f"Invalid URL: {img_url}")

            elements.append(KeepTogether(property_elements))
            elements.append(PageBreak())

        doc.build(elements)
        dynamic_pdf_buffer.seek(0)
        dynamic_pdf = PdfReader(dynamic_pdf_buffer)

        # Merge static and dynamic PDFs
        output_pdf = PdfWriter()

        # Add static pages (pages 1, 2, and 5 from the original PDF)
        output_pdf.add_page(static_pdf.pages[0])
        output_pdf.add_page(static_pdf.pages[1])

        # Add dynamic content as pages 3 and 4
        for page in dynamic_pdf.pages:
            output_pdf.add_page(page)

        # Add static page 5 from the original PDF
        output_pdf.add_page(static_pdf.pages[4])

        # Save the combined PDF to a buffer
        combined_pdf_buffer = BytesIO()
        output_pdf.write(combined_pdf_buffer)
        combined_pdf_buffer.seek(0)

        # Create email message and attach the combined PDF
        message = Message(subject='Your Property Data',
                          recipients=[to_email],
                          cc=['buzz@propques.com', 'enterprise.propques@gmail.com'],
                          html=f"<strong>Dear {name},</strong><br>"
                               "<strong>Please find attached the details of the properties you requested:</strong><br><br>"
                               "If you're interested in maximizing the benefits of the above properties at no cost, please reply to this email with 'Deal.' We will assign an account manager to coordinate with you.")
        message.attach("property_data.pdf", "application/pdf", combined_pdf_buffer.read())

        mail.send(message)
        print("Email sent successfully.")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
    
def send_whatsapp_verification(mobile):
    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')
    redirect_uri = "https://coworkingspaceschatbot-tmva.el.r.appspot.com/verify_mobile"
    channel = "WHATSAPP"

    if not mobile.startswith('+91'):
        mobile = f"+91{mobile.lstrip('0')}"

    user_details = OTPLessAuthSDK.UserDetail.generate_magic_link(
        mobile, None, client_id, client_secret, redirect_uri, channel
    )
    return user_details

def delete_old_email_logs():
    limit_date = datetime.datetime.now() - datetime.timedelta(days=30)
    result = db.email_logs.delete_many({'date': {'$lt': limit_date}})
    print(f"Deleted {result.deleted_count} old email logs.")

scheduler = BackgroundScheduler()
scheduler.add_job(func=delete_old_email_logs, trigger="interval", weeks=1)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'verify_mobile':
            name = request.form.get('name')
            mobile = request.form.get('mobile')
            email = request.form.get('email')

            if not all([name, mobile, email]):
                flash("Name, mobile, and email are required.")
                return redirect(url_for('index'))

            session['name'] = name
            session['mobile'] = mobile
            session['email'] = email

            user = db.users.find_one({'mobile_number': mobile})

            if user:
                flash("Mobile number already verified. You can proceed to submit the form.")
            else:
                result = send_whatsapp_verification(mobile)
                if result.get('success'):
                    flash("A WhatsApp verification message has been sent to your mobile number. Please verify to proceed.")
                else:
                    flash("Failed to send WhatsApp verification.Please try again.")

            return redirect(url_for('index'))

        elif action == 'submit_form':
            name = session.get('name')
            mobile = session.get('mobile')
            email = session.get('email')
            property_type = request.form.get('property_type')
            selected_city = request.form.get('city')
            selected_micromarket = request.form.get('micromarket')
            budget = request.form.get('budget')

            if not all([name, mobile, email, property_type, selected_city, selected_micromarket, budget]):
                flash("All form fields are required.")
                return redirect(url_for('index'))

            user = db.users.find_one({'mobile_number': mobile})

            if user:
                db.users.update_one(
                    {'mobile_number': mobile},
                    {'$set': {'name': name, 'email': email}},
                    upsert=True
                )
            else:
                db.users.update_one(
                    {'mobile_number': mobile},
                    {'$setOnInsert': {'name': name, 'email': email}},
                    upsert=True
                )

            if property_type == 'coworking':
                data = coworking_data

            filtered_properties = data[(data['city'] == selected_city) &
                                       (data['micromarket'] == selected_micromarket) &
                                       (data['price'] <= float(budget))]

            if send_email(email, name, filtered_properties.to_dict('records')):
                property_data = {
                    'user_id': user['_id'],
                    'city': selected_city,
                    'micromarket': selected_micromarket,
                    'budget': float(budget),
                    'date': datetime.datetime.now()
                }
                db.properties.insert_one(property_data)

                if "@gmail.com" in email:
                    email_log = {
                        'email': email,
                        'date': datetime.datetime.now()
                    }
                    db.email_logs.insert_one(email_log)
                flash("Email sent successfully.")
            else:
                flash("Email limit reached for this Gmail address. Please try again later.")

            return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/verify_mobile', methods=['GET'])
def verify_mobile():
    token = request.args.get('code')
    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')

    user_details = OTPLessAuthSDK.UserDetail.verify_code(
        token, client_id, client_secret, None
    )

    if user_details.get('success'):
        mobile_number = user_details.get('phone_number').replace("+91", "")
        name = session.get('name')
        email = session.get('email')

        db.users.update_one(
            {'mobile_number': mobile_number},
            {'$set': {'name': name, 'email': email}},
            upsert=True
        )
        flash("Mobile number verified successfully. You can now submit the form.")
    else:
        flash("Failed to verify mobile number. Please try again.")

    return redirect(url_for('index'))

@app.route('/get_cities', methods=['POST'])
def get_cities():
    data = coworking_data
    cities = sorted(data['city'].dropna().unique().tolist())
    return jsonify(cities)

@app.route('/get_micromarkets', methods=['POST'])
def get_micromarkets():
    selected_city = request.form.get('city')
    data = coworking_data
    micromarkets = sorted(data[data['city'] == selected_city]['micromarket'].dropna().unique().tolist())
    return jsonify(micromarkets)

@app.route('/get_prices', methods=['POST'])
def get_prices():
    selected_city = request.form.get('city')
    selected_micromarket = request.form.get('micromarket')
    data = coworking_data
    prices = sorted(data[(data['city'] == selected_city) & (data['micromarket'] == selected_micromarket)]['price'].dropna().unique().tolist())
    return jsonify(prices)

if __name__ == '__main__':
    app.run(debug=True)