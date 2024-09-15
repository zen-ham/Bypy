from aiortc import RTCPeerConnection, RTCSessionDescription
import zlib, base64, pyperclip, asyncio


# Function to encode and compress SDP offer/answer using Base85
def encode_sdp(sdp):
    compressed_sdp = zlib.compress(sdp.encode('utf-8'))
    return base64.b85encode(compressed_sdp).decode('utf-8')


# Function to decode and decompress the encoded SDP using Base85
def decode_sdp(encoded_sdp):
    compressed_sdp = base64.b85decode(encoded_sdp.encode('utf-8'))
    return zlib.decompress(compressed_sdp).decode('utf-8')


async def offerer():
    pc = RTCPeerConnection()

    # STUN / TURN server configuration
    pc.configuration = {
        "iceServers": [
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": "stun:stun.relay.metered.ca:80"},
            {"urls": "turn:global.relay.metered.ca:80", 'username': "1edb644b728495f20713eec4", 'credential': "80EQGekYuibNug72"},
            {'urls': "turn:global.relay.metered.ca:80?transport=tcp", 'username': "1edb644b728495f20713eec4", 'credential': "80EQGekYuibNug72"},
            {'urls': "turn:global.relay.metered.ca:443", 'username': "1edb644b728495f20713eec4", 'credential': "80EQGekYuibNug72"},
            {'urls': "turns:global.relay.metered.ca:443?transport=tcp", 'username': "1edb644b728495f20713eec4", 'credential': "80EQGekYuibNug72"},
        ]
    }

    # Monitor ICE connection state changes
    @pc.on("iceconnectionstatechange")
    async def on_ice_state_change():
        print(f"ICE connection state is now {pc.iceConnectionState}")
        if pc.iceConnectionState == "completed" or pc.iceConnectionState == "connected":
            # Check which ICE candidates are being used
            for transceiver in pc.getTransceivers():
                ice_transport = transceiver.sender.transport.iceTransport
                selected_pair = ice_transport.getSelectedCandidatePair()
                if selected_pair is not None:
                    local_candidate = selected_pair.local
                    remote_candidate = selected_pair.remote
                    print(f"Local candidate type: {local_candidate.type}")
                    print(f"Remote candidate type: {remote_candidate.type}")
                    if local_candidate.type == "relay" or remote_candidate.type == "relay":
                        print("Using TURN server (relay)")
                    else:
                        print("Direct or STUN-assisted connection (no TURN)")

    # Create a data channel
    data_channel = pc.createDataChannel("game")

    # Print when the data channel opens
    @data_channel.on("open")
    def on_open():
        print("Data channel is open")
        data_channel.send("ping from server")  # Send a ping message

    # Print any messages received on the data channel
    @data_channel.on("message")
    def on_message(message):
        print(f"Received message: {message}")

    # Create and send an offer
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    print("Offer sent. Please give this offer to the answerer:")
    join_code = encode_sdp(pc.localDescription.sdp)
    print(join_code)
    pyperclip.copy(join_code)
    print('(copied to clipboard)')

    # Wait for the answer to be entered manually
    sdp_answer = decode_sdp(input("Paste the SDP answer here:\n"))
    await pc.setRemoteDescription(RTCSessionDescription(sdp_answer, "answer"))

    # Keep the connection open
    while True:
        await asyncio.sleep(1)


asyncio.run(offerer())
