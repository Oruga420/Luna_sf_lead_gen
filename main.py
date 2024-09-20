from flask import Flask, render_template, request, jsonify, send_file, Response
from utils.form_parser import parse_web_to_lead_form
from utils.lead_generator import generate_leads
from utils.salesforce_submitter import submit_leads_to_salesforce
import csv
import tempfile
import logging
import json

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store generated leads temporarily
generated_leads_cache = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_leads', methods=['POST'])
def generate_leads_route():
    global generated_leads_cache
    try:
        web_to_lead_html = request.json['webToLeadHtml']
        num_leads = int(request.json['numLeads'])
        inspiration = request.json.get('inspiration', '')
        use_case = request.json.get('useCase', '')

        form_fields = parse_web_to_lead_form(web_to_lead_html)
        
        def generate_leads_with_progress():
            generated_leads = []
            for i, lead in enumerate(generate_leads(form_fields, num_leads, inspiration, use_case)):
                generated_leads.append(lead)
                progress = (i + 1) / num_leads * 100
                yield f"data: {json.dumps({'progress': progress, 'message': f'Generated {i + 1}/{num_leads} leads'})}\n\n"
            
            global generated_leads_cache
            generated_leads_cache = generated_leads
            submit_results = submit_leads_to_salesforce(web_to_lead_html, generated_leads)
            
            yield f"data: {json.dumps({'progress': 100, 'message': f'Successfully generated and submitted {len(submit_results)} leads.', 'results': submit_results})}\n\n"

        return Response(generate_leads_with_progress(), content_type='text/event-stream')

    except Exception as e:
        logger.error(f"Error in generate_leads_route: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 400

@app.route('/download_csv', methods=['GET'])
def download_csv():
    global generated_leads_cache
    if not generated_leads_cache:
        logger.error("No leads generated yet")
        return jsonify({'error': 'No leads generated yet'}), 400

    try:
        # Create a temporary file to store the CSV
        with tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', suffix='.csv') as temp_file:
            writer = csv.DictWriter(temp_file, fieldnames=generated_leads_cache[0].keys())
            writer.writeheader()
            for lead in generated_leads_cache:
                writer.writerow(lead)

        logger.info(f"CSV file created with {len(generated_leads_cache)} leads")
        # Send the temporary file as an attachment
        return send_file(temp_file.name, as_attachment=True, download_name='generated_leads.csv', mimetype='text/csv')
    except Exception as e:
        logger.error(f"Error in download_csv: {str(e)}")
        return jsonify({'error': f'Error creating CSV file: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
