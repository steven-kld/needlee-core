from atoms import get_bucket, upload_file_to_path
import tempfile
import os
import mimetypes

def save_chunk(org_id, interview_id, uuid, attempt, question_num, chunk_index, file_storage):
    bucket = get_bucket(org_id)

    # Build GCS path: o_<org_id>/<interview_id>/respondents/<uuid>/attempt_<n>/<q>_<chunk>.webm
    gcs_path = f"{interview_id}/respondents/{uuid}/attempt_{attempt}/{question_num}_{chunk_index}.webm"

    # Save file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        file_storage.save(tmp.name)
        local_file_path = tmp.name

    # Upload to GCS
    upload_file_to_path(bucket, gcs_path, local_file_path)

    # Cleanup
    os.remove(local_file_path)

    return True
