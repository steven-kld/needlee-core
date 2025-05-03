user_id = "825098b6-524d-48da-8c03-ac2c00c705a3"
user_contact = "long"
interview_id = 1
organization_id = 1
attempt = None

from services.process_manager import ProcessManager

process = ProcessManager(organization_id, interview_id, user_id, attempt)
process.process()