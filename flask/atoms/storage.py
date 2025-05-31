import os
import mimetypes
from dotenv import load_dotenv
from google.cloud import storage
from google.oauth2 import service_account
from datetime import timedelta
from google.api_core.exceptions import NotFound

load_dotenv()

def init_google_credentials():
    return service_account.Credentials.from_service_account_info({
        "type": "service_account",
        "project_id": os.getenv("GOOGLE_PROJECT_ID"),
        "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace('\\n', '\n'),
        "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
    })

def get_client():
    return storage.Client(credentials=init_google_credentials(), project=os.getenv("GOOGLE_PROJECT_ID"))

def create_org_bucket(org_id):
    client = get_client()
    bucket_name = f"o_{org_id}"
    if not client.lookup_bucket(bucket_name):
        client.create_bucket(bucket_name)
    print(f"✅ Bucket created or verified: {bucket_name}")

def get_bucket(org_id, logger=None):
    client = get_client()
    bucket_name = f"o_{org_id}"

    try:
        bucket = client.lookup_bucket(bucket_name)
        if bucket is None:
            msg = f"❌ Bucket '{bucket_name}' does not exist."
            if logger: logger.error(msg)
            else: print(msg)
            return None
        return bucket
    except NotFound:
        msg = f"❌ Bucket '{bucket_name}' not found (NotFound exception)."
        if logger: logger.error(msg)
        else: print(msg)
        return None
    except Exception as e:
        msg = f"❌ Unexpected error while accessing bucket '{bucket_name}': {e}"
        if logger: logger.exception(msg)
        else: print(msg)
        return None

def blob_exists(bucket, path):
    return bucket.blob(path).exists()

def create_empty_blob(bucket, path):
    bucket.blob(path).upload_from_string("")

def upload_string(bucket, path, data, content_type="text/plain"):
    blob = bucket.blob(path)
    blob.upload_from_string(data, content_type=content_type)

def upload_file_to_path(bucket, path, local_file_path):
    blob = bucket.blob(path)
    
    if local_file_path.endswith(".log"):
        mime_type = "text/plain; charset=utf-8"
    else:
        mime_type, _ = mimetypes.guess_type(local_file_path)
        if mime_type is None:
            raise ValueError(f"Unsupported file type for '{local_file_path}'")
        
    blob.content_type = mime_type
    blob.upload_from_filename(local_file_path)

def load_file_as_string(bucket, path):
    return bucket.blob(path).download_as_text()

def delete_blob(bucket, path):
    blob = bucket.blob(path)
    blob.delete()

def list_blobs(bucket, prefix):
    return list(bucket.list_blobs(prefix=prefix))

def get_signed_url(bucket, path, expiration=3600, method="GET"):
    blob = bucket.blob(path)
    return blob.generate_signed_url(
        expiration=timedelta(seconds=expiration),
        method=method
    )

def get_file_signed_url(org_id, path, expiration=3600):
    bucket = get_bucket(org_id)
    return get_signed_url(bucket, path, expiration)

def load_file(org_id, path):
    bucket = get_bucket(org_id)
    return load_file_as_string(bucket, path)

def upload_file(org_id, local_file_path, destination_path):
    bucket = get_bucket(org_id)
    upload_file_to_path(bucket, destination_path, local_file_path)

def get_last_attempt(org_id, interview_id, user_id):
    bucket = get_bucket(org_id)
    base_prefix = f"{interview_id}/respondents/{user_id}/"
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

    return max(attempt_nums) if attempt_nums else 0

def upload_blob_from_bytes(bucket, path, data_bytes, content_type="application/octet-stream"):
    """
    Upload a binary blob (e.g., mp3) to GCS at the specified path.
    
    Args:
        bucket: GCS bucket object
        path (str): Full path in the bucket
        data_bytes (bytes): Raw binary data to upload
        content_type (str): MIME type (e.g., "audio/mpeg")
    """
    blob = bucket.blob(path)
    blob.upload_from_string(data_bytes, content_type=content_type)

    
# import os, mimetypes
# from dotenv import load_dotenv
# from google.cloud import storage
# from google.oauth2 import service_account
# from google.api_core.exceptions import Forbidden, GoogleAPIError
# from datetime import timedelta

# load_dotenv()

# def init_google_credentials():
#     return service_account.Credentials.from_service_account_info({
#         "type": "service_account",
#         "project_id": os.getenv("GOOGLE_PROJECT_ID"),
#         "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
#         "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace('\\n', '\n'),
#         "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
#         "client_id": os.getenv("GOOGLE_CLIENT_ID"),
#         "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#         "token_uri": "https://oauth2.googleapis.com/token",
#         "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
#         "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
#     })

# def get_client():
#     return storage.Client(credentials=init_google_credentials(), project=os.getenv("GOOGLE_PROJECT_ID"))

# def get_bucket(org_id):
#     return get_client().bucket(f"o_{org_id}")

# def create_empty_blob(bucket, path):
#     blob = bucket.blob(path)
#     blob.upload_from_string("")



# def create_interview_folder(org_id, interview_id):
#     bucket = get_bucket(org_id)
#     base_path = f"{interview_id}/"
#     create_empty_blob(bucket, f"{base_path}questions/")
#     create_empty_blob(bucket, f"{base_path}respondents/")
#     print(f"✅ Interview folder initialized: {base_path}")

# def upload_file(org_id, interview_id, subfolder, local_file_path):
#     bucket = get_bucket(org_id)
#     file_name = os.path.basename(local_file_path)
#     blob_path = f"{interview_id}/{subfolder}/{file_name}"
#     blob = bucket.blob(blob_path)

#     mime_type, _ = mimetypes.guess_type(local_file_path)
#     if mime_type is None:
#         return False, f"❌ Unsupported file type for '{file_name}'"
#     blob.content_type = mime_type

#     try:
#         blob.upload_from_filename(local_file_path)
#         print(f"✅ File '{file_name}' uploaded to '{blob_path}' in bucket '{org_id}'")
#         return True, blob_path
#     except GoogleAPIError as e:
#         return False, f"❌ GCS error: {e}"
#     except Exception as e:
#         return False, f"❌ Upload failed: {e}"

# def create_respondent_folder(org_id, interview_id, respondent_uuid):
#     bucket = get_bucket(org_id)
#     base_path = f"{interview_id}/respondents/{respondent_uuid}/"
#     create_empty_blob(bucket, base_path)
#     print(f"✅ Respondent folder created: {base_path}")

# def create_respondent_attempt_folder(org_id, interview_id, respondent_uuid):
#     try:
#         bucket = get_bucket(org_id)
#         base_prefix = f"{interview_id}/respondents/{respondent_uuid}/"
#         blobs = list(bucket.list_blobs(prefix=base_prefix))

#         attempt_nums = set()
#         for blob in blobs:
#             parts = blob.name[len(base_prefix):].split('/')
#             if parts and parts[0].startswith("attempt_"):
#                 try:
#                     attempt_num = int(parts[0].split("_")[1])
#                     attempt_nums.add(attempt_num)
#                 except ValueError:
#                     continue

#         next_attempt = max(attempt_nums, default=0) + 1
#         attempt_path = f"{base_prefix}attempt_{next_attempt}/"
#         create_empty_blob(bucket, attempt_path)
#         create_empty_blob(bucket, f"{attempt_path}.ready")
#         print(f"📁 Created attempt folder: {attempt_path}")
#         return attempt_path

#     except Forbidden:
#         raise PermissionError("GCS write access forbidden")
#     except GoogleAPIError as e:
#         raise RuntimeError(f"GCS error: {e}")
#     except Exception as e:
#         raise RuntimeError(f"Unexpected error: {e}")

# def generate_question_signed_url(org_id, interview_id, question_n, expiration=3600):
#     bucket = get_bucket(org_id)
#     blob_path = f"{interview_id}/questions/{question_n}.webm"
#     blob = bucket.blob(blob_path)
#     return blob.generate_signed_url(
#         expiration=timedelta(seconds=expiration),
#         method="GET"
#     )

# def generate_interview_signed_url(org_id, interview_id, respondent_uuid, expiration=3600):
#     bucket = get_bucket(org_id)
#     blob_path = f"{interview_id}/respondents/{respondent_uuid}/interview.mp4"
#     blob = bucket.blob(blob_path)
#     return blob.generate_signed_url(
#         expiration=timedelta(seconds=expiration),
#         method="GET"
#     )
