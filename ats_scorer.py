import re
import logging
from typing import List, Dict, Optional
import numpy as np

# Try to import sentence-transformers for semantic similarity
try:
    from sentence_transformers import SentenceTransformer, util
    import torch
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not installed. Semantic similarity scoring will be disabled.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ATSScorer:
    def __init__(self):
        # Define common sections to look for in a resume
        self.sections = {
            'contact': ['email', 'phone', 'address', 'linkedin', 'github'],
            'experience': ['experience', 'work history', 'employment', 'professional experience'],
            'education': ['education', 'academic background', 'qualifications'],
            'skills': ['skills', 'technical skills', 'competencies', 'expertise'],
            'summary': ['summary', 'profile', 'objective', 'professional summary']
        }
        # Compile regex patterns for section detection (case-insensitive)
        self.section_patterns = {}
        for section, keywords in self.sections.items():
            pattern = r'\b(' + '|'.join(keywords) + r')\b'
            self.section_patterns[section] = re.compile(pattern, re.IGNORECASE)

        # Common ATS keywords (hard skills, job titles, etc.) - this is a simplified list
        # In practice, this should be tailored to the job description or industry.
        self.at_keywords = [
            'management', 'leadership', 'communication', 'problem solving', 'teamwork',
            'project management', 'data analysis', 'sql', 'python', 'java', 'javascript',
            'html', 'css', 'react', 'angular', 'node.js', 'aws', 'azure', 'cloud',
            'machine learning', 'ai', 'analytics', 'reporting', 'budget', 'finance',
            'marketing', 'sales', 'customer service', 'operations', 'supply chain'
        ]
        self.keyword_pattern = re.compile(r'\b(' + '|'.join(self.at_keywords) + r')\b', re.IGNORECASE)

        # Initialize sentence transformer model if available
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded sentence-transformers model: all-MiniLM-L6-v2")
        else:
            self.model = None

    def _score_section_presence(self, text: str) -> float:
        """
        Score based on presence of standard resume sections.
        Returns a score between 0 and 1.
        """
        found_sections = 0
        for section, pattern in self.section_patterns.items():
            if pattern.search(text):
                found_sections += 1
        # Normalize by number of sections we look for
        score = found_sections / len(self.sections)
        logger.info(f"Section presence score: {score:.2f} (found {found_sections}/{len(self.sections)} sections)")
        return score

    def _score_keyword_density(self, text: str) -> float:
        """
        Score based on density of ATS-relevant keywords.
        Returns a score between 0 and 1.
        """
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return 0.0
        keyword_matches = self.keyword_pattern.findall(text.lower())
        density = len(keyword_matches) / len(words)
        # Normalize density to a 0-1 score (assuming max density of 0.3 is excellent)
        # We'll use a sigmoid-like normalization, but for simplicity, we'll cap at 0.3
        score = min(density / 0.3, 1.0)
        logger.info(f"Keyword density score: {score:.2f} (density: {density:.4f})")
        return score

    def _score_length(self, text: str) -> float:
        """
        Score based on resume length (word count).
        Ideal resume length is around 400-800 words.
        Returns a score between 0 and 1.
        """
        word_count = len(re.findall(r'\b\w+\b', text))
        if word_count < 100:
            score = word_count / 100  # Linear increase from 0 to 1 as words go from 0 to 100
        elif word_count > 1000:
            score = max(0.0, 1.0 - (word_count - 1000) / 1000)  # Decrease after 1000 words
        else:
            # Between 100 and 1000 words, we give a score that peaks at 600 words
            # Using a triangular shape: score = 1 - |word_count - 600| / 400, clamped to 0-1
            score = 1.0 - abs(word_count - 600) / 400.0
            score = max(0.0, min(score, 1.0))
        logger.info(f"Length score: {score:.2f} (word count: {word_count})")
        return score

    def _score_semantic_similarity(self, resume_text: str, job_description: str) -> float:
        """
        Score based on semantic similarity between resume and job description.
        Returns a score between 0 and 1 (cosine similarity).
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE or self.model is None:
            logger.warning("Sentence transformer model not available. Returning 0.0 for semantic similarity.")
            return 0.0
        if not job_description.strip():
            return 0.0
        try:
            # Encode both texts
            resume_embedding = self.model.encode(resume_text, convert_to_tensor=True)
            job_embedding = self.model.encode(job_description, convert_to_tensor=True)
            # Compute cosine similarity
            cosine_score = util.pytorch_cos_sim(resume_embedding, job_embedding)
            score = cosine_score.item()
            logger.info(f"Semantic similarity score: {score:.2f}")
            return score
        except Exception as e:
            logger.error(f"Error computing semantic similarity: {e}")
            return 0.0

    def score_resume(self, resume_text: str, job_description: Optional[str] = None) -> Dict[str, float]:
        """
        Compute ATS score for a resume.
        Returns a dictionary with individual scores and overall score.
        """
        # Section presence score
        section_score = self._score_section_presence(resume_text)
        # Keyword density score
        keyword_score = self._score_keyword_density(resume_text)
        # Length score
        length_score = self._score_length(resume_text)

        scores = {
            'section_presence': section_score,
            'keyword_density': keyword_score,
            'length': length_score
        }

        # If job description is provided, add semantic similarity
        if job_description is not None:
            semantic_score = self._score_semantic_similarity(resume_text, job_description)
            scores['semantic_similarity'] = semantic_score
            # Overall score: weighted average (weights can be adjusted)
            overall = (
                0.3 * section_score +
                0.3 * keyword_score +
                0.2 * length_score +
                0.2 * semantic_score
            )
        else:
            # Overall score without semantic similarity
            overall = (
                0.4 * section_score +
                0.4 * keyword_score +
                0.2 * length_score
            )
        scores['overall'] = overall

        logger.info(f"ATS scores: {scores}")
        return scores

    def get_ats_score_percentage(self, resume_text: str, job_description: Optional[str] = None) -> float:
        """
        Returns the overall ATS score as a percentage (0-100).
        """
        scores = self.score_resume(resume_text, job_description)
        return scores['overall'] * 100

if __name__ == "__main__":
    # Example usage
    scorer = ATSScorer()
    sample_resume = """
    John Doe
    Email: john.doe@example.com
    Phone: 555-123-4567

    SUMMARY
    Experienced software engineer with 5 years of experience in web development.

    EXPERIENCE
    Software Engineer at ABC Corp (2020-Present)
    - Developed web applications using JavaScript, React, and Node.js.
    - Collaborated with cross-functional teams to deliver projects on time.

    EDUCATION
    Bachelor of Science in Computer Science
    XYZ University, 2015-2019

    SKILLS
    JavaScript, React, Node.js, HTML, CSS, SQL, Python
    """
    job_desc = """
    We are looking for a Software Engineer with experience in JavaScript, React, and Node.js.
    The ideal candidate should have a strong background in web development and be able to work in a team environment.
    """
    scores = scorer.score_resume(sample_resume, job_desc)
    print("Scores:", scores)
    print(f"Overall ATS Score: {scorer.get_ats_score_percentage(sample_resume, job_desc):.2f}%")