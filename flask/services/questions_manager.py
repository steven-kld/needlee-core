from entities import (
    get_questions,
    get_question_audio_url,
    create_respondent_folder,
    create_respondent_attempt_folder,
    wait_for_attempt_ready
)

class QuestionsManager:
    def __init__(self, org_id, interview_id, respondent_hash, respondent_exists):
        self.org_id = org_id
        self.interview_id = interview_id
        self.respondent_hash = respondent_hash
        self.respondent_exists = respondent_exists

    def prepare_respondent(self):
        if not self.respondent_exists:
            create_respondent_folder(self.org_id, self.interview_id, self.respondent_hash)

        self.attempt_path, attempt_num = create_respondent_attempt_folder(
            self.org_id, self.interview_id, self.respondent_hash
        )

        return attempt_num

    def wait_for_ready(self, attempt_num, timeout=10):
        return wait_for_attempt_ready(
            self.org_id,
            self.interview_id,
            self.respondent_hash,
            attempt_num,
            timeout
        )

    def get_questions(self):
        return get_questions(self.interview_id)

    def generate_signed_urls(self, questions, expiration=3600):
        return [
            get_question_audio_url(
                self.org_id,
                self.interview_id,
                q["question_num"],
                expiration
            )
            for q in questions
        ]
