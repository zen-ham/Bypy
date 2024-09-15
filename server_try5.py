import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription
import base64


# Function to encode SDP offer/answer into a single string
def encode_sdp(sdp):
    return base64.urlsafe_b64encode(sdp.encode('utf-8')).decode('utf-8')


# Function to decode the encoded SDP back to its original form
def decode_sdp(encoded_sdp):
    return base64.urlsafe_b64decode(encoded_sdp.encode('utf-8')).decode('utf-8')



async def offerer():
    pc = RTCPeerConnection()

    # STUN / TURN server configuration
    pc.configuration = {
        "iceServers": [
            {"urls": "stun:stun.l.google.com:19302"},  # Public STUN server
            {"urls": "turn:global.relay.metered.ca:80", "username": "1edb644b728495f20713eec4", "credential": "80EQGekYuibNug72"},
        ]
    }

    # Create a data channel
    data_channel = pc.createDataChannel("game")
    data_channel.on("open", lambda: print("Data channel is open"))
    data_channel.on("message", lambda message: print(f"Received message: {message}"))

    # Create and send an offer
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    print("Offer sent. Please give this offer to the answerer:")
    print(encode_sdp(pc.localDescription.sdp))

    # Wait for the answer to be entered manually
    sdp_answer = decode_sdp(input("Paste the SDP answer here:\n"))
    await pc.setRemoteDescription(RTCSessionDescription(sdp_answer, "answer"))

    # Keep the connection open
    while True:
        await asyncio.sleep(1)


asyncio.run(offerer())
