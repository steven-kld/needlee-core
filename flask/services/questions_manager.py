from entities import (
    get_questions,
    get_question_audio_url,
    get_latest_attempt_number,
    wait_for_attempt_ready
)

class QuestionsManager:
    def __init__(self, org_id, interview_id, respondent_hash):
        """
        Service-level wrapper for managing questions and readiness state
        during an interview session.

        Args:
            org_id (int): Organization ID.
            interview_id (int): Interview ID.
            respondent_hash (str): Respondent UUID.
        """
        self.org_id = org_id
        self.interview_id = interview_id
        self.respondent_hash = respondent_hash

    def get_latest_attempt_number(self):
        """
        Get the latest attempt folder number for this respondent.

        Returns:
            int: The latest attempt number (1 if none exists yet).
        """
        return get_latest_attempt_number(
            self.org_id,
            self.interview_id,
            self.respondent_hash
        )

    def wait_for_ready(self, attempt_num, timeout=10):
        """
        Wait until `.ready` marker is found in the current attempt folder.

        Args:
            attempt_num (int): Which attempt number to check.
            timeout (int): Max wait time in seconds.

        Returns:
            bool: True if ready marker found, else False.
        """
        return wait_for_attempt_ready(
            self.org_id,
            self.interview_id,
            self.respondent_hash,
            attempt_num,
            timeout
        )

    def get_questions(self):
        """
        Fetch the list of interview questions (text only).

        Returns:
            list of dicts: Each with 'question_num' and 'question'.
        """
        return get_questions(self.interview_id)

    def generate_signed_urls(self, questions, expiration=3600):
        """
        Generate signed URLs for each question's audio file.

        Args:
            questions (list): List of dicts with 'question_num'.
            expiration (int): Link expiry time in seconds.

        Returns:
            list of str: Signed URLs for each question audio.
        """
        return [
            get_question_audio_url(
                self.org_id,
                self.interview_id,
                q["question_num"],
                expiration
            )
            for q in questions
        ]
