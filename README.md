# Resume SQL Detection Model

This project provides a model to detect SQL injection in resumes and compute an ATS (Applicant Tracking System) score.

## Features

- **Resume Parsing**: Extract text from PDF, DOCX, and TXT files.
- **SQL Injection Detection**: Identify potential SQL injection attempts using rule-based regex patterns.
- **Text Sanitization**: Remove detected SQL injection patterns to sanitize resume input.
- **ATS Scoring**: Evaluate how well a resume would perform in an ATS based on:
  - Section presence (contact, experience, experience, education, skills)
  - Keyword density (ATS-relevant keywords)
  - Resume length
  - Optional semantic similarity with a job description (using sentence-transformers)

## Installation

1. Clone or copy this repository to your local machine.
2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   Note: You may need to install system dependencies for pdfminer and python-docx.

## Usage

### Command Line Interface (CLI)

To analyze a resume file and detect SQL injection:

```bash
python main.py path/to/resume.pdf
```

### With Job Description for Semantic Similarity

To include semantic similarity scoring (requires a job description file):

```bash
python main.py path/to/resume.pdf --job_desc path/to/job_description.txt
```

### To Avoid Sanitization (Detection Only)

If you only want to detect SQL injection without sanitizing the text:

```bash
python main.py path/to/resume.pdf --no_sanitize
```

### Save Results to JSON

To save the results to a JSON file:

```bash
python main.py path/to/resume.pdf --output results.json
```

### Web Interface (Streamlit)

For an easy-to-use graphical interface:

```bash
streamlit run streamlit_app.py
```

This will open a web browser at `http://localhost:8501` where you can:
- Upload resume files (PDF, DOCX, TXT)
- Optionally upload a job description file
- Choose whether to sanitize SQL injection
- View the results: SQL injection detection, ATS scores, etc.
- Download results as JSON

## Output

The program outputs a JSON object with the following fields:

- `resume_file`: Path to the processed resume file.
- `sql_injection_detected`: Boolean indicating if SQL injection was detected.
- `sql_injection_matches`: List of detected SQL injection patterns.
- `sanitized`: Boolean indicating if the text was sanitized (only if detection was positive and `--no_sanitize` was not used).
- `ats_scores`: Dictionary containing individual scores:
  - `section_presence`: Score based on presence of standard resume sections.
  - `keyword_density`: Score based on density of ATS-relevant keywords.
  - `length`: Score based on resume length (ideal around 400-800 words).
  - `semantic_similarity`: Score based on semantic similarity with job description (if provided).
- `ats_score_percentage`: Overall ATS score as a percentage (0-100).

## Example

```bash
$ python main.py sample_resume.pdf --job_desc sample_job.txt --output result.json
{
  "resume_file": "sample_resume.pdf",
  "sql_injection_detected": false,
  "sql_injection_matches": [],
  "sanitized": false,
  "ats_scores": {
    "section_presence": 0.75,
    "keyword_density": 0.6,
    "length": 0.9,
    "semantic_similarity": 0.85
  },
  "ats_score_percentage": 78.0
}
```

## Customization

- **SQL Injection Detection**: Modify `sql_injection_detector.py` to add/remove regex patterns or adjust the whitelist.
- **ATS Scoring**: Adjust weights in `ats_scorer.py` or modify the keyword list and section definitions.
- **Resume Parsing**: Extend `resume_parser.py` to support additional file formats.

## License

MIT

## Disclaimer

This tool is for educational purposes and should not be relied upon for production use without thorough testing and validation. SQL injection detection via regex is not foolproof and should be complemented with other security measures. ATS scoring is a heuristic and may not reflect actual ATS behavior.