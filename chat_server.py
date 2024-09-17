import sys

from aiortc import RTCPeerConnection, RTCSessionDescription
import zlib, base64, pyperclip, asyncio, time, zhmiscellany, threading, traceback


# Function to encode and compress SDP offer/answer using Base85
def encode_sdp(sdp):
    compressed_sdp = zlib.compress(sdp.encode('utf-8'))
    return base64.b85encode(compressed_sdp).decode('utf-8')


# Function to decode and decompress the encoded SDP using Base85
def decode_sdp(encoded_sdp):
    compressed_sdp = base64.b85decode(encoded_sdp.encode('utf-8'))
    return zlib.decompress(compressed_sdp).decode('utf-8')


class MultiPeerManager:
    def __init__(self):
        self.peer_datachannel_objects = []
        self.connection_data = zhmiscellany.fileio.read_json_file('connection_data.json')
        #self.pastebin = zhmiscellany.pastebin.PasteBin(self.connection_data["pastebin"]["api_dev_key"], self.connection_data["pastebin"]["api_user_key"])
        self.pastebin = zhmiscellany.pastebin.Pasteee(self.connection_data['pasteee']['app_key'])
        #self.paste_expire = '10M'
        self.paste_expire = 60*10
        self.num_established_connections = 0

    def search_pastebin_titles(self, search):
        pastes = self.pastebin.list_pastes(1000)
        for paste in pastes:
            if search in paste['paste_title']:
                return self.pastebin.raw_pastes(paste['paste_key']), paste

        raise Exception(f'No paste found for the given search ({search})')

    def send_message(self, connection_id, message):
        zhmiscellany.processing.start_daemon(target=self.thread_async, args=(self._send_message, (connection_id, message)))

    async def _send_message(self, connection_id, message):
        self.peer_datachannel_objects[connection_id]['data_channel'].send(message)
        print(f"Sent to connection {connection_id}: {message}")

    def thread_async(self, function, args):
        asyncio.run(function(*args))

    def create_new_connection(self, session_code):
        connection_id = len(self.peer_datachannel_objects)
        self.peer_datachannel_objects.append(self.new_connection_object(connection_id, session_code))

        zhmiscellany.processing.start_daemon(target=self.thread_async, args=(self._create_new_connection, (connection_id,)))

    def new_connection_object(self, connection_id, session_code):
        return {'data_channel': None, 'connection_id': connection_id, 'session_code': session_code, 'is_established': {'data': False, 'hook': threading.Event()}, 'incoming_packets': {'data': [], 'hook': threading.Event()}, 'outgoing_packets': [], 'ping': None, 'offer': {'data': None, 'hook': threading.Event()}, 'answer': {'data': None, 'hook': threading.Event()}}

    async def _create_new_connection(self, connection_id):
        print(f'Initializing connection {connection_id}')

        pc = RTCPeerConnection()

        pc.configuration = self.connection_data['ice']

        @pc.on("iceconnectionstatechange")
        async def on_ice_state_change():
            print(f"Connection {connection_id} state is now {pc.iceConnectionState}")

        data_channel = pc.createDataChannel("p2p")
        self.peer_datachannel_objects[connection_id]['data_channel'] = data_channel

        # Print when the data channel opens
        @data_channel.on("open")
        def on_open():
            global connection_ping
            print(f"Connection {connection_id} was established")
            self.peer_datachannel_objects[connection_id]['is_established']['data'] = True
            self.num_established_connections += 1
            self.peer_datachannel_objects[connection_id]['is_established']['hook'].set()
            self.send_message(connection_id, "<auto>calculate_ping")  # Send a ping message
            connection_ping = time.time()

        connection_ping = 0

        # load any messages received on the data channel
        @data_channel.on("message")
        def on_message(message):
            global connection_ping
            self.peer_datachannel_objects[connection_id]['incoming_packets']['data'].append(message)
            self.peer_datachannel_objects[connection_id]['incoming_packets']['hook'].set()
            self.peer_datachannel_objects[connection_id]['incoming_packets']['hook'] = threading.Event()
            if type(message) == str:
                if message.startswith('<auto>'):
                    data = message.split('<auto>')[1]
                    if data == 'calculate_ping':
                        self.send_message(connection_id, '<auto>calculate_ping_response')
                    elif data == 'calculate_ping_response':
                        connection_ping = round(((time.time() - connection_ping) * 1000)/2)
                        self.peer_datachannel_objects[connection_id]['ping'] = connection_ping
                        self.send_message(connection_id, f'<auto>set_connection_ping_{connection_ping}')
                    elif data.startswith('set_connection_ping_'):
                        connection_ping = data.split('_').pop()
                        self.peer_datachannel_objects[connection_id]['ping'] = connection_ping

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        offer_string = encode_sdp(pc.localDescription.sdp)

        offer_name = f'{self.peer_datachannel_objects[connection_id]["session_code"]}_offer_{connection_id}'
        print(f'Making offer with internal name {offer_name}')
        self.pastebin.paste(data=offer_string, name=offer_name, expire=self.paste_expire)

        self.peer_datachannel_objects[connection_id]['offer']['data'] = pc.localDescription.sdp
        self.peer_datachannel_objects[connection_id]['offer']['hook'].set()

        print(f'Connection {connection_id} posted SDP offer')

        sdp_answer = None
        while not sdp_answer:
            try:
                sdp_answer, paste = self.search_pastebin_titles(f'{self.peer_datachannel_objects[connection_id]["session_code"]}_answer')
            except:
                await asyncio.sleep(2)  # wait some seconds between checking to respect the api a little

        self.pastebin.delete_paste(paste['paste_key'])

        sdp_answer = decode_sdp(sdp_answer)

        await pc.setRemoteDescription(RTCSessionDescription(sdp_answer, "answer"))

        self.peer_datachannel_objects[connection_id]['answer']['data'] = sdp_answer
        self.peer_datachannel_objects[connection_id]['answer']['hook'].set()

        # Keep the connection open
        while pc.iceConnectionState not in ["closed", "failed", "disconnected"]:
            await asyncio.sleep(1)
        self.peer_datachannel_objects[connection_id]['is_established']['data'] = False
        self.num_established_connections -= 1
        print(f'Exiting connection {connection_id} thread')










    def connect(self, session_code):
        connection_id = len(self.peer_datachannel_objects)
        self.peer_datachannel_objects.append(self.new_connection_object(connection_id, session_code))

        zhmiscellany.processing.start_daemon(target=self.thread_async, args=(self._connect, (connection_id,)))

    async def _connect(self, connection_id):
        print(f'Initializing connection {connection_id}')
        pc = RTCPeerConnection()

        pc.configuration = self.connection_data['ice']

        @pc.on("iceconnectionstatechange")
        async def on_ice_state_change():
            print(f"Connection {connection_id} state is now {pc.iceConnectionState}")
            if pc.iceConnectionState == 'completed':
                print(f"Connection {connection_id} was established")
                self.peer_datachannel_objects[connection_id]['is_established']['data'] = True
                self.num_established_connections += 1
                self.peer_datachannel_objects[connection_id]['is_established']['hook'].set()

        connection_ping = 0

        # Create a data channel
        @pc.on("datachannel")
        def on_data_channel(channel):
            data_channel = channel

            self.peer_datachannel_objects[connection_id]['data_channel'] = data_channel

            # Print when the data channel opens
            @channel.on("open")
            def on_open():
                print(f"Connection {connection_id} was established")

            # Print any messages received on the data channel
            @channel.on("message")
            def on_message(message):
                global connection_ping
                self.peer_datachannel_objects[connection_id]['incoming_packets']['data'].append(message)
                self.peer_datachannel_objects[connection_id]['incoming_packets']['hook'].set()
                self.peer_datachannel_objects[connection_id]['incoming_packets']['hook'] = threading.Event()
                if '<auto>' in message:
                    data = message.split('<auto>')[1]
                    if data == 'calculate_ping':
                        self.send_message(connection_id, '<auto>calculate_ping_response')
                    elif data == 'calculate_ping_response':
                        connection_ping = round(((time.time() - connection_ping) * 1000)/2)
                        self.send_message(connection_id, f'<auto>set_connection_ping_{connection_ping}')
                        self.peer_datachannel_objects[connection_id]['ping'] = connection_ping
                    elif data.startswith('set_connection_ping_'):
                        connection_ping = data.split('_').pop()
                        self.peer_datachannel_objects[connection_id]['ping'] = connection_ping

        search = f'{self.peer_datachannel_objects[connection_id]["session_code"]}_offer'
        print(f'Searching for {search}')
        sdp_offer, paste = self.search_pastebin_titles(search)
        print(f'Found {paste["paste_title"]}')
        self.pastebin.delete_paste(paste['paste_key'])
        sdp_offer = decode_sdp(sdp_offer)

        await pc.setRemoteDescription(RTCSessionDescription(sdp_offer, "offer"))

        self.peer_datachannel_objects[connection_id]['offer']['data'] = sdp_offer
        self.peer_datachannel_objects[connection_id]['offer']['hook'].set()

        # Create and send an answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        answer_string = encode_sdp(pc.localDescription.sdp)

        answer_name = f'{self.peer_datachannel_objects[connection_id]["session_code"]}_answer_{connection_id}'
        print(f'Making offer with internal name {answer_name}')
        self.pastebin.paste(data=answer_string, name=answer_name, expire=self.paste_expire)

        self.peer_datachannel_objects[connection_id]['answer']['data'] = pc.localDescription.sdp
        self.peer_datachannel_objects[connection_id]['answer']['hook'].set()

        print(f'Connection {connection_id} posted SDP answer')

        # Keep the connection open
        while pc.iceConnectionState not in ["closed", "failed", "disconnected"]:
            await asyncio.sleep(1)
        self.peer_datachannel_objects[connection_id]['is_established']['data'] = False
        self.num_established_connections -= 1
        print(f'Exiting connection {connection_id} thread')


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
        messages = []
        while True:

            for connection in ice_handler.peer_datachannel_objects:
                while connection['incoming_packets']['data']:
                    received_message = connection['incoming_packets']['data'].pop(0)
                    messages.append([connection['connection_id'], received_message])
                    print(f'Received on connection {connection["connection_id"]}: {received_message}')

            if ice_handler.num_established_connections > 1:
                forwards = 0
                for message in messages:
                    for connection in ice_handler.peer_datachannel_objects:
                        if connection['connection_id'] != message[0] and instance['is_established']['data']:
                            ice_handler.send_message(connection['connection_id'], message[1])
                            forwards += 1
                messages = []

            event_hooks = []
            for connection in ice_handler.peer_datachannel_objects:
                event_hooks.append(connection['incoming_packets']['hook'])
            wait_for_any_event(event_hooks)

    zhmiscellany.processing.start_daemon(target=chat_relay)

    # maintain 1 free channel at all times to allow for new connections
    while True:
        ice_handler.create_new_connection(session_code)

        for instance in ice_handler.peer_datachannel_objects:
            instance['is_established']['hook'].wait()


def run_chat_client():
    zhmiscellany.misc.die_on_key('f8')

    session_code = input('Input session code:')
    ice_handler.connect(session_code)
    for connection in ice_handler.peer_datachannel_objects:
        connection['is_established']['hook'].wait()

    def show_incoming_chat():
        while True:
            for connection in ice_handler.peer_datachannel_objects:
                while connection['incoming_packets']['data']:
                    print(f"Received on connection {connection['connection_id']}: {connection['incoming_packets']['data'].pop(0)}")

            event_hooks = []
            for connection in ice_handler.peer_datachannel_objects:
                event_hooks.append(connection['incoming_packets']['hook'])
            wait_for_any_event(event_hooks)

    zhmiscellany.processing.start_daemon(target=show_incoming_chat)

    while True:
        user_message = input('')
        for connection in ice_handler.peer_datachannel_objects:
            if connection['is_established']['data']:
                ice_handler.send_message(connection['connection_id'], user_message)


ice_handler = MultiPeerManager()

choice = None
if len(sys.argv) != 1:
    if sys.argv[1] == 'server':
        choice = sys.argv[1]
    elif sys.argv[1] == 'client':
        choice = sys.argv[1]

if not choice:
    choice = zhmiscellany.misc.decide(['server', 'client'], 'Start as server or client?')

if choice == 'server':
    run_chat_server()
else:
    run_chat_client()