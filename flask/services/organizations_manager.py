from entities import check_creds, set_password, get_interviews_for_org

class OrganizationManager:
    def __init__(self, email, display_name, org_id):
        self.email = email
        self.display_name = display_name
        self.org_id = org_id
        self.interviews = get_interviews_for_org(org_id)

    @classmethod
    def from_login(cls, email, password):
        msg, display_name, org_id = check_creds(email, password)
        if org_id is None:
            raise ValueError(f"Login failed: {msg}")
        return cls(email, display_name, org_id)

    @classmethod
    def from_session(cls, session):
        if not session.get("org_id"):
            raise ValueError("User not logged in")
        return cls(session["email"], session["display_name"], session["org_id"])
