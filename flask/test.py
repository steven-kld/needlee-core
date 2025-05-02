user_id = "b117d2ba-f101-4616-a041-ce9a9c6d5474"
user_contact = "qwerqq"
interview_id = 1
organization_id = 1
attempt = None

from services.process_manager import ProcessManager

process = ProcessManager(organization_id, interview_id, user_id, attempt)
process.process()