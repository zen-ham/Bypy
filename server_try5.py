import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription

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
    print(pc.localDescription.sdp)

    # Wait for the answer to be entered manually
    sdp_answer = input("Paste the SDP answer here:\n")
    await pc.setRemoteDescription(RTCSessionDescription(sdp_answer, "answer"))

    # Keep the connection open
    while True:
        await asyncio.sleep(1)


asyncio.run(offerer())
