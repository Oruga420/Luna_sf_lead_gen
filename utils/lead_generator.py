from openai import OpenAI
import os
import json
import logging
import re

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_leads(form_fields, num_leads, inspiration, use_case):
    batch_size = 10
    leads = []
    for i in range(0, num_leads, batch_size):
        batch_num_leads = min(batch_size, num_leads - i)
        batch_leads = generate_lead_batch(form_fields, batch_num_leads, inspiration, use_case)
        leads.extend(batch_leads)
        logger.info(f"Generated batch of {len(batch_leads)} leads. Total leads: {len(leads)}/{num_leads}")
    return leads

def generate_lead_batch(form_fields, num_leads, inspiration, use_case):
    field_descriptions = ", ".join([f"{field['name']} ({field['type']})" for field in form_fields])
    
    prompt = f'''Generate {num_leads} realistic leads for a Salesforce Web-to-Lead form with the following fields:
    {field_descriptions}

    {'If a TV show or movie is specified, use a variety of different characters from it to create diverse leads. TV show or movie: ' + inspiration if inspiration else 'Create realistic fictional people'}

    Consider the following use case when generating the leads: {use_case}

    Provide the response as multiple JSON objects, each representing a single lead with field names as keys.'''

    try:
        logger.info(f"Sending request to OpenAI API for {num_leads} leads")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3000
        )
        
        content = response.choices[0].message.content
        logger.info(f"Received response from OpenAI API: {content[:100]}...")

        # Extract all JSON objects from the content using regex
        json_matches = re.findall(r'\{[^{}]*\}', content, re.DOTALL)
        if json_matches:
            leads = []
            for json_str in json_matches:
                try:
                    lead_data = json.loads(json_str)
                    leads.append(lead_data)
                except json.JSONDecodeError as json_error:
                    logger.error(f"Error parsing JSON: {str(json_error)}")
                    logger.error(f"Problematic JSON string: {json_str}")
            
            if leads:
                return leads
            else:
                raise ValueError("No valid JSON objects found in the API response")
        else:
            logger.error("No JSON objects found in the API response")
            logger.error(f"Raw content: {content}")
            raise ValueError(f"No JSON objects found in the API response. Raw content: {content}")

    except Exception as e:
        logger.error(f"Error generating lead data: {str(e)}")
        raise ValueError(f"Error generating lead data: {str(e)}")
