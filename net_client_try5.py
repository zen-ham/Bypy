import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription

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
    sdp_offer = input("Paste the SDP offer here:\n")
    await pc.setRemoteDescription(RTCSessionDescription(sdp_offer, "offer"))

    # Create and send an answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    print("Answer sent. Please give this answer to the offerer:")
    print(pc.localDescription.sdp)

    # Keep the connection open
    while True:
        await asyncio.sleep(1)


asyncio.run(answerer())
