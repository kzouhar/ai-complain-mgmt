import json
import os
import traceback
import time
import urllib.request
import urllib.error

import boto3

VERIFY_TOKEN = os.environ["VERIFY_TOKEN"]
ACCESS_TOKEN = os.environ["WHATSAPP_ACCESS_TOKEN"]
MEDIA_BUCKET = os.environ["MEDIA_BUCKET"]

s3 = boto3.client("s3")


def download_media(media_id):
    """
    Download a WhatsApp media file using the Graph API.
    Returns: (bytes, mime_type)
    """

    # Step 1: Get the media metadata (includes the download URL)
    metadata_request = urllib.request.Request(
        f"https://graph.facebook.com/v25.0/{media_id}",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }
    )

    with urllib.request.urlopen(metadata_request, timeout=30) as response:
        metadata = json.loads(response.read().decode("utf-8"))

    media_url = metadata["url"]
    mime_type = metadata["mime_type"]

    # Step 2: Download the media
    media_request = urllib.request.Request(
        media_url,
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }
    )

    with urllib.request.urlopen(media_request, timeout=60) as response:
        media_bytes = response.read()

    return media_bytes, mime_type


def save_to_s3(media_id, data, mime_type, message_from, phone_number_id):

    extensions = {
        "audio/ogg": "ogg",
        "audio/opus": "opus",
        "audio/mp4": "m4a",
        "audio/mpeg": "mp3",
        "audio/aac": "aac",
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp"
    }

    extension = extensions.get(mime_type, "bin")

    key = f"{media_id}.{extension}"

    s3.put_object(
        Bucket=MEDIA_BUCKET,
        Key=key,
        Body=data,
        ContentType=mime_type,
        Metadata={
            "from": message_from,
            "messageid": media_id,
            "timestamp": str(int(time.time())),
            "phone_number_id": phone_number_id
        }
    )

    return key


def lambda_handler(event, context):

    print(json.dumps(event))

    http_method = event.get("httpMethod", "")

    # ----------------------------------------------------
    # Webhook Verification
    # ----------------------------------------------------
    if http_method == "GET":

        params = event.get("queryStringParameters") or {}

        if (
            params.get("hub.mode") == "subscribe"
            and params.get("hub.verify_token") == VERIFY_TOKEN
        ):
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "text/plain"
                },
                "body": params["hub.challenge"]
            }

        return {
            "statusCode": 403,
            "body": "Verification failed"
        }

    # ----------------------------------------------------
    # Incoming WhatsApp Messages
    # ----------------------------------------------------
    elif http_method == "POST":

        try:

            body = json.loads(event["body"])
            print(json.dumps(body, indent=2))

            change = body["entry"][0]["changes"][0]["value"]

            if "messages" not in change:
                return {
                    "statusCode": 200,
                    "body": json.dumps({"status": "ignored"})
                }

            message = change["messages"][0]
           
            if message["type"] != "audio":
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "status": "not audio"
                    })
                }

            media_id = message["audio"]["id"]
            message_from = message["from"]
            phone_number_id = change["metadata"]["phone_number_id"]
            print(f"Downloading media: {media_id}")

            audio, mime_type = download_media(media_id)

            key = save_to_s3(
                media_id,
                audio,
                mime_type,
                message_from,
                phone_number_id
            )

            print(f"Saved to s3://{MEDIA_BUCKET}/{key}")

            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "stored",
                    "media_id": media_id,
                    "bucket": MEDIA_BUCKET,
                    "key": key,
                    "mime_type": mime_type
                })
            }

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")

            print("HTTP Error")
            print(error_body)

            return {
                "statusCode": e.code,
                "body": json.dumps({
                    "error": error_body
                })
            }

        except Exception as ex:

            traceback.print_exc()

            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": str(ex)
                })
            }

    return {
        "statusCode": 405,
        "body": "Method Not Allowed"
    }