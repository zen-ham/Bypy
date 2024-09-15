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


async def answerer():
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

    # Monitor ICE candidates
    @pc.on("icecandidate")
    async def on_ice_candidate(candidate):
        if candidate is None:
            print("ICE gathering complete")
        elif candidate.candidate.startswith("relay"):
            print("Using TURN server for relaying")
        elif candidate.candidate.startswith("srflx"):
            print("Using STUN server for NAT traversal")
        elif candidate.candidate.startswith("host"):
            print("Using direct peer-to-peer (local network)")

    # Create a data channel
    @pc.on("datachannel")
    def on_data_channel(channel):
        # Print when the data channel opens
        @channel.on("open")
        def on_open():
            print("Data channel is open")

        # Print any messages received on the data channel
        @channel.on("message")
        def on_message(message):
            print(f"Received message: {message}")
            channel.send("pong from client")  # Respond with a pong message

    # Wait for the offer to be entered manually
    sdp_offer = decode_sdp(input("Paste the SDP offer here:\n"))
    await pc.setRemoteDescription(RTCSessionDescription(sdp_offer, "offer"))

    # Create and send an answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    join_code = encode_sdp(pc.localDescription.sdp)
    print("Answer sent. Please give this answer to the offerer:")
    print(join_code)
    pyperclip.copy(join_code)
    print('(copied to clipboard)')

    # Keep the connection open
    while True:
        await asyncio.sleep(1)


asyncio.run(answerer())
