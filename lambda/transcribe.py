import json
import os
import time
import urllib.request
import boto3
import uuid
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

OUTPUT_BUCKET = os.environ["OUTPUT_BUCKET"]
WHATSAPP_ACCESS_TOKEN = os.environ["WHATSAPP_ACCESS_TOKEN"]
TRANSCRIPTS_TABLE = os.environ["TRANSCRIPTS_TABLE"]
OPEN_API_KEY = os.environ["OPEN_API_KEY"]

table = dynamodb.Table(TRANSCRIPTS_TABLE)

def transcribe_audio(local_audio_file):
    """
    Transcribe an audio file using the OpenAI REST API.

    Returns:
        Transcript text.
    """

    api_key = os.environ["OPEN_API_KEY"]

    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    }

    with open(local_audio_file, "rb") as f:
        audio_bytes = f.read()

    body = bytearray()

    # model
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="model"\r\n\r\n')
    body.extend(b"gpt-4o-mini-transcribe\r\n")

    # file
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        b'Content-Disposition: form-data; '
        b'name="file"; filename="audio.m4a"\r\n'
    )
    body.extend(b"Content-Type: audio/mp4\r\n\r\n")
    body.extend(audio_bytes)
    body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode())

    request = urllib.request.Request(
        "https://api.openai.com/v1/audio/transcriptions",
        data=bytes(body),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(request) as response:
            result = json.loads(response.read().decode())
            return result["text"]
    except urllib.error.HTTPError as e:
        print("Status:", e.code)
        print(e.read().decode())
        raise

def lambda_handler(event, context):

    record = event["Records"][0]

    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]

    head = s3.head_object(Bucket=bucket, Key=key)
    metadata = head.get("Metadata", {})
    from_number = metadata.get("from")
    x_amz_meta_from = metadata.get("x-amz-meta-from")
    phone_number_id = metadata.get("phone_number_id")
    print(f"event: {json.dumps(event)}")
    print(f"from_number: {from_number}")
    print(f"x-amz-meta-from: {x_amz_meta_from}")
    print(f"metadata: {metadata}") 
    if not from_number:
        raise Exception("Missing 'from' metadata on audio object")
    print(f"Replying to WhatsApp number: {from_number}")

    extension = key.split(".")[-1]

    media_uri = f"s3://{bucket}/{key}"
    local_file = "/tmp/audio.m4a"

    s3.download_file(bucket, key, local_file)

    text = transcribe_audio(local_file)

    #job_name = f"{key.replace('/', '-').replace('.', '-')}-{int(time.time())}"

    #print(f"Starting transcription: {job_name}")
    #print(f"Media URI: {media_uri}")
    #print(f"Output bucket: {OUTPUT_BUCKET}")
    #print(f"Extension: {extension}")
    #transcribe.start_transcription_job(
    #    TranscriptionJobName=job_name,
    #    LanguageCode="en-US",
    #    Media={
    #        "MediaFileUri": media_uri
    #    },
    #    MediaFormat=extension,
    #    OutputBucketName=OUTPUT_BUCKET,
    #    OutputKey=f"transcripts/{job_name}.json"
    #)

    #while True:

    #    response = transcribe.get_transcription_job(
    #        TranscriptionJobName=job_name
    #    )
    #
    #    status = response["TranscriptionJob"]["TranscriptionJobStatus"]

    #    print(status)

    #    if status == "COMPLETED":
    #        break

    #    if status == "FAILED":
    #        raise Exception("Transcription failed")

    #    time.sleep(5)

    #response = s3.get_object(
    #    Bucket=OUTPUT_BUCKET,
    #    Key=f"transcripts/{job_name}.json"
    #)

    #transcript = json.loads(
    #    response["Body"].read().decode("utf-8")
    #)

    #text = transcript["results"]["transcripts"][0]["transcript"]

    print(text)

    payload = {
        "messaging_product": "whatsapp",
        "to": from_number,
        "type": "text",
        "text": {
            "body": text
        }
    }

    request = urllib.request.Request(
        f"https://graph.facebook.com/v23.0/{phone_number_id}/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(request) as resp:
            print(resp.read().decode())
    except urllib.error.HTTPError as e:
        print("HTTP Status:", e.code)
        print("URL:", request.full_url)
        print("Payload:")
        print(json.dumps(payload, indent=2))
        print("Response:")
        print(e.read().decode())
        raise

    # Save transcript to DynamoDB
    message_id = metadata.get("messageid", key.rsplit(".",1)[0])
    timestamp = metadata.get("timestamp")

    table.put_item(
        Item={
            "messageId": message_id,
            "phoneNumber": from_number,
            "timestamp": int(timestamp) if timestamp else int(time.time()),
            "audioKey": key,
            "transcript": text
        }
    )
    print(f"Saved transcript {message_id} to DynamoDB")

    return {
        "status": "completed",
        "text": text
    }