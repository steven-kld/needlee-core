from utils.logger import LogManager
import openai, os, shutil
from entities import (
    update_respondent_status,
    get_respondent,
    get_interview_by_id,
    get_closed_respondent_id,
    get_questions_expected,
    download_attempt_files,
    generate_transcription,
    rate_answer_set,
    build_video,
    upload_interview,
)

class ProcessManager:
    def __init__(self, organization_id, interview_id, user_id, attempt):
        self.organization_id = organization_id
        self.interview_id = interview_id
        self.user_id = user_id
        self.attempt = attempt
        
        self.language_code = None
        self.language_name = None
        self.valid = False
        self.respondent_id = None
        self.questions = []
        self.openai_client = None
        self.logger = None
        
        try:
            self._validate_inputs()
            self.questions = get_questions_expected(self.interview_id)
            self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            if self._init_process() == False:
                return
                
            self.valid = True
            self.logger.info("✅ ProcessManager data validation success")

        except Exception as e:
            self.logger.info(f"❌ ProcessManager init failed: {e}")

    def _init_process(self):
        self.respondent_id = get_closed_respondent_id(self.organization_id, self.interview_id, self.user_id)
        if not self.respondent_id:
            respondent = get_respondent(self.organization_id, self.interview_id, self.user_id)
            if respondent == None:
                return False
            if respondent["status"] in ["error", "process"]:
                update_respondent_status(respondent["id"], "closed")
                self.respondent_id = get_closed_respondent_id(self.organization_id, self.interview_id, self.user_id)
            else:
                return False
        
        local_dir = f"temp/{self.user_id}"
        os.makedirs(local_dir, exist_ok=True)

        log_manager = LogManager(
            logger_name="NeedleeCore",
            log_path=f"{local_dir}/",
            log_file="process.log",
            uuid=self.user_id
        )
        self.logger = log_manager.get_session_logger()
        
        try:
            self.language_code = get_interview_by_id(self.organization_id, self.interview_id)['language']
        except:
            self.logger.error(f"❌ Failed to detect interview language")
            return False
        
        lang_map = {
            "ru": "Russian",
            "en": "English",
            "es": "Spanish",
            "de": "German",
            "fr": "French"
        }

        self.language_name = lang_map.get(self.language_code, None)
        if self.language_name == None:
            self.logger.error(f"❌ {self.language_code} is not supported ")
            return False
        
        update_respondent_status(self.respondent_id, "process")
        self.logger.info(f"✅ Respondent {self.user_id} status was set to process")

        return True
    
    def _validate_inputs(self):
        if not all([self.organization_id, self.interview_id, self.user_id]):
            raise ValueError("Missing required process parameters.")
        
    def process(self):
        if not self.valid:
            return False
        
        self.logger.info("✅ Interview processing started")
        self.logger.start_timer()

        if download_attempt_files(self.organization_id, self.interview_id, self.user_id, self.attempt, self.logger) == []:
            self.logger.error("❌ Downloading step failed - stopping.")
            return

        self.logger.info(f"✅ Files downloading complete")
        
        data = generate_transcription(self.user_id, self.questions, self.logger, self.language_code)
        if not data:
            self.logger.error("❌ Transcription step failed - stopping.")
            return
        else:
            data = rate_answer_set(data, self.logger, self.language_name)
            self.logger.info(f"✅ Rating step complete")
        
        timecodes = build_video(self.user_id, len(data["interview"]), self.logger)
        if timecodes != {}:
            self.logger.info(f"✅ Video processing step complete")
            data["timecodes"] = timecodes

            upload_interview(self.user_id, 14, self.interview_id, self.organization_id, data, self.logger)
            shutil.rmtree(f"temp/{self.user_id}")

                
            
            
