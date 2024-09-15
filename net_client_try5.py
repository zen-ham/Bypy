import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription
import base64


# Function to encode SDP offer/answer into a single string
def encode_sdp(sdp):
    return base64.urlsafe_b64encode(sdp.encode('utf-8')).decode('utf-8')


# Function to decode the encoded SDP back to its original form
def decode_sdp(encoded_sdp):
    return base64.urlsafe_b64decode(encoded_sdp.encode('utf-8')).decode('utf-8')



async def answerer():
    pc = RTCPeerConnection()

    # STUN / TURN server configuration
    pc.configuration = {
        "iceServers": [
            {"urls": "stun:stun.l.google.com:19302"},  # Public STUN server
            {"urls": "turn:global.relay.metered.ca:80", "username": "1edb644b728495f20713eec4", "credential": "80EQGekYuibNug72"},
        ]
    }

    # Handle incoming data channel messages
    @pc.on("datachannel")
    def on_datachannel(channel):
        print(f"Data channel {channel.label} is created")
        channel.on("message", lambda message: print(f"Received message: {message}"))

    # Receive the offer from the offerer
    sdp_offer = decode_sdp(input("Paste the SDP offer here:\n"))
    await pc.setRemoteDescription(RTCSessionDescription(sdp_offer, "offer"))

    # Create and send an answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    print("Answer sent. Please give this answer to the offerer:")
    print(encode_sdp(pc.localDescription.sdp))

    # Keep the connection open
    while True:
        await asyncio.sleep(1)


asyncio.run(answerer())
