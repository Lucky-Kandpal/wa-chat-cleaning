#pip install fastapi uvicorn emoji python-multipart
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import re
import json
from datetime import datetime
import unicodedata
import emoji
import tempfile

app = FastAPI()

# === Utility Functions ===

def clean_unicode(text):
    return ''.join(c for c in text if unicodedata.category(c) != 'Cf')

def remove_emojis(text):
    return emoji.replace_emoji(text, replace='')

def is_system_message(message):
    system_phrases = [
        "Messages and calls are end-to-end encrypted",
        "image omitted",
        "video omitted",
        "GIF omitted",
        "document omitted",
        "changed their phone number to a new number",
        "added ~",
        "created this group",
        "This message was deleted.",
        "added you",
        "was added",
        "Waiting for this message"
    ]
    return any(phrase in message for phrase in system_phrases)

# === FastAPI Route ===

@app.post("/clean-chat/")
async def clean_chat(file: UploadFile = File(...)):
    raw_text = await file.read()
    raw_text = raw_text.decode("utf-8")

    cleaned_text = clean_unicode(raw_text)

    msg_start_pattern = re.compile(
        r"^\[(\d{2}/\d{2}/\d{2}), (\d{1,2}:\d{2}:\d{2})\s?(AM|PM)?\] (.*?): (.*)"
    )

    lines = cleaned_text.splitlines()
    parsed_messages = []
    current_message = None

    for line in lines:
        match = msg_start_pattern.match(line)
        if match:
            if current_message:
                parsed_messages.append(current_message)

            date_str, time_str, am_pm, sender, message = match.groups()
            timestamp_str = f"{date_str} {time_str} {am_pm or ''}".strip()

            try:
                timestamp = datetime.strptime(timestamp_str, "%d/%m/%y %I:%M:%S %p")
            except ValueError:
                try:
                    timestamp = datetime.strptime(timestamp_str, "%d/%m/%y %H:%M:%S")
                except ValueError:
                    continue

            sender = ''.join(c for c in sender.lstrip("~").strip() if unicodedata.category(c) != 'Cf')
            message = ''.join(c for c in message.strip() if unicodedata.category(c) != 'Cf')
            sender=remove_emojis(sender)
            message = remove_emojis(message)

            if is_system_message(message):
                current_message = None
                continue

            current_message = {
                "sender": sender,
                "message": message,
                "timestamp": timestamp.isoformat()
            }
        elif current_message:
            extra_line = remove_emojis(line.strip())
            current_message["message"] += "\n" + extra_line

    if current_message:
        parsed_messages.append(current_message)

    # Write to a temporary file (optional for download)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='w', encoding='utf-8') as tmp_file:
        json.dump(parsed_messages, tmp_file, ensure_ascii=False, indent=2)
        tmp_file_path = tmp_file.name

    return JSONResponse(content={"status": "success", "messages_cleaned": len(parsed_messages), "data": parsed_messages})






# import re
# import json
# from datetime import datetime
# import unicodedata
# import emoji
# # Step 1: Load and clean raw WhatsApp text from _chat.txt
# chat_txt_path = "_chat.txt"
# final_output_path = "final_cleaned_chat.json"

# with open(chat_txt_path, "r", encoding="utf-8") as f:
#     raw_text = f.read()

# # Clean invisible Unicode characters
# def clean_unicode(text):
#     return ''.join(c for c in text if unicodedata.category(c) != 'Cf')

# cleaned_text = clean_unicode(raw_text)

# # Regex to detect start of a message
# msg_start_pattern = re.compile(
#     r"^\[(\d{2}/\d{2}/\d{2}), (\d{1,2}:\d{2}:\d{2})\s?(AM|PM)?\] (.*?): (.*)"
# )

# def remove_emojis(text):
#     return emoji.replace_emoji(text, replace='')  
# # Emoji removal pattern
# emoji_pattern = re.compile(
#     "["
#     "\U0001F600-\U0001F64F"
#     "\U0001F300-\U0001F5FF"
#     "\U0001F680-\U0001F6FF"
#     "\U0001F1E0-\U0001F1FF"
#     "\U00002700-\U000027BF"
#     "\U0001F900-\U0001F9FF"
#     "\U00002600-\U000026FF"
#     "\U00002B50"
#     "]+", flags=re.UNICODE
# )

# # System messages to exclude
# system_phrases = [
#     "Messages and calls are end-to-end encrypted",
#     "image omitted",
#     "video omitted",
#     "GIF omitted",
#     "document omitted",
#     "changed their phone number to a new number",
#     "added ~",
#     "created this group",
#     "This message was deleted.",
#     "added you",
#     "was added",
#     "Waiting for this message",
# ]

# # Step 2: Parse lines and build messages
# lines = cleaned_text.splitlines()
# parsed_messages = []
# current_message = None

# for line in lines:
#     match = msg_start_pattern.match(line)
#     if match:
#         if current_message:
#             parsed_messages.append(current_message)
#         date_str, time_str, am_pm, sender, message = match.groups()
#         timestamp_str = f"{date_str} {time_str} {am_pm or ''}".strip()
#         try:
#             timestamp = datetime.strptime(timestamp_str, "%d/%m/%y %I:%M:%S %p")
#         except ValueError:
#             try:
#                 timestamp = datetime.strptime(timestamp_str, "%d/%m/%y %H:%M:%S")
#             except ValueError:
#                 continue

#         # Clean fields
#         sender = ''.join(c for c in sender.lstrip("~").strip() if unicodedata.category(c) != 'Cf')
#         message = ''.join(c for c in message.strip() if unicodedata.category(c) != 'Cf')
#         message = remove_emojis(message)

#         if any(phrase in message for phrase in system_phrases):
#             current_message = None
#             continue

#         current_message = {
#             "sender": sender,
#             "message": message,
#             "timestamp": timestamp.isoformat()
#         }
#     elif current_message:
#         extra_line = remove_emojis(line.strip())
#         current_message["message"] += "\n" + extra_line

# if current_message:
#     parsed_messages.append(current_message)

# # Step 3: Save final cleaned output
# with open(final_output_path, "w", encoding="utf-8") as out_file:
#     json.dump(parsed_messages, out_file, ensure_ascii=False, indent=2)

# final_output_path
