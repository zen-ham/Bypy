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

async def run_client():
    pc = RTCPeerConnection(iceServers=[TURN_SERVER])

    # Create offer and print it
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    print("Sending Offer:", json.dumps({'sdp': pc.localDescription.sdp, 'type': pc.localDescription.type}))

    # Wait for answer from Peer A
    answer_json = input("Enter the answer JSON from Peer A:\n")
    answer = RTCSessionDescription(**json.loads(answer_json))
    await pc.setRemoteDescription(answer)

    # Open a data channel and send a message
    data_channel = pc.createDataChannel("test")
    data_channel.on('open', lambda: data_channel.send("Hello from Peer B!"))

    # Close connection when 'bye' is received
    await pc.on('iceconnectionstatechange', lambda: print(f"ICE Connection State: {pc.iceConnectionState}"))
    await asyncio.sleep(5)

    await pc.close()

if __name__ == "__main__":
    asyncio.run(run_client())
