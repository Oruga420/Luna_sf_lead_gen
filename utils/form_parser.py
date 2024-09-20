from html.parser import HTMLParser
import html as html_module

try:
    from lxml import html
except ImportError:
    html = None

def parse_web_to_lead_form(web_to_lead_html):
    try:
        if html is not None:
            tree = html.fromstring(web_to_lead_html)
            form = tree.xpath('//form')[0]
            
            fields = []
            for input_element in form.xpath('.//input | .//select | .//textarea'):
                field_name = input_element.get('name')
                if field_name and not field_name.startswith('00N'):  # Exclude custom fields
                    field_type = input_element.get('type', 'text')
                    if field_type == 'hidden':
                        continue
                    fields.append({
                        'name': field_name,
                        'type': field_type
                    })
        else:
            class FormParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.fields = []
                    self.in_form = False

                def handle_starttag(self, tag, attrs):
                    if tag == 'form':
                        self.in_form = True
                    if self.in_form and tag in ['input', 'select', 'textarea']:
                        attrs_dict = dict(attrs)
                        field_name = attrs_dict.get('name')
                        if field_name and not field_name.startswith('00N'):
                            field_type = attrs_dict.get('type', 'text')
                            if field_type != 'hidden':
                                self.fields.append({
                                    'name': field_name,
                                    'type': field_type
                                })

                def handle_endtag(self, tag):
                    if tag == 'form':
                        self.in_form = False

            parser = FormParser()
            parser.feed(web_to_lead_html)
            fields = parser.fields

        return fields
    except Exception as e:
        raise ValueError(f"Error parsing Web-to-Lead form: {str(e)}")
