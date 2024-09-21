from aiortc import RTCPeerConnection, RTCSessionDescription
import zlib, base64, pyperclip, asyncio, time, zhmiscellany, threading, traceback, sys, json


class MultiPeerManager:
    def __init__(self):
        self.peer_datachannel_objects = []
        self.backup_datachannels = []
        self.connection_data = zhmiscellany.fileio.read_json_file('connection_data.json')
        #self.pastebin = zhmiscellany.pastebin.PasteBin(self.connection_data["pastebin"]["api_dev_key"], self.connection_data["pastebin"]["api_user_key"])
        self.pastebin = zhmiscellany.pastebin.Pasteee(self.connection_data['pasteee']['app_key'])
        #self.paste_expire = '10M'
        self.paste_expire = 60*10
        self.min_backup_connections = 2
        self.max_backup_connections = 4
        self.num_established_connections = 0
        self.processing_send = threading.Event()
        self.processing_send.set()
        self.max_sent_packets_per_second = 30  # THIS WILL BREAK WITH MORE THEN 2 PLAYERS
        self.last_sent_packet_time = 0

    def search_pastebin_titles(self, search):
        pastes = self.pastebin.list_pastes(1000)
        for paste in pastes:
            if search in paste['paste_title']:
                return self.pastebin.raw_pastes(paste['paste_key']), paste

        raise Exception(f'No paste found for the given search ({search})')

    def send_message(self, connection_id, message):
        zhmiscellany.processing.start_daemon(target=self.thread_async, args=(self._send_message, (connection_id, message)))

    async def _send_message(self, connection_id, message):
        if 'udp' in message:
            if not self.processing_send.is_set() or self.count_established_backups_for_connection(connection_id) < self.min_backup_connections:  # if the packet is in udp mode and another message is being processed then don't even bother waiting to send it and just discard it
                #print('discarded packet')
                return
        #print('sending packet')
        self.processing_send.wait()
        self.processing_send = threading.Event()
        data_channel = self.peer_datachannel_objects[connection_id]['data_channel']
        buf_before = data_channel.bufferedAmount
        try:
            data_channel.send(json.dumps(message))
        except Exception as e:
            print(f'Tried to send message to connection {connection_id} but failed: {e}')
        buf_after = data_channel.bufferedAmount
        zhmiscellany.misc.high_precision_sleep(1/self.max_sent_packets_per_second)
        self.processing_send.set()
        print(f"{buf_before} {buf_after} Sent to connection {connection_id}: {message}")

    def move_and_replace(self, lst, source_index, dest_index):
        obj = lst.pop(source_index)

        lst[dest_index] = obj

        return lst

    def thread_async(self, function, args):
        asyncio.run(function(*args))

    def wait_for_connection(self):
        event_hooks = []
        for instance in self.peer_datachannel_objects:
            if instance['as_backup'] is None:
                event_hooks.append(instance['is_established']['hook'])
        for event_hook in event_hooks:
            event_hook.wait()

    def encode_sdp(self, sdp):
        compressed_sdp = zlib.compress(sdp.encode('utf-8'))
        return base64.b85encode(compressed_sdp).decode('utf-8')

    def decode_sdp(self, encoded_sdp):
        compressed_sdp = base64.b85decode(encoded_sdp.encode('utf-8'))
        return zlib.decompress(compressed_sdp).decode('utf-8')

    def count_established_backups_for_connection(self, connection_id):
        backups = 0
        for connection in self.peer_datachannel_objects:
            if connection['as_backup'] == connection_id and connection['is_established']['data']:
                backups += 1
        return backups

    def find_newest_backup_id(self, connection_id):
        for connection in self.peer_datachannel_objects:
            if connection['as_backup'] == connection_id and connection['offer']['data'] is None:
                return connection['connection_id']
        raise Exception(f'no backup for connection {connection_id} found!')

    def find_newest_backup_answer_id(self, connection_id):
        for connection in reversed(self.peer_datachannel_objects):
            if connection['as_backup'] == connection_id:
                return connection['connection_id']
        raise Exception(f'no backup for connection {connection_id} found!')

    def find_valid_backup(self, connection_id):
        for connection in self.peer_datachannel_objects:
            if connection['as_backup'] == connection_id and connection['is_established']['data']:
                return connection['connection_id']
        raise Exception(f'no backup for connection {connection_id} found!')

    def handle_backup_offers(self, connection_id):
        while True:
            while self.count_established_backups_for_connection(connection_id) < self.max_backup_connections:  # while there isn't enough backups
                # create a backup
                self.create_new_connection(self.peer_datachannel_objects[connection_id]['session_code'], connection_id)
                time.sleep(0.1)
                backup_id = self.find_newest_backup_id(connection_id)
                self.peer_datachannel_objects[backup_id]['offer']['hook'].wait()
                backup_sdp_offer = self.peer_datachannel_objects[backup_id]['offer']['data']
                self.send_message(connection_id, {'relay': False, 'content': f"<auto>backup_offer_{backup_id}_{self.encode_sdp(backup_sdp_offer)}"})

            time.sleep(1)

    def handle_backup_answer(self, connection_id, backup_offer, remote_backup_id):
        self.connect(self.peer_datachannel_objects[connection_id]['session_code'], as_backup=connection_id, backup_offer=backup_offer)
        time.sleep(0.1)
        backup_id = self.find_newest_backup_answer_id(connection_id)
        print(f'handle_backup_answer waiting on connection {backup_id}')
        self.peer_datachannel_objects[backup_id]['answer']['hook'].wait()
        print(f'handle_backup_answer connection {backup_id} finished waiting')
        backup_sdp_answer = self.peer_datachannel_objects[backup_id]['answer']['data']
        self.send_message(connection_id, {'relay': False, 'content': f"<auto>backup_answer_{remote_backup_id}_{self.encode_sdp(backup_sdp_answer)}"})

    def new_connection_object(self, connection_id, session_code, as_backup, backup_offer=None):
        return {'data_channel': None, 'connection_id': connection_id, 'backups': 0, 'as_backup': as_backup, 'backup_offer': backup_offer, 'server_side_id': {'data': None, 'hook': threading.Event()}, 'session_code': session_code, 'is_established': {'data': False, 'hook': threading.Event()}, 'incoming_packets': {'data': [], 'hook': threading.Event()}, 'outgoing_packets': [], 'ping': None, 'offer': {'data': None, 'hook': threading.Event()}, 'answer': {'data': None, 'hook': threading.Event()}}

    def find_first_backup_with_no_answer(self, connection_id):
        for connection in self.peer_datachannel_objects:
            if connection['as_backup'] == connection_id and connection['answer']['data'] is None:
                return connection['connection_id']
        raise Exception(f'no backup for connection {connection_id} found!')

    def is_backup(self, connection_id):
        return True if self.peer_datachannel_objects[connection_id]['as_backup'] is not None else False





    def create_new_connection(self, session_code, as_backup=None, backup_offer=None):
        connection_id = len(self.peer_datachannel_objects)
        self.peer_datachannel_objects.append(self.new_connection_object(connection_id, session_code, as_backup, backup_offer))

        zhmiscellany.processing.start_daemon(target=self.thread_async, args=(self._create_new_connection, (connection_id,)))

    async def _create_new_connection(self, connection_id):
        is_backup = self.is_backup(connection_id)
        if not is_backup:
            print(f'Initializing connection {connection_id}')
        else:
            print(f'Initializing backup connection {connection_id}')
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
            if not is_backup:
                self.num_established_connections += 1
            self.peer_datachannel_objects[connection_id]['is_established']['hook'].set()
            self.peer_datachannel_objects[connection_id]['is_established']['hook'] = threading.Event()
            self.send_message(connection_id, {'relay': False, 'content': "<auto>calculate_ping"})  # Send a ping message
            self.send_message(connection_id, {'relay': False, 'content': f"<auto>set_connection_id_{connection_id}"})  # Send set client id
            connection_ping = time.time()
            if self.peer_datachannel_objects[connection_id]['as_backup'] is None:  # if we're not a backup
                zhmiscellany.processing.start_daemon(target=self.handle_backup_offers, args=(connection_id,))


        connection_ping = 0

        # load any messages received on the data channel
        @data_channel.on("message")
        def on_message(message):
            global connection_ping
            message = json.loads(message)
            self.peer_datachannel_objects[connection_id]['incoming_packets']['data'].append(message)
            self.peer_datachannel_objects[connection_id]['incoming_packets']['hook'].set()
            self.peer_datachannel_objects[connection_id]['incoming_packets']['hook'] = threading.Event()
            if type(message['content']) == str:
                if message['content'].startswith('<auto>'):
                    data = message['content'].split('<auto>')[1]
                    if data == 'calculate_ping_response':
                        connection_ping = round(((time.time() - connection_ping) * 1000)/2)
                        self.peer_datachannel_objects[connection_id]['ping'] = connection_ping
                        self.send_message(connection_id, {'relay': False, 'content': f'<auto>set_connection_ping_{connection_ping}'})
                    elif data.startswith('set_connection_ping_'):
                        connection_ping = data.split('_').pop()
                        self.peer_datachannel_objects[connection_id]['ping'] = connection_ping
                    elif data.startswith('backup_answer_'):
                        backup_answer = '_'.join(data.split('_')[3:])
                        print(f'EXTRACTED ANSWER: {backup_answer}')
                        backup_id = int(data.split('_')[2])
                        #backup_id = self.find_first_backup_with_no_answer(connection_id)
                        self.peer_datachannel_objects[backup_id]['answer']['data'] = self.decode_sdp(backup_answer)
                        self.peer_datachannel_objects[backup_id]['answer']['hook'].set()

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        offer_string = self.encode_sdp(pc.localDescription.sdp)

        if not is_backup:
            offer_name = f'{self.peer_datachannel_objects[connection_id]["session_code"]}_offer_{connection_id}'
            print(f'Making offer with internal name {offer_name}')
            self.pastebin.paste(data=offer_string, name=offer_name, expire=self.paste_expire)

        self.peer_datachannel_objects[connection_id]['offer']['data'] = pc.localDescription.sdp
        self.peer_datachannel_objects[connection_id]['offer']['hook'].set()

        print(f'Connection {connection_id} posted SDP offer')

        if not is_backup:
            sdp_answer = None
            while not sdp_answer:
                try:
                    sdp_answer, paste = self.search_pastebin_titles(f'{self.peer_datachannel_objects[connection_id]["session_code"]}_answer')
                except:
                    await asyncio.sleep(2)  # wait some seconds between checking to respect the api a little

            self.pastebin.delete_paste(paste['paste_key'])

        if not is_backup:
            sdp_answer = self.decode_sdp(sdp_answer)
        else:
            self.peer_datachannel_objects[connection_id]['answer']['hook'].wait()
            sdp_answer = self.peer_datachannel_objects[connection_id]['answer']['data']

        print(f'Connection {connection_id} using answer')

        await pc.setRemoteDescription(RTCSessionDescription(sdp_answer, "answer"))

        if not is_backup:
            self.peer_datachannel_objects[connection_id]['answer']['data'] = sdp_answer
            self.peer_datachannel_objects[connection_id]['answer']['hook'].set()

        # Keep the connection open
        while pc.iceConnectionState not in ["closed", "failed", "disconnected"]:
            await asyncio.sleep(1)
        #self.peer_datachannel_objects[connection_id]['is_established']['data'] = False
        #self.peer_datachannel_objects[connection_id]['is_established']['hook'].set()

        replacement_id = self.find_valid_backup(connection_id)
        self.move_and_replace(self.peer_datachannel_objects, connection_id, replacement_id)

        print(f'Exiting connection {connection_id} thread')










    def connect(self, session_code, as_backup=None, backup_offer=None):
        connection_id = len(self.peer_datachannel_objects)
        self.peer_datachannel_objects.append(self.new_connection_object(connection_id, session_code, as_backup, backup_offer))

        zhmiscellany.processing.start_daemon(target=self.thread_async, args=(self._connect, (connection_id,)))

    async def _connect(self, connection_id):
        is_backup = self.is_backup(connection_id)

        if not is_backup:
            print(f'Initializing connection {connection_id}')
        else:
            print(f'Initializing backup connection {connection_id}')

        pc = RTCPeerConnection()

        pc.configuration = self.connection_data['ice']

        @pc.on("iceconnectionstatechange")
        async def on_ice_state_change():
            print(f"Connection {connection_id} state is now {pc.iceConnectionState}")
            if pc.iceConnectionState == 'completed':
                print(f"Connection {connection_id} was established")
                self.peer_datachannel_objects[connection_id]['is_established']['data'] = True
                if not is_backup:
                    self.num_established_connections += 1
                self.peer_datachannel_objects[connection_id]['is_established']['hook'].set()
                self.peer_datachannel_objects[connection_id]['is_established']['hook'] = threading.Event()

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

            @channel.on("message")
            def on_message(message):
                #if self.peer_datachannel_objects[connection_id]['as_backup'] is not None:
                #    if type(message['content']) == str:
                #        if '<auto>' in message['content']:
                #
                #else:
                global connection_ping
                message = json.loads(message)
                self.peer_datachannel_objects[connection_id]['incoming_packets']['data'].append(message)
                self.peer_datachannel_objects[connection_id]['incoming_packets']['hook'].set()
                self.peer_datachannel_objects[connection_id]['incoming_packets']['hook'] = threading.Event()
                if type(message['content']) == str:
                    if '<auto>' in message['content']:
                        data = message['content'].split('<auto>')[1]
                        if data == 'calculate_ping':
                            self.send_message(connection_id, {'relay': False, 'content': '<auto>calculate_ping_response'})
                        elif data.startswith('set_connection_ping_'):
                            connection_ping = data.split('_').pop()
                            self.peer_datachannel_objects[connection_id]['ping'] = connection_ping
                        elif data.startswith('set_connection_id_'):
                            self.peer_datachannel_objects[connection_id]['server_side_id']['data'] = data.split('_').pop()
                            self.peer_datachannel_objects[connection_id]['server_side_id']['hook'].set()
                        elif data.startswith('backup_offer_'):
                            backup_offer = '_'.join(data.split('_')[3:])
                            print(f'EXTRACTED OFFER: {backup_offer}')
                            backup_id = data.split('_')[2]
                            zhmiscellany.processing.start_daemon(target=self.handle_backup_answer, args=(connection_id, backup_offer, backup_id))
                            #self.create_new_connection(self.peer_datachannel_objects[connection_id]['session_code'], as_backup=connection_id, backup_offer=backup_offer)

        if not is_backup:
            search = f'{self.peer_datachannel_objects[connection_id]["session_code"]}_offer'
            print(f'Searching for {search}')
            sdp_offer, paste = self.search_pastebin_titles(search)
            print(f'Found {paste["paste_title"]}')
            self.pastebin.delete_paste(paste['paste_key'])
            sdp_offer = self.decode_sdp(sdp_offer)
        else:
            sdp_offer = self.decode_sdp(self.peer_datachannel_objects[connection_id]['backup_offer'])

        print(f'Connection {connection_id} using offer {sdp_offer}')

        await pc.setRemoteDescription(RTCSessionDescription(sdp_offer, "offer"))

        self.peer_datachannel_objects[connection_id]['offer']['data'] = sdp_offer
        self.peer_datachannel_objects[connection_id]['offer']['hook'].set()

        # Create and send an answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        answer_string = self.encode_sdp(pc.localDescription.sdp)

        if not is_backup:
            answer_name = f'{self.peer_datachannel_objects[connection_id]["session_code"]}_answer_{connection_id}'
            print(f'Making offer with internal name {answer_name}')
            self.pastebin.paste(data=answer_string, name=answer_name, expire=self.paste_expire)

        self.peer_datachannel_objects[connection_id]['answer']['data'] = pc.localDescription.sdp
        self.peer_datachannel_objects[connection_id]['answer']['hook'].set()

        print(f'Connection {connection_id} posted SDP answer')

        # Keep the connection open
        while pc.iceConnectionState not in ["closed", "failed", "disconnected"]:
            await asyncio.sleep(1)

        replacement_id = self.find_valid_backup(connection_id)
        self.move_and_replace(self.peer_datachannel_objects, connection_id, replacement_id)
        #self.peer_datachannel_objects[connection_id]['is_established']['data'] = False
        #self.peer_datachannel_objects[connection_id]['is_established']['hook'].set()
        print(f'Exiting connection {connection_id} thread')