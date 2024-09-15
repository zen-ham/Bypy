# offer.py
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.signaling import BYE

# A free public STUN and TURN server list
iceServers = [
    {"urls": "stun:stun.l.google.com:19302"},
    {"urls": "turn:turn.anyfirewall.com:443?transport=tcp", "username": "webrtc", "credential": "webrtc"}
]


async def run_offer():
    pc = RTCPeerConnection(configuration={"iceServers": iceServers})

    @pc.on("datachannel")
    async def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            print(f"Received: {message}")

    # Create data channel
    channel = pc.createDataChannel("test")

    # Set up peer connection and generate offer
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    print("Send this offer to your peer:")
    print(pc.localDescription.sdp)

    # Wait for answer
    answer_sdp = input("\nEnter the answer from your peer:\n")
    await pc.setRemoteDescription(RTCSessionDescription(answer_sdp, "answer"))

    # Send a message to the peer
    channel.send("Hello from the offerer!")

    await BYE.wait_for_signal()


asyncio.run(run_offer())
