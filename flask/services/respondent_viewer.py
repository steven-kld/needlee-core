from entities import (
    get_respondent_by_id,
    get_interview_recording_url,
    get_respondent_review
)

class RespondentViewer:
    def __init__(self, org_id, respondent_id):
        self.exists = False
        self.respondent_id = respondent_id
        self.respondent = get_respondent_by_id(org_id, respondent_id)
        if self.respondent:
            self.exists = True
            self.url = get_interview_recording_url(
                self.respondent["organization_id"], 
                self.respondent["interview_id"], 
                self.respondent["respondent_hash"]
            )

    def get_required_respondent_data(self):
        self.data_required = True

        review_row = get_respondent_review(self.respondent_id)
        if not review_row:
            return

        self.review_data = review_row["review_data"]
        self.created_at = review_row["created_at"]
        self.contact = self.respondent["contact"]
        self.rate = self.review_data.get("summary", {}).get("rate", None)


    def to_dict(self):
        base = {
            "recording_url": self.url
        }

        if not self.data_required:
            return base

        return {
            **base,
            "respondent": {
                "id": self.respondent_id,
                "contact": self.contact,
                "date": self.created_at.strftime("%Y-%m-%d") if self.created_at else None,
                "rate": self.rate,
                "review_data": self.review_data
            }
        }

