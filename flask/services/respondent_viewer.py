from entities import (
    get_respondent_by_id,
    get_interview_recording_url
)

class RespondentViewer:
    def __init__(self, org_id, respondent_id):
        self.exists = False
        self.respondent = get_respondent_by_id(org_id, respondent_id)
        if self.respondent:
            self.exists = True
            self.url = get_interview_recording_url(
                self.respondent["organization_id"], 
                self.respondent["interview_id"], 
                self.respondent["respondent_hash"]
            )
