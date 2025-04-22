from entities.answers import save_chunk as save_chunk_entity

class AnswersManager:
    def __init__(self, org_id, interview_id, respondent_hash):
        """
        Service-layer manager for handling respondent answer uploads.

        Args:
            org_id (int): Organization ID.
            interview_id (int): Interview ID.
            respondent_hash (str): Respondent UUID.
        """
        self.org_id = org_id
        self.interview_id = interview_id
        self.respondent_hash = respondent_hash

    def save_chunk(self, attempt, question_num, chunk_index, file_storage):
        """
        Save a recorded chunk to the proper GCS path.

        Args:
            attempt (int): Attempt number.
            question_num (int): Which question.
            chunk_index (int): Slice index (15s intervals).
            file_storage (werkzeug.datastructures.FileStorage): Uploaded chunk.

        Returns:
            bool: Success.
        """
        return save_chunk_entity(
            self.org_id,
            self.interview_id,
            self.respondent_hash,
            attempt,
            question_num,
            chunk_index,
            file_storage
        )
