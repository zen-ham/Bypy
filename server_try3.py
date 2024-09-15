import asyncio
import json
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.signaling import BYE

# Configure STUN/TURN server (replace with your TURN server details)
TURN_SERVER = {
    'urls': 'turn:your.turn.server:3478',
    'username': 'user',
    'credential': 'password'
}

async def run_server():
    pc = RTCPeerConnection(iceServers=[TURN_SERVER])

    async def handle_offer(offer):
        print("Received Offer:", offer)
        await pc.setRemoteDescription(offer)

        # Create and send an answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        print("Sending Answer:", json.dumps({'sdp': pc.localDescription.sdp, 'type': pc.localDescription.type}))

    # Wait for offer
    offer_json = input("Enter the offer JSON from Peer B:\n")
    offer = RTCSessionDescription(**json.loads(offer_json))
    await handle_offer(offer)

    # Close connection when 'bye' is received
    await pc.on('datachannel', lambda channel: channel.on('message', lambda msg: print("Received message:", msg)))
    await pc.on('iceconnectionstatechange', lambda: print(f"ICE Connection State: {pc.iceConnectionState}"))
    await asyncio.sleep(5)

    await pc.close()

if __name__ == "__main__":
    asyncio.run(run_server())
