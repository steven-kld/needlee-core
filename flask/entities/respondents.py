from atoms import run_query
from atoms import get_bucket, create_empty_blob, list_blobs
from google.api_core.exceptions import Forbidden, GoogleAPIError

def get_progress_respondent_id(org_id, interview_id, respondent_hash):
    """
    Return respondent ID if status is 'init' or 'progress'; otherwise return None.
    """
    row = run_query(
        """
        SELECT id FROM respondents
        WHERE organization_id = %s AND interview_id = %s
        AND respondent_hash = %s AND status IN ('init', 'progress')
        """,
        (org_id, interview_id, respondent_hash),
        fetch_one=True
    )
    return row["id"] if row else None


def get_or_create_respondent(org_id, interview_id, contact, respondent_hash, interview_name, language):
    """
    Fetch an existing respondent by interview + contact, or create one if not found.

    Args:
        org_id (int): Organization ID.
        interview_id (int): Interview ID.
        contact (str): Contact ID (or fallback UUID).
        respondent_hash (str): UUID used for file system tracking.
        interview_name (str): Name to show in dashboards/logs.
        language (str): Language code.

    Returns:
        tuple: (respondent dict, exists: bool)
    """
    existing = run_query(
        """
        SELECT * FROM respondents
        WHERE interview_id = %s AND contact = %s
        """,
        (interview_id, contact),
        fetch_one=True
    )

    if existing:
        return existing, True

    new_respondent = run_query(
        """
        INSERT INTO respondents (
            interview_id, organization_id, interview_display_name,
            contact, respondent_hash, language, status, timecodes, visible
        ) VALUES (%s, %s, %s, %s, %s, %s, 'init', '', TRUE)
        RETURNING *
        """,
        (interview_id, org_id, interview_name, contact, respondent_hash, language),
        fetch_one=True
    )

    return new_respondent, False


def update_respondent_status(respondent_id, new_status):
    """
    Update the respondent's status (e.g., from 'init' to 'progress' or 'done').

    Args:
        respondent_id (int): Respondent row ID.
        new_status (str): New status to assign.

    Returns:
        None
    """
    run_query(
        """
        UPDATE respondents SET status = %s WHERE id = %s
        """,
        (new_status, respondent_id)
    )


def create_respondent_folder(org_id, interview_id, respondent_uuid):
    """
    Initialize an empty folder in GCS for a respondent.

    Args:
        org_id (int): Organization ID.
        interview_id (int): Interview ID.
        respondent_uuid (str): UUID used for folder naming.

    Returns:
        str: Path of created folder.
    """
    bucket = get_bucket(org_id)
    base_path = f"{interview_id}/respondents/{respondent_uuid}/"
    create_empty_blob(bucket, base_path)
    print(f"✅ Respondent folder created: {base_path}")
    return base_path


def create_respondent_attempt_folder(org_id, interview_id, respondent_uuid):
    """
    Creates a versioned attempt folder for a respondent and marks it with a `.ready` file.

    Args:
        org_id (int): Organization ID.
        interview_id (int): Interview ID.
        respondent_uuid (str): UUID used for pathing.

    Returns:
        str: Full path of the created attempt folder.

    Raises:
        PermissionError or RuntimeError on failure.
    """
    try:
        bucket = get_bucket(org_id)
        base_prefix = f"{interview_id}/respondents/{respondent_uuid}/"
        blobs = list_blobs(bucket, prefix=base_prefix)

        attempt_nums = set()
        for blob in blobs:
            parts = blob.name[len(base_prefix):].split('/')
            if parts and parts[0].startswith("attempt_"):
                try:
                    attempt_num = int(parts[0].split("_")[1])
                    attempt_nums.add(attempt_num)
                except ValueError:
                    continue

        next_attempt = max(attempt_nums, default=0) + 1
        attempt_path = f"{base_prefix}attempt_{next_attempt}/"
        create_empty_blob(bucket, attempt_path)
        create_empty_blob(bucket, f"{attempt_path}.ready")

        print(f"📁 Created attempt folder: {attempt_path}")
        return attempt_path, next_attempt

    except Forbidden:
        raise PermissionError("GCS write access forbidden")
    except GoogleAPIError as e:
        raise RuntimeError(f"GCS error: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {e}")
