from aiortc import RTCPeerConnection, RTCSessionDescription
import zlib, base64, pyperclip, asyncio, time, zhmiscellany, threading


zhmiscellany.misc.die_on_key()


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
        self.pastebin = zhmiscellany.pastebin.PasteBin(self.connection_data["pastebin"]["api_dev_key"], self.connection_data["pastebin"]["api_user_key"])

    def create_new_connection(self, session_code):
        connection_id = len(self.peer_datachannel_objects)
        self.peer_datachannel_objects.append({'data_channel': None, 'is_established': False, 'incoming_packets': [], 'outgoing_packets': [], 'ping': None, 'offer': {'data': None, 'hook': threading.Event()}, 'answer': None})
        def thread_async(function, args):
            asyncio.run(function(*args))
        zhmiscellany.processing.start_daemon(target=thread_async, args=(self._create_new_connection, (connection_id, session_code)))

    async def _create_new_connection(self, connection_id, session_code):
        pc = RTCPeerConnection()

        pc.configuration = self.connection_data['ice']

        data_channel = pc.createDataChannel("p2p")

        self.peer_datachannel_objects[connection_id]['data_channel'] = data_channel
        
        @pc.on("iceconnectionstatechange")
        async def on_ice_state_change():
            print(f"Connection {connection_id} state is now {pc.iceConnectionState}")
        
        # Print when the data channel opens
        @data_channel.on("open")
        def on_open():
            global connection_ping
            print(f"Connection {connection_id} was established")
            self.peer_datachannel_objects[connection_id]['is_established'] = True
            send_message("<auto>calculate_ping")  # Send a ping message
            connection_ping = time.time()

        connection_ping = 0

        # load any messages received on the data channel
        @data_channel.on("message")
        def on_message(message):
            global connection_ping
            self.peer_datachannel_objects[connection_id]['incoming_packets'].append(message)
            if type(message) == str:
                if message.startswith('<auto>'):
                    data = message.split('<auto>')[1]
                    if data == 'calculate_ping':
                        send_message('<auto>calculate_ping_response')
                    elif data == 'calculate_ping_response':
                        connection_ping = round((time.time() - connection_ping) * 1000)/2
                        self.peer_datachannel_objects[connection_id]['ping'] = connection_ping
                        send_message(f'<auto>set_connection_ping_{connection_ping}')
                    elif data.startswith('set_connection_ping_'):
                        connection_ping = data.split('_').pop()
                        self.peer_datachannel_objects[connection_id]['ping'] = connection_ping

        # Handle message sent
        def send_message(message):
            data_channel.send(message)
            print(f"Sent message: {message}")

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        offer_string = encode_sdp(pc.localDescription.sdp)

        self.pastebin.paste(data=offer_string, name=session_code, private=2, expire='10M')

        self.peer_datachannel_objects[connection_id]['offer']['data'] = session_code
        self.peer_datachannel_objects[connection_id]['offer']['hook'].set()

        await pc.setRemoteDescription(RTCSessionDescription(self.peer_datachannel_objects[connection_id]['answer']['answer'], "answer"))

    async def _connect(self, connection_id, session_code):
        pc = RTCPeerConnection()

        pc.configuration = self.connection_data['ice']

        @pc.on("iceconnectionstatechange")
        async def on_ice_state_change():
            print(f"Connection {connection_id} state is now {pc.iceConnectionState}")

        connection_ping = 0

        # Handle message sent
        def send_message(message):
            data_channel.send(message)
            print(f"Sent message: {message}")

        # Create a data channel
        @pc.on("datachannel")
        def on_data_channel(channel):
            global data_channel
            data_channel = channel

            # Print when the data channel opens
            @channel.on("open")
            def on_open():
                print("Data channel is open")

            # Print any messages received on the data channel
            @channel.on("message")
            def on_message(message):
                global connection_ping
                print(f"Received message: {message}")
                if '<auto>' in message:
                    data = message.split('<auto>')[1]
                    if data == 'calculate_ping':
                        send_message('<auto>calculate_ping_response')
                    elif data == 'calculate_ping_response':
                        connection_ping = round((time.time() - connection_ping) * 1000)
                        send_message(f'<auto>set_connection_ping_{connection_ping}')
                        self.peer_datachannel_objects[connection_id]['ping'] = connection_ping
                    elif data.startswith('set_connection_ping_'):
                        connection_ping = data.split('_').pop()
                        self.peer_datachannel_objects[connection_id]['ping'] = connection_ping

            def handle_chat():
                while True:
                    chat_message = input('')
                    send_message(chat_message)

            asyncio.to_thread(handle_chat)

        # Wait for the offer to be entered manually
        sdp_offer = decode_sdp(input("Paste the SDP offer here:\n"))
        await pc.setRemoteDescription(RTCSessionDescription(sdp_offer, "offer"))

        # Create and send an answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)


        join_code = encode_sdp(pc.localDescription.sdp)

        async def handle_chat():
            while True:
                chat_message = await asyncio.to_thread(input, '')
                send_message(chat_message)

        asyncio.create_task(handle_chat())

        # Keep the connection open
        while True:
            await asyncio.sleep(1)
    


ice_handler = MultiPeerManager()

# create pastebin with the offer and title and set offer to pastebin key
# 

session_code = zhmiscellany.string.get_universally_unique_string()

ice_handler.create_new_connection(session_code)

for instance in ice_handler.peer_datachannel_objects:
    instance['offer']['hook'].wait()
    print(instance['offer']['data'])
