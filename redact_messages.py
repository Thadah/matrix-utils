import asyncio
import time

from nio import (
    AsyncClient,
    RoomMessagesError,
    RoomRedactResponse
)

# ----------------------------------
# Configuration
# ----------------------------------
HOMESERVER = "https://matrix.homeserver.example"
USER_ID = "@admin:matrix.homeserver.example"    # Your full user ID
PASSWORD = ""              # Your Matrix password
ROOM_ID = "!room_id:matrix.homeserver.example"

# If the server rate-limits you, try increasing this:
REDACTION_DELAY_SECONDS = 0.1

# Which event types to redact:
ALLOWED_TYPES_TO_REDACT = [
    "m.room.message",    # unencrypted messages
    "m.room.encrypted",  # encrypted messages
    # "m.room.member",    # or other types if you really want to
]

async def redact_all_messages():
    """
    Redacts messages in a Matrix room based on specified criteria.

    This function connects to a Matrix server, logs in as a specified user, 
    and paginates through messages in a specified room. It redacts messages 
    that match allowed event types. The function handles server rate limits 
    by introducing a delay between redactions.

    Returns:
        None
    """

    # Create the matrix-nio async client
    client = AsyncClient(homeserver=HOMESERVER, user=USER_ID)

    # Login to the instance with password
    login_response = await client.login(
        password=PASSWORD,
        device_name="Redaction script"
    )
    if login_response and login_response.access_token:
        print("Successfully logged in.")
    else:
        print(f"Login error: {login_response}")
        await client.close()
        return

    try:
        total_redacted = 0
        from_token = ""  # Start with an empty pagination token

        while True:
            print(f"Paginating from token: {from_token or '(none)'}")

            # Fetch up to 100 messages (max) going backwards
            res = await client.room_messages(
                room_id=ROOM_ID,
                start=from_token,
                limit=100,
                direction="b",
            )

            if isinstance(res, RoomMessagesError):
                print(f"[ERROR] Could not fetch room messages: {res.message}")
                break

            if not res.chunk:
                print("[INFO] No more messages to process.")
                break

            print(f"[INFO] Processing {len(res.chunk)} messages...")
            for event in res.chunk:
                event_type = event.source.get("type")
                if event_type in ALLOWED_TYPES_TO_REDACT:
                    time.sleep(REDACTION_DELAY_SECONDS)
                    # Redact the message
                    redact_resp = await client.room_redact(
                        room_id=ROOM_ID,
                        event_id=event.event_id,
                        reason="Bulk cleanup"
                    )
                    if (isinstance(redact_resp, RoomRedactResponse)
                            and redact_resp.event_id):
                        total_redacted += 1
                        print(f"[INFO] Redacted event: {event.event_id} (type {event_type})")
                    else:
                        print(f"[ERROR] Failed to redact event: {event.event_id} (type {event_type})")

            from_token = res.end
            if not from_token:
                print("[INFO] No further pagination token, all done.")
                break

        print(f"[INFO] Finished redacting. Total messages redacted: {total_redacted}")

    finally:
        await client.close()

def main():
    asyncio.run(redact_all_messages())

if __name__ == "__main__":
    main()
