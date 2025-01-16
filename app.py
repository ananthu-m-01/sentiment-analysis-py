import base64
from flask import Flask, render_template, request, jsonify, send_file, url_for
import json
import os
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from textblob import TextBlob
from flask import Flask, request, jsonify, url_for
from xml.etree.ElementTree import Element, SubElement, ElementTree, parse, tostring
from xml.dom.minidom import parseString
import os
import pandas as pd
from flask import render_template, jsonify
from flask import Flask, request, render_template, redirect, url_for, jsonify, send_file
from flask import Flask, request, render_template, jsonify, send_file
import pandas as pd
import matplotlib.pyplot as plt
import io
# Corrected Flask initialization
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Ensure this key is strong for production

# Database configuration (replace with your actual database credentials)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:your_new_password@localhost/project'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database model for storing survey questions
class SurveyQuestions(db.Model):
    __tablename__ = 'surveyquestions'  # Explicitly bind to the existing table
    question_id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(200), nullable=False)
    responses = db.relationship('SurveyResponses', backref='question', lazy=True)  # Relationship to SurveyResponses

# Database model for storing survey responses
class SurveyResponses(db.Model):
    __tablename__ = 'survey_responses'
    response_id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('surveyquestions.question_id'), nullable=False)
    user_response = db.Column(db.String(200), nullable=False)

# Initialize database tables (only needed during setup)
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Error during db.create_all(): {e}")

# Serve the data.json file for the survey
@app.route('/get-data', methods=['GET'])
def get_data():
    try:
        data_file_path = os.path.join('data', 'data.json')
        with open(data_file_path, 'r') as file:
            data = json.load(file)
        return jsonify(data), 200
    except Exception as e:
        print(f"Error reading data.json: {e}")
        return jsonify({"message": "Failed to load survey data"}), 500

# Handle survey form submission
from flask import Flask, request, jsonify, url_for
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

@app.route('/submit-survey', methods=['POST'])
def submit_survey():
    try:
        # Get JSON data from the request
        data = request.get_json()
        responses = data.get('responses')
        if not responses:
            return jsonify({"message": "No responses found"}), 400

        # Path to the XML file
        xml_file_path = os.path.join(os.path.dirname(__file__), 'survey_responses.xml')

        # Print to verify the path
        print("XML File Path:", xml_file_path)

        # Check if the XML file exists and is not empty
        if os.path.exists(xml_file_path) and os.path.getsize(xml_file_path) > 0:
            tree = parse(xml_file_path)
            root = tree.getroot()
        else:
            # Create the root structure if the file is empty or doesn't exist
            root = Element('SurveyResponses')
            tree = ElementTree(root)
            with open(xml_file_path, 'wb') as xml_file:
                tree.write(xml_file)

        # Add new responses to the XML
        for response in responses:
            response_element = SubElement(root, 'Response')
            id_element = SubElement(response_element, 'ID')
            id_element.text = str(len(root.findall('Response')) + 1)  # Incremental ID
            question_id_element = SubElement(response_element, 'QuestionID')
            question_id_element.text = str(response['questionId'])
            user_response_element = SubElement(response_element, 'UserResponse')
            user_response_element.text = response['userResponse']

        # Convert to pretty XML string
        xml_str = tostring(root)
        pretty_xml_str = parseString(xml_str).toprettyxml(indent="  ")

        # Write the updated XML content to the file
        with open(xml_file_path, 'w', encoding='utf-8') as xml_file:
            xml_file.write(pretty_xml_str)

        # Confirm data is saved in SQL database as well
        for response in responses:
            survey_response = SurveyResponses(
                question_id=response['questionId'],
                user_response=response['userResponse']
            )
            db.session.add(survey_response)

        db.session.commit()

        return jsonify({"redirect": url_for('thank_you')}), 200

    except Exception as e:
        print(f"Error saving survey responses: {e}")
        db.session.rollback()
        return jsonify({"message": "Failed to submit survey"}), 500

# Thank you page
@app.route('/thankyou')
def thank_you():
    return render_template('thankyou.html')


def load_question_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
        questions = data['questions']
        question_texts = {i+1: question['question'] for i, question in enumerate(questions)}
    return question_texts

@app.route('/upload', methods=['GET'])
def upload():
    return render_template('upload_form.html')

@app.route('/upload-file', methods=['POST'])
def upload_file():
    # Load question data
    question_file_path = r'C:\Users\anant\Desktop\Ananthu\4-MCA\SEM-1\4-ADBMS\Project\backend\data\data.json'
    question_texts = load_question_data(question_file_path)

    if 'fileUpload' not in request.files:
        return jsonify({"message": "No file uploaded"}), 400

    file = request.files['fileUpload']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    if file:
        try:
            # Read the Excel file into a DataFrame
            df = pd.read_excel(file, engine='openpyxl')

            # Check for required columns
            if not all(col in df.columns for col in ['question_id', 'question_text', 'yes_count', 'no_count', 'neutral_count']):
                return jsonify({"message": "Invalid Excel format. Please check the column names."}), 400

            # Plotting the data
            plt.figure(figsize=(14, 7))
            df.set_index('question_id')[['yes_count', 'no_count', 'neutral_count']].plot(kind='bar', ax=plt.gca(), colormap='viridis')

            plt.title('Survey Results')
            plt.xlabel('Question Number')
            plt.ylabel('Counts')
            plt.xticks(ticks=range(1, len(df) + 1), labels=df['question_id'], rotation=45, ha='right')

            # Place the legend outside the plot
            plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3)

            # Save the plot to a BytesIO object
            img_stream = io.BytesIO()
            plt.tight_layout()
            plt.savefig(img_stream, format='png')
            img_stream.seek(0)

            # Convert the image to base64 for embedding in HTML
            chart_img_base64 = base64.b64encode(img_stream.getvalue()).decode('utf-8')

            # Render the template with the base64-encoded image and question texts
            return render_template('upload_success.html', chart_img=chart_img_base64, question_texts=question_texts)

        except Exception as e:
            print(f"Error processing file: {e}")
            return jsonify({"message": "Error processing the Excel file"}), 500
        
# Main page
@app.route('/')
def index():
    return render_template('index.html')

# Admin page
@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/visualization')
def visualization():
    try:
        # Fetch the data from the database for visualization
        analysis_data = db.session.query(
            SurveyQuestions.question_id,
            SurveyQuestions.question_text,
            db.func.sum(db.case((SurveyResponses.user_response == 'Yes', 1), else_=0)).label('yes_count'),
            db.func.sum(db.case((SurveyResponses.user_response == 'No', 1), else_=0)).label('no_count'),
            db.func.sum(db.case((SurveyResponses.user_response == 'Neutral', 1), else_=0)).label('neutral_count')
        ).outerjoin(SurveyResponses, SurveyQuestions.question_id == SurveyResponses.question_id) \
         .group_by(SurveyQuestions.question_id).all()

        analysis_list = [
            {
                "question_id": data.question_id,
                "question_text": data.question_text,
                "yes_count": data.yes_count,
                "no_count": data.no_count,
                "neutral_count": data.neutral_count
            }
            for data in analysis_data
        ]

        return render_template('datavisualization.html', analysis_data=analysis_list)

    except Exception as e:
        print(f"Error rendering visualization page: {e}")
        return render_template('datavisualization.html', analysis_data=[])


@app.route('/analysis')
def analysis():
    try:
        # Corrected query using positional arguments for the 'case' function
        analysis_data = db.session.query(
            SurveyQuestions.question_id,
            SurveyQuestions.question_text,
            db.func.sum(db.case((SurveyResponses.user_response == 'Yes', 1), else_=0)).label('yes_count'),
            db.func.sum(db.case((SurveyResponses.user_response == 'No', 1), else_=0)).label('no_count'),
            db.func.sum(db.case((SurveyResponses.user_response == 'Neutral', 1), else_=0)).label('neutral_count')
        ).outerjoin(SurveyResponses, SurveyQuestions.question_id == SurveyResponses.question_id) \
         .group_by(SurveyQuestions.question_id).all()

        # Prepare data for rendering
        analysis_list = [
            {
                "question_id": data.question_id,
                "question_text": data.question_text,
                "yes_count": data.yes_count,
                "no_count": data.no_count,
                "neutral_count": data.neutral_count
            }
            for data in analysis_data
        ]

        return render_template('analysis.html', analysis_data=analysis_list)

    except Exception as e:
        print(f"Error rendering analysis page: {e}")
        return render_template('analysis.html', analysis_data=[])

@app.route('/export-to-excel')
def export_to_excel():
    try:
        # Query the data from the database
        analysis_data = db.session.query(
            SurveyQuestions.question_id,
            SurveyQuestions.question_text,
            db.func.sum(db.case((SurveyResponses.user_response == 'Yes', 1), else_=0)).label('yes_count'),
            db.func.sum(db.case((SurveyResponses.user_response == 'No', 1), else_=0)).label('no_count'),
            db.func.sum(db.case((SurveyResponses.user_response == 'Neutral', 1), else_=0)).label('neutral_count')
        ).outerjoin(SurveyResponses, SurveyQuestions.question_id == SurveyResponses.question_id) \
         .group_by(SurveyQuestions.question_id).all()

        # Convert query results to a list of dictionaries
        analysis_list = [
            {
                "question_id": data.question_id,
                "question_text": data.question_text,
                "yes_count": data.yes_count,
                "no_count": data.no_count,
                "neutral_count": data.neutral_count
            }
            for data in analysis_data
        ]

        # Convert the analysis data to a DataFrame
        df = pd.DataFrame(analysis_list)

        # Specify the path to save the Excel file
        excel_file_path = os.path.join(os.path.dirname(__file__), 'survey_analysis.xlsx')

        # Save the DataFrame to an Excel file
        df.to_excel(excel_file_path, index=False, engine='openpyxl')

        # Send the Excel file as a response to download
        return send_file(excel_file_path, as_attachment=True, download_name='survey_analysis.xlsx')

    except Exception as e:
        print(f"Error exporting data to Excel: {e}")
        return jsonify({"message": "Failed to export data to Excel"}), 500

    
if __name__ == '__main__':  # Corrected the entry point
    app.run(debug=True)
