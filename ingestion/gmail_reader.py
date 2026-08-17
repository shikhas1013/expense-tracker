import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import html
from lambda_function import lambda_handler

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def main():
  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)

    queries = ['from:ibanking.alert@dbs.com subject:"iBanking Alerts" PAYNOW', 
               'from:paylah.alert@dbs.com']
    
    comb_queries = " OR ".join([f"({q})" for q in queries])

    results = service.users().messages().list(
        userId="me",
        q=comb_queries,
        maxResults=10
    ).execute()

    messages = results.get("messages", [])

    if not messages:
        print("No DBS emails found.")
        return

    for msg in messages:
      msg_id = msg["id"]

      message = service.users().messages().get(
          userId="me",
          id=msg_id,
          format="full"
      ).execute()

      email_body = extract_email_body(message)

      response = lambda_handler({
          "email_text": email_body,
          "email_id": msg_id
      }, None)

      print(response)

  except HttpError as error:
    print(f"An error occurred: {error}")

def extract_email_body(message):
    def walk_parts(part):
        mime_type = part.get("mimeType")
        body = part.get("body", {})
        data = body.get("data")

        if data and mime_type in ["text/plain", "text/html"]:
            decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            return html.unescape(decoded)

        for sub_part in part.get("parts", []):
            result = walk_parts(sub_part)
            if result:
                return result

        return None

    payload = message.get("payload", {})
    body = walk_parts(payload)

    if body:
        return body

    return html.unescape(message.get("snippet", ""))
if __name__ == "__main__":
  main()