import requests
from lxml import html

def submit_leads_to_salesforce(web_to_lead_html, generated_leads):
    try:
        tree = html.fromstring(web_to_lead_html)
        form = tree.xpath('//form')[0]
        action_url = form.get('action')
        
        results = []
        for lead in generated_leads:
            data = {**lead}  # Create a copy of the lead data
            
            # Add any hidden fields from the original form
            for hidden_input in form.xpath('.//input[@type="hidden"]'):
                name = hidden_input.get('name')
                value = hidden_input.get('value')
                if name and value:
                    data[name] = value
            
            response = requests.post(action_url, data=data)
            results.append({
                'success': response.status_code == 200,
                'status_code': response.status_code
            })
        
        return results
    except Exception as e:
        raise ValueError(f"Error submitting leads to Salesforce: {str(e)}")
