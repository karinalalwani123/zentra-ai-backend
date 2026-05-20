def format_email(email):
    return f"""
From: {email['sender']}
Subject: {email['subject']}
Body: {email['body']}
"""