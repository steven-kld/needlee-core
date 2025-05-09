from entities.gen_interview import generate_interview_from_text, generate_interview_from_questions, prepare_interview_folder, record_interview_questions, upload_interview_audio 
from entities.interviews import create_interview_with_questions

class InterviewGenerator:
    def __init__(self, org_id):
        self.org_id = org_id
        self.interview_id = None
        self.language = None
        self.display_name = None
        self.description = None
        self.thank_you_text = None
        self.questions = []
        self.thank_you_url = None
        self.contact_required = False
        self.video_required = True

    def from_raw_text(self, raw_text):
        result = generate_interview_from_text(raw_text)
        if not result:
            raise ValueError("Interview generation failed")
        self.apply_result(result)
        return self

    def from_questions(self, questions):
        result = generate_interview_from_questions(questions)
        if not result:
            raise ValueError("Question-based generation failed")
        self.apply_result(result)
        return self

    def apply_result(self, result):
        self.language = result["language"]
        self.display_name = result["display_name"]
        self.description = result["description"]
        self.thank_you_text = result["thank_you_text"]
        self.questions = result["questions"]
        
        for field in ["thank_you_url", "contact_required", "video_required"]:
            if field in result: setattr(self, field, result[field])

    def insert_interview_to_db(self):
        question_list = [
            (i, q["question"], q["expected"])
            for i, q in enumerate(self.questions)
        ]
        self.interview_id = create_interview_with_questions(
            org_id=self.org_id,
            language=self.language,
            display_name=self.display_name,
            description_text=self.description,
            thank_you_text=self.thank_you_text,
            thank_you_url=self.thank_you_url,
            contact_required=self.contact_required,
            video_required=self.video_required,
            question_list=question_list
        )

    def to_dict(self):
        return {
            "org_id": self.org_id,
            "interview_id": self.interview_id,
            "language": self.language,
            "display_name": self.display_name,
            "description": self.description,
            "thank_you_text": self.thank_you_text,
            "questions": self.questions,
            "thank_you_url": self.thank_you_url,
            "contact_required": self.contact_required,
            "video_required": self.video_required
        }
    
    def build(self):
        try:
            prepare_interview_folder(self.org_id, self.interview_id)
        except Exception as e:
            raise RuntimeError(f"❌ Failed to create folder structure: {e}")

        try:
            blobs = record_interview_questions(self.questions)
        except Exception as e:
            raise RuntimeError(f"❌ Failed to synthesize questions: {e}")

        try:
            upload_interview_audio(self.org_id, self.interview_id, blobs)
        except Exception as e:
            raise RuntimeError(f"❌ Failed to upload audio: {e}")

