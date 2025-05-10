from entities import (
    get_interview_by_id,
    get_questions_expected,
    get_respondents_reviews
)

class InterviewViewer:
    def __init__(self, org_id, interview_id):
        self.exists = False
        self.org_id = org_id
        self.interview_id = interview_id
        self.language = None
        self.display_name = None
        self.description_text = None
        self.questions = []
        self.completed = 0
        self.respondents = []
        self.err = None

        self.validate()

        if self.exists:
            self.questions = get_questions_expected(self.interview_id)
            self.respondents = get_respondents_reviews(self.interview_id)
            self.completed = len(self.respondents)

    def validate(self):
        if not self.org_id or not self.interview_id:
            self.err = ("Missing required fields", 400)
            return False
        
        interview = get_interview_by_id(self.org_id, self.interview_id)
        if not interview:
            self.err = ("Interview not found", 404)
            return False

        self.language = interview["language"]
        self.display_name = interview["display_name"]
        self.description_text = interview["description_text"]
        self.exists = True

    def to_dict(self):
        return {
            "display_name": self.display_name,
            "description_text": self.description_text,
            "language": self.language,
            "completed": self.completed,
            "respondents": self.respondents,
            "questions": self.questions
        }
