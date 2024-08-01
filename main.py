from flask import Flask, render_template, request, jsonify
from flask_mail import Mail, Message
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.units import inch
import base64
import requests
from io import BytesIO
import pandas as pd

app = Flask(__name__)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'project.propques@gmail.com'
app.config['MAIL_PASSWORD'] = 'srcrthwcvdkaslap'
app.config['MAIL_DEFAULT_SENDER'] = 'project.propques@gmail.com'

mail = Mail(app)

# Load the cleaned CSV data
coworking_data = pd.read_csv('data/coworking_spaces.csv')
retail_data = pd.read_csv('data/99_acres.csv')

def send_email(to_email, name, properties):
    try:
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Bold', fontName='Helvetica-Bold'))
        elements = []

        for p in properties:
            for img_url in [p['img1'], p['img2']]:
                if isinstance(img_url, str) and (img_url.startswith('http://') or img_url.startswith('https://')):
                    try:
                        response = requests.get(img_url)
                        img = Image(BytesIO(response.content), width=4*inch, height=3*inch)
                        elements.append(img)
                    except Exception as e:
                        print(f"Error processing image {img_url}: {e}")
                else:
                    print(f"Invalid URL: {img_url}")

            elements.append(Paragraph(f"Name: {p['name']}", styles['Bold']))
            elements.append(Paragraph(f"Address: {p['micromarket']}, {p['city']}", styles['Bold']))
            elements.append(Paragraph("Details:", styles['Bold']))
            elements.append(Paragraph(str(p['details']), styles['Normal']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("About:", styles['Bold']))
            elements.append(Paragraph(str(p['about']), styles['Normal']))
            elements.append(Spacer(1, 12))

        doc.build(elements)
        pdf_buffer.seek(0)

        message = Message(subject='Your Property Data',
                          recipients=[to_email],
                          #cc=['buzz@propques.com', 'enterprise.propques@gmail.com'],
                          html=f"<strong>Dear {name},</strong><br>"
                               "<strong>Please find attached the details of the properties you requested:</strong><br><br>"
                               "If you're interested in maximizing the benefits of the above properties at no cost, please reply to this email with 'Deal.' We will assign an account manager to coordinate with you.")
        message.attach("property_data.pdf", "application/pdf", pdf_buffer.read())

        mail.send(message)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

@app.route('/', methods=['GET', 'POST'])
def index():
    property_type = None
    selected_city = None
    selected_micromarket = None
    budget = None
    micromarkets = []
    filtered_properties = pd.DataFrame()

    if request.method == 'POST':
        print("Form Data:", request.form)
        property_type = request.form.get('property_type')
        selected_city = request.form.get('city')
        selected_micromarket = request.form.get('micromarket')
        budget = request.form.get('budget')
        name = request.form.get('name')
        mobile = request.form.get('mobile')
        email = request.form.get('email')

        if property_type == 'coworking':
            data = coworking_data
        else:
            data = retail_data

        cities = data['city'].dropna().unique().tolist()
        print("Cities:", cities)

        if selected_city:
            micromarkets = data[data['city'] == selected_city]['micromarket'].dropna().unique().tolist()
            print("Micromarkets:", micromarkets)

        if selected_micromarket and budget:
            budget = float(budget)
            filtered_properties = data[(data['city'] == selected_city) &
                                       (data['micromarket'] == selected_micromarket) &
                                       (data['price'] <= budget)]
            print("Filtered Properties:", filtered_properties)
            if not filtered_properties.empty:
                # Send email with property details
                send_email(email, name, filtered_properties.to_dict('records'))

        return render_template('index.html',
                               property_type=property_type,
                               cities=cities,
                               micromarkets=micromarkets,
                               selected_city=selected_city,
                               selected_micromarket=selected_micromarket,
                               filtered_properties=None,
                               has_filtered_properties=False)

    return render_template('index.html', property_type=None, cities=[], micromarkets=[], selected_city=None, selected_micromarket=None, filtered_properties=None, has_filtered_properties=False)

@app.route('/get_cities', methods=['POST'])
def get_cities():
    property_type = request.form.get('property_type')
    if property_type == 'coworking':
        data = coworking_data
    else:
        data = retail_data
    cities = data['city'].dropna().unique().tolist()
    return jsonify(cities)

@app.route('/get_micromarkets', methods=['POST'])
def get_micromarkets():
    property_type = request.form.get('property_type')
    selected_city = request.form.get('city')
    if property_type == 'coworking':
        data = coworking_data
    else:
        data = retail_data
    micromarkets = data[data['city'] == selected_city]['micromarket'].dropna().unique().tolist()
    return jsonify(micromarkets)

@app.route('/get_prices', methods=['POST'])
def get_prices():
    property_type = request.form.get('property_type')
    selected_city = request.form.get('city')
    selected_micromarket = request.form.get('micromarket')
    if property_type == 'coworking':
        data = coworking_data
    else:
        data = retail_data
    prices = data[(data['city'] == selected_city) & (data['micromarket'] == selected_micromarket)]['price'].dropna().unique().tolist()
    return jsonify(prices)

if __name__ == '__main__':
    app.run(debug=True)
