#!/usr/bin/env python3
"""
Resume Generator

This script generates a LaTeX resume from a YAML file using a Jinja2 template.
"""

import os
import yaml
import subprocess
from jinja2 import Environment, FileSystemLoader

def load_yaml_data(yaml_file):
    """Load data from YAML file."""
    with open(yaml_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def render_template(template_path, output_path, context):
    """Render Jinja2 template with the given context."""
    template_dir = os.path.dirname(template_path)
    template_file = os.path.basename(template_path)
    
    env = Environment(
        loader=FileSystemLoader(template_dir),
        block_start_string='<%%',
        block_end_string='%%>',
        variable_start_string='<<',
        variable_end_string='>>',
        comment_start_string='<#',
        comment_end_string='#>',
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
        extensions=['jinja2.ext.loopcontrols']
    )
    
    # Add custom filters
    def escape_latex(text):
        if text is None:
            return ''
        if not isinstance(text, str):
            text = str(text)
        text = text.replace('\\', '\\\\')
        text = text.replace('{', '\\{')
        text = text.replace('}', '\\}')
        text = text.replace('&', '\\&')
        text = text.replace('%', '\\%')
        text = text.replace('$', '\\$')
        text = text.replace('#', '\\#')
        text = text.replace('_', '\\_')
        text = text.replace('^', '\\^')
        return text
    
    env.filters['escape_latex'] = escape_latex
    
    template = env.get_template(template_file)
    output = template.render(**context)
    
    # Clean up any double backslashes that might have been added
    output = output.replace('\\\\\\\\', '\\\\')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)

def compile_latex(tex_file):
    """Compile LaTeX file to PDF."""
    try:
        # Run pdflatex
        subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', tex_file],
            cwd=os.path.dirname(tex_file),
            check=True
        )
        print(f"Successfully generated PDF at {os.path.splitext(tex_file)[0]}.pdf")
    except subprocess.CalledProcessError as e:
        print(f"Error compiling LaTeX: {e}")
        raise

def main():
    # File paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    latex_dir = os.path.join(base_dir, 'latex')
    
    yaml_file = os.path.join(latex_dir, 'resume_data.yaml')
    template_file = os.path.join(latex_dir, 'resume_template.tex.j2')
    output_tex = os.path.join(latex_dir, 'resume.tex')
    
    # Ensure output directory exists
    os.makedirs(latex_dir, exist_ok=True)
    
    # Load data and render template
    context = load_yaml_data(yaml_file)
    print(f"Loaded context: {context.keys()}")
    
    render_template(template_file, output_tex, context)
    
    # Compile LaTeX to PDF
    compile_latex(output_tex)

if __name__ == "__main__":
    main()
