from entities import (
    get_interview_by_id,
    get_or_create_respondent,
    update_respondent_status,
    get_progress_respondent_id
)

class InterviewManager:
    def __init__(self, org_id, interview_id, contact, uuid):
        self.org_id = org_id
        self.interview_id = interview_id
        self.contact = contact
        self.uuid = uuid

        self.err = None
        self.valid = False
        self.interview = None
        self.respondent = None
        self.respondent_exists = False
        self.attempt_path = None

        if self.validate():
            self.valid = True

    def validate(self):
        """
        Validate required inputs and load interview data.
        Sets self.err on failure.
        """
        self.interview = get_interview_by_id(self.org_id, self.interview_id)

        if not self.org_id or not self.interview_id or not self.uuid:
            self.err = ("Missing required fields", 400)
            return False

        if not self.interview:
            self.err = ("Interview not found", 404)
            return False

        if self.interview["contact_required"]:
            if not self.contact:
                self.err = ("Contact is required for this interview", 400)
                return False
        else:
            self.contact = self.uuid  # fallback to anonymous ID

        return True

    def get_initial_response(self):
        """
        Returns a dict with interview metadata and 'complete' flag.
        Starts async preparation if interview is not yet complete.
        """
        if not self.valid:
            return self.get_error_response()
        
        self.respondent, self.respondent_exists = get_or_create_respondent(
            org_id=self.org_id,
            interview_id=self.interview_id,
            contact=self.contact,
            respondent_hash=self.uuid,
            interview_name=self.interview["display_name"],
            language=self.interview["language"]
        )
        self.uuid = self.respondent["respondent_hash"]
        update_respondent_status(self.respondent["id"], "init")
        
        return {
            "uuid": self.uuid,
            "respondent_exists": self.respondent_exists,
            "complete": self.respondent["status"] not in ["init", "progress"],
            "displayName": self.interview["display_name"],
            "description": self.interview["description"],
            "thankYouMessage": self.interview["thank_you_text"],
            "thankYouUrl": self.interview["thank_you_url"],
            "video": self.interview["video_required"],
            "language": self.interview["language"]
        }, 200

    def get_error_response(self):
        """
        Wraps any internal error into a proper API response.
        """
        if self.err:
            message, code = self.err
            return ({"complete": True} if code == 200 else {"error": message}, code)
        return None

    def close_interview(self):
        respondent_id = get_progress_respondent_id(self.org_id, self.interview_id, self.uuid)
        if respondent_id:
            update_respondent_status(respondent_id, "closed")
            return True
        return False