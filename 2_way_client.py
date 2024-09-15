import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.signaling import BYE

pc = RTCPeerConnection()

# Adding STUN and TURN servers to the ICE candidate gathering
pc.configuration = [
        {"urls": "stun:stun.l.google.com:19302"},  # Public STUN server
        {"urls": "stun:stun.relay.metered.ca:80"},
        {"urls": "turn:global.relay.metered.ca:80", 'username': "1edb644b728495f20713eec4", 'credential': "80EQGekYuibNug72"},
        {'urls': "turn:global.relay.metered.ca:80?transport=tcp", 'username': "1edb644b728495f20713eec4", 'credential': "80EQGekYuibNug72"},
        {'urls': "turn:global.relay.metered.ca:443", 'username': "1edb644b728495f20713eec4", 'credential': "80EQGekYuibNug72"},
        {'urls': "turns:global.relay.metered.ca:443?transport=tcp", 'username': "1edb644b728495f20713eec4", 'credential': "80EQGekYuibNug72"},
    ]


# Data channel setup (for peer-to-peer data, e.g., for a game)
data_channel = pc.createDataChannel("game")


async def send_offer():
    # Create and send an offer
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    # This would be where you send the offer to the peer
    print(f"Offer sent:\n{offer.sdp}")


async def handle_answer(sdp):
    # This would be where you receive the peer's answer
    await pc.setRemoteDescription(RTCSessionDescription(sdp, "answer"))


asyncio.run(send_offer())
