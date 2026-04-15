import boto3
import mimetypes
from botocore.exceptions import NoCredentialsError, ClientError
import os
import time
import config


def _get_client(service):
    return boto3.client(
        service,
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
        region_name=config.AWS_REGION,
    )


def upload_files(file_list):
    if not file_list:
        print("  No files to upload")
        return []

    client = _get_client("s3")
    uploaded = []
    base_dir = os.path.dirname(os.path.dirname(__file__))
    web_dir = os.path.join(base_dir, "website")

    for fpath in file_list:
        if os.path.isabs(fpath):
            full_path = fpath
        else:
            full_path = os.path.join(base_dir, fpath)

        if not os.path.isfile(full_path):
            print(f"  Skip (not found): {fpath}")
            continue

        if full_path.startswith(web_dir):
            s3_key = os.path.relpath(full_path, web_dir)
        else:
            s3_key = os.path.basename(fpath)

        extra = {"ACL": "public-read"}
        content_type, _ = mimetypes.guess_type(full_path)
        if content_type:
            extra["ContentType"] = content_type

        try:
            client.upload_file(full_path, config.S3_BUCKET, s3_key, ExtraArgs=extra)
            uploaded.append(s3_key)
            print(f"  Uploaded: {s3_key}")
        except FileNotFoundError:
            print(f"  File not found: {full_path}")
        except NoCredentialsError:
            print("  AWS credentials not available")
        except ClientError as e:
            print(f"  Failed to upload {s3_key}: {e}")

    if uploaded and config.DISTRIBUTION_ID:
        _invalidate_cache()

    print(f"Uploaded {len(uploaded)} files to s3://{config.S3_BUCKET}")
    return uploaded


def _invalidate_cache():
    try:
        client = _get_client("cloudfront")
        ref = str(time.time()).replace(".", "")
        inv = client.create_invalidation(
            DistributionId=config.DISTRIBUTION_ID,
            InvalidationBatch={
                "Paths": {"Quantity": 1, "Items": ["/*"]},
                "CallerReference": ref,
            },
        )
        print(f"  CloudFront invalidation: {inv['Invalidation']['Id']}")
    except Exception as e:
        print(f"  CloudFront invalidation failed: {e}")
