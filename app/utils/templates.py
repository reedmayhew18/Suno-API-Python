"""
Load YAML-based templates for chat rendering.
"""
import os
import yaml
from jinja2 import Template
from app.config import settings

# Mapping of template name to Jinja2 Template
templates = {}

def load_templates():
    """
    Walk through the configured template directory, parse YAML files,
    and compile each string as a Jinja2 template.
    """
    base_dir = settings.chat_template_dir
    if not base_dir or not os.path.isdir(base_dir):
        return
    for root, _, files in os.walk(base_dir):
        for file in files:
            if not file.lower().endswith(('.yaml', '.yml')):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                data = yaml.safe_load(content)
                if not isinstance(data, dict):
                    continue
                for name, tmpl in data.items():
                    if isinstance(tmpl, str) and tmpl.strip():
                        templates[name] = Template(tmpl)
            except Exception:
                # Skip invalid or unparsable files
                continue