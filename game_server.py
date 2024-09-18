import threading, zhmiscellany, pyperclip, time, sys
from ice_manager import MultiPeerManager


def wait_for_any_event(events):
    if not events:
        return
    # This shared event will be set by any of the threads
    shared_event = threading.Event()

    # Function for each thread to wait on its respective event
    def wait_on_event(event):
        event.wait()  # Wait for the event to be set
        shared_event.set()  # Set the shared event when this one is triggered

    # Create a thread for each event and start it
    threads = []
    for event in events:
        t = threading.Thread(target=wait_on_event, args=(event,))
        threads.append(t)
        t.start()

    # Block until any of the events has been set (via shared_event)
    shared_event.wait()


def run_chat_server():
    zhmiscellany.misc.die_on_key()

    session_code = zhmiscellany.string.get_universally_unique_string()

    print(f'Your server join code: {session_code} (copied to clipboard)')
    pyperclip.copy(session_code)

    def chat_relay():
        time.sleep(0.1)  # just make sure ice_handler has some sort of connection created
        messages = []
        while True:

            for connection in ice_handler.peer_datachannel_objects:
                while connection['incoming_packets']['data']:
                    received_message = connection['incoming_packets']['data'].pop(0)
                    if received_message['relay']:
                        messages.append([connection['connection_id'], received_message])
                        #print(f'Received on connection {connection["connection_id"]}: {received_message}')

            if ice_handler.num_established_connections > 1:  # if there's more then one person to forward chat to
                forwards = 0
                for message in messages:
                    for connection in ice_handler.peer_datachannel_objects:
                        if connection['connection_id'] != message[0] and connection['is_established']['data']:
                            message[1]['relay'] = False
                            ice_handler.send_message(connection['connection_id'], message[1])
                            forwards += 1
                messages = []
            else:
                # throw away packets if there's no onw to send them to
                messages = []

            event_hooks = []
            for connection in ice_handler.peer_datachannel_objects:
                event_hooks.append(connection['incoming_packets']['hook'])
            wait_for_any_event(event_hooks)

    zhmiscellany.processing.start_daemon(target=chat_relay)

    # maintain 1 free channel at all times to allow for new connections
    while True:
        ice_handler.create_new_connection(session_code)

        ice_handler.wait_for_connection()


ice_handler = MultiPeerManager()


run_chat_server()
