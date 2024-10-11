import boto3
import uuid
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION_NAME, AWS_S3_BUCKET_NAME

def upload_audiostream_to_s3(audio_stream):
    """
    Upload an audio stream to AWS S3 and return the S3 file name.
    """
    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION_NAME,
    )
    s3 = session.client("s3")
    s3_file_name = f"{uuid.uuid4()}.mp3"
    s3.upload_fileobj(audio_stream, AWS_S3_BUCKET_NAME, s3_file_name)
    return s3_file_name

def generate_presigned_url(s3_file_name):
    """
    Generate a presigned URL for an S3 object.
    """
    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION_NAME,
    )
    s3 = session.client("s3")
    signed_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": AWS_S3_BUCKET_NAME, "Key": s3_file_name},
        ExpiresIn=3600,
    )
    return signed_url
