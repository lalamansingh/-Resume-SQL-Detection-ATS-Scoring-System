import os
import sys
import logging
import argparse

from resume_parser import parse_resume
from sql_injection_detector import SQLInjectionDetector
from ats_scorer import ATSScorer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Detect SQL injection in resumes and compute ATS score.')
    parser.add_argument('resume_file', help='Path to the resume file (PDF, DOCX, TXT)')
    parser.add_argument('--job_desc', help='Path to job description file (TXT) for semantic similarity scoring', default=None)
    parser.add_argument('--output', help='Output file to save results (JSON format)', default=None)
    parser.add_argument('--no_sanitize', action='store_true', help='Do not sanitize SQL injection (only detect)')
    args = parser.parse_args()

    logger.info(f"Processing resume: {args.resume_file}")
    logger.info(f"Job description provided: {args.job_desc is not None}")

    # Step 1: Parse resume
    try:
        resume_text = parse_resume(args.resume_file)
        logger.info(f"Resume text extracted, length: {len(resume_text)} characters")
    except Exception as e:
        logger.error(f"Failed to parse resume: {e}")
        sys.exit(1)

    # Step 2: Detect and optionally sanitize SQL injection
    detector = SQLInjectionDetector()
    is_malicious, matches = detector.detect(resume_text)
    logger.info(f"SQL injection detected: {is_malicious}")
    if matches:
        logger.info(f"Matches found: {matches}")

    if is_malicious and not args.no_sanitize:
        logger.info("Sanitizing resume text...")
        sanitized_text = detector.sanitize(resume_text)
        # Optionally, we could log how much was removed
        removed_chars = len(resume_text) - len(sanitized_text)
        logger.info(f"Removed {removed_chars} characters during sanitization.")
        text_to_score = sanitized_text
    else:
        text_to_score = resume_text
        if is_malicious:
            logger.warning("SQL injection detected but not sanitizing (as per --no_sanitize flag).")
        else:
            logger.info("No SQL injection detected.")

    # Step 3: Compute ATS score
    job_description = None
    if args.job_desc:
        if os.path.exists(args.job_desc):
            try:
                with open(args.job_desc, 'r', encoding='utf-8') as f:
                    job_description = f.read()
                logger.info(f"Job description loaded from {args.job_desc}, length: {len(job_description)} characters")
            except Exception as e:
                logger.error(f"Failed to read job description: {e}")
                # Continue without job description
        else:
            logger.warning(f"Job description file not found: {args.job_desc}")

    scorer = ATSScorer()
    scores = scorer.score_resume(text_to_score, job_description)
    logger.info(f"ATS scores computed: {scores}")

    # Step 4: Output results
    result = {
        'resume_file': args.resume_file,
        'sql_injection_detected': is_malicious,
        'sql_injection_matches': matches,
        'sanitized': not args.no_sanitize and is_malicious,
        'ats_scores': scores,
        'ats_score_percentage': scores['overall'] * 100
    }

    if args.output:
        import json
        try:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Results saved to {args.output}")
        except Exception as e:
            logger.error(f"Failed to write output file: {e}")
    else:
        # Print to stdout
        import json
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()