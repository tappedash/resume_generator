# Professional Resume Generator

A Python-based resume generator that uses Jinja2 templates and LaTeX to create professional, beautifully formatted CVs. Maintain your resume content in a simple YAML file while generating polished PDF output.

## Features

- Easy-to-edit YAML format for resume content
- Professional LaTeX-based PDF output
- Customizable template with support for:
  - Work experience with detailed bullet points
  - Education history
  - Skills categorization
  - Language proficiency
  - Profile photo

## Quick Start

1. **Install Dependencies**
   ```bash
   # Install Python requirements
   pip install -r src/requirements.txt
   
   # Install LaTeX distribution:
   # - macOS: brew install --cask mactex-no-gui
   # - Windows: Install MiKTeX from https://miktex.org/download
   ```

2. **Edit Your Resume**
   - Update `latex/resume_data.yaml` with your information
   - Add your photo as `latex/picture.jpeg`

3. **Generate PDF**
   ```bash
   python src/generate_resume.py
   # Output: latex/resume.pdf
   ```

## Project Structure

```
.
├── src/                    # Python code
│   ├── generate_resume.py  # Main script
│   └── requirements.txt    # Python dependencies
└── latex/                  # LaTeX files
    ├── resume.pdf          # Generated PDF
    ├── resume.tex          # Generated LaTeX
    ├── resume_template.tex.j2  # Jinja2 template
    ├── resume_data.yaml    # Your resume content (edit this)
    ├── altacv.cls          # LaTeX class
    └── picture.jpeg        # Your profile photo
```

## Customization

### Content
- Edit `latex/resume_data.yaml` to update your information
- The YAML file is organized into logical sections

### Design
- Modify `latex/resume_template.tex.j2` for layout changes
- Adjust colors and fonts in the template
- Uses the AltaCV LaTeX class

### Profile Photo
1. Place your photo in the `latex` directory
2. Update the `photo` field in `resume_data.yaml`
3. Supported formats: JPG, PNG, or PDF

## Troubleshooting

### Common Issues

1. **Missing LaTeX packages**
   - **Error**: `File '<package>.sty' not found`
   - **Fix**: Install missing packages:
     - macOS: `sudo tlmgr install <package-name>`
     - Windows: Use MiKTeX Console

2. **Python errors**
   - **Error**: `ModuleNotFoundError`
   - **Fix**: `pip install -r src/requirements.txt`

3. **Font issues**
   - Ensure Lato font is installed or modify the template

## License

Based on [AltaCV](https://github.com/liantze/AltaCV) by LianTze Lim (Apache 2.0)

## Customization

- **Update Content**: Edit `latex/resume_data.yaml`
- **Change Styling**: Modify `latex/resume_template.tex.j2`
- **Update LaTeX Class**: Edit `latex/altacv.cls`

## Notes

- The template is based on AltaCV by LianTze Lim (liantze@gmail.com)
- Original AltaCV documentation is available in the `latex` directory

## Requirements and Compilation

- A complete LaTeX installation is required (e.g., TeX Live, MiKTeX, or MacTeX)
- The following LaTeX packages are required:
  - `fontawesome5` - For icons
  - `tcolorbox` - For colored boxes and frames
  - `enumitem` - For customizing lists
  - `paracol` - For multi-column layouts
  - `lato` - The default font (or any other font of your choice)
  - `biblatex` - For publications and references

## Troubleshooting

1. **Missing LaTeX packages**:
   - If you get errors about missing `.sty` files, install the required packages using your LaTeX distribution's package manager:
     - For TeX Live: `tlmgr install <package-name>`
     - For MiKTeX: Use the MiKTeX Console to install missing packages

2. **Photo not found**:
   - Ensure the photo file exists in the `latex` directory
   - Check the filename in `resume_data.yaml` matches exactly (including extension)
   - Supported formats: JPG, PNG, or PDF

3. **Font issues**:
   - If you get font-related errors, install the Lato font package
   - Alternatively, modify the template to use a different font by editing the font settings in the template

## License

This project is based on [AltaCV](https://github.com/liantze/AltaCV) by LianTze Lim, which is licensed under the [Apache License 2.0](https://github.com/liantze/AltaCV/blob/main/LICENSE).

## Contributing

Contributions are welcome! If you'd like to contribute, please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## Acknowledgements

- [AltaCV](https://github.com/liantze/AltaCV) - The LaTeX template this project is based on
- [Jinja2](https://palletsprojects.com/p/jinja/) - For powerful template rendering
- [PyYAML](https://pyyaml.org/) - For YAML parsing and data serialization

## Advanced Configuration

### Layout Options

- Use the `normalphoto` option to get normal (non-circular) photos
- Customize colors and fonts through the template configuration
- The `withhyper` document class option makes personal info fields clickable hyperlinks
- Supports multiple LaTeX engines: pdflatex, XeLaTeX, and LuaLaTeX
- Uses Lato font by default, but can be customized

### Example LaTeX Configuration

Here's a minimal example of how to use the template in your LaTeX file:

```latex
\documentclass[10pt,a4paper,ragged2e,withhyper]{altacv}

% Page layout
\geometry{left=1.25cm, right=1.25cm, top=1.5cm, bottom=1.5cm, columnsep=1.2cm}

% For parallel columns
\usepackage{paracol}

% Start a two-column layout
\begin{document}
\begin{paracol}{2}

% Left column
\cvsection{Experience}
% Your experience items here

% Switch to right column
\switchcolumn
\cvsection{Education}
% Your education items here

\end{paracol}
\end{document}
```

### Clickable Info Fields

When using the `withhyper` option, personal info fields become clickable hyperlinks. For example, `\email{example@example.com}` will create a clickable email link.

You can customize the hyperlink behavior by redefining the following commands:

```latex
% Change the hyperlink prefix (defaults to https://)
\renewcommand{\homepagehyperprefix}{http://}

% Change the symbol used for homepages
\renewcommand{\homepagesymbol}{\faLink}
```

## Adding Custom Fields

You can add custom information fields using these methods:

### Using `\printinfo`

```latex
\printinfo{\faGithub}{your-username}[https://github.com/]
```

### Defining a New Field

```latex
\NewInfoField{github}{\faGithub}[https://github.com/]
\github{your-username}
```

### Custom Icons and Colors

You can customize various aspects of the template:

#### Colors
```latex
\colorlet{accent}{blue!70!black}
\colorlet{heading}{black}
```

#### Fonts
```latex
\renewcommand{\namefont}{\Huge\bfseries}
\renewcommand{\taglinefont}{\large\bfseries}
```

#### Icons
```latex
\renewcommand{\cvItemMarker}{\textbullet}
\renewcommand{\cvRatingMarker}{\faCircle}
```

### ATS Compatibility

This template includes features to improve compatibility with Applicant Tracking Systems (ATS):
- Icons include alternative text for screen readers
- Uses semantic LaTeX markup
- Generates clean text output with `pdftotext`

For best results, test your generated PDF with:
```bash
pdftotext -layout resume.pdf
```

## Need More Help?

For advanced customization options, refer to the [AltaCV documentation](https://github.com/liantze/AltaCV) in the `latex` directory.
