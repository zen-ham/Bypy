# answer.py
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.signaling import BYE

iceServers = [
    {"urls": "stun:stun.l.google.com:19302"},
    {"urls": "turn:turn.anyfirewall.com:443?transport=tcp", "username": "webrtc", "credential": "webrtc"}
]

async def run_answer():
    pc = RTCPeerConnection(configuration={"iceServers": iceServers})

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            print(f"Received: {message}")
            channel.send("Hello from the answerer!")

    offer_sdp = input("Enter the offer from your peer:\n")
    await pc.setRemoteDescription(RTCSessionDescription(offer_sdp, "offer"))

    # Generate answer and send it back
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    print("\nSend this answer back to your peer:")
    print(pc.localDescription.sdp)

    await BYE.wait_for_signal()

asyncio.run(run_answer())
