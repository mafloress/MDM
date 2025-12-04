import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pyairtable import Api
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')

# Configuration
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME', 'Clients')
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL')

# Mock User for Login
USERS = {
    "admin": "password123"
}

def get_airtable_table():
    if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
        return None
    api = Api(AIRTABLE_API_KEY)
    return api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('kanban'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in USERS and USERS[username] == password:
            session['user'] = username
            return redirect(url_for('kanban'))
        flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/kanban')
def kanban():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    table = get_airtable_table()
    if not table:
        # Return mock data if no API key configured
        clients = [
            {'id': '1', 'fields': {'Name': 'Juan Perez', 'Status': 'INVITACIÓN', 'Company': 'Tech Corp'}},
            {'id': '2', 'fields': {'Name': 'Maria Garcia', 'Status': 'ACEPTADO', 'Company': 'Eventos MX'}},
            {'id': '3', 'fields': {'Name': 'Carlos Lopez', 'Status': 'EN ESPERA', 'Company': 'Global Congress'}},
            {'id': '4', 'fields': {'Name': 'Ana Silva', 'Status': 'VALIDACIÓN DOCTOS', 'Company': 'Travel Inc'}},
            {'id': '5', 'fields': {'Name': 'Pedro Ruiz', 'Status': 'ACEPTADOS', 'Company': 'Mega Events'}}
        ]
    else:
        try:
            clients = table.all()
        except Exception as e:
            flash(f"Error connecting to Airtable: {e}", 'error')
            clients = []

    # Group by Status
    pools = {
        'INVITACIÓN': [],
        'ACEPTADO': [],
        'EN ESPERA': [],
        'VALIDACIÓN DOCTOS': [],
        'ACEPTADOS': []
    }
    
    for client in clients:
        status = client['fields'].get('Status', 'INVITACIÓN')
        if status in pools:
            pools[status].append(client)
        else:
            # Fallback for unknown statuses
            pools['INVITACIÓN'].append(client)

    return render_template('kanban.html', pools=pools)

@app.route('/add_client', methods=['POST'])
def add_client():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.form
    table = get_airtable_table()
    
    if table:
        table.create({
            'Name': data.get('name'),
            'Email': data.get('email'),
            'Company': data.get('company'),
            'Status': 'INVITACIÓN'
        })
    
    return redirect(url_for('kanban'))

@app.route('/upload_document/<client_id>', methods=['POST'])
def upload_document(client_id):
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    # In a real app, you would upload to S3/Cloudinary and then save the URL to Airtable
    # Or use Airtable's attachment API (requires URL)
    # For this demo, we'll simulate the action
    flash('Document uploaded successfully (Simulation)', 'success')
    return redirect(url_for('kanban'))

@app.route('/trigger_invitations', methods=['POST'])
def trigger_invitations():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    category_id = request.form.get('categoryId')
    template_id = request.form.get('templateId')
    
    # URL for the new Invitation Webhook (Workflow 4)
    # Assuming a different endpoint or the same base URL with a different path
    # The JSON F4 has path "send-invitations"
    webhook_url = os.getenv('N8N_INVITE_WEBHOOK_URL') 
    
    if webhook_url:
        try:
            requests.post(webhook_url, json={'categoryId': category_id, 'templateId': template_id})
            flash('Invitation process started via n8n!', 'success')
        except Exception as e:
            flash(f'Error triggering n8n: {e}', 'error')
    else:
        flash('n8n Invite Webhook URL not configured', 'warning')
        
    return redirect(url_for('kanban'))

@app.route('/trigger_scraping', methods=['POST'])
def trigger_scraping():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    criteria = request.form.get('criteria')
    
    if N8N_WEBHOOK_URL:
        try:
            requests.post(N8N_WEBHOOK_URL, json={'criteria': criteria, 'action': 'scrape'})
            flash('Scraping process started via n8n!', 'success')
        except Exception as e:
            flash(f'Error triggering n8n: {e}', 'error')
    else:
        flash('n8n Webhook URL not configured', 'warning')
        
    return redirect(url_for('kanban'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
