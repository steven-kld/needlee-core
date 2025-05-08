from entities.gen_interview import generate_interview_from_text, generate_interview_from_questions

class InterviewGenerator:
    def __init__(self, org_id):
        self.org_id = org_id
        self.language = None
        self.display_name = None
        self.description_text = None
        self.thank_you_text = None
        self.questions = []

    def from_raw_text(self, raw_text):
        result = generate_interview_from_text(raw_text)
        if not result:
            raise ValueError("Interview generation failed")
        self._apply_result(result)
        return self

    def from_questions(self, questions):
        result = generate_interview_from_questions(questions)
        if not result:
            raise ValueError("Question-based generation failed")
        self._apply_result(result)
        return self

    def _apply_result(self, result):
        self.language = result["language"]
        self.display_name = result["display_name"]
        self.description_text = result["description"]
        self.thank_you_text = result["thank_you_text"]
        self.questions = result["questions"]

    def to_dict(self):
        return {
            "language": self.language,
            "display_name": self.display_name,
            "description_text": self.description_text,
            "thank_you_text": self.thank_you_text,
            "questions": self.questions
        }
