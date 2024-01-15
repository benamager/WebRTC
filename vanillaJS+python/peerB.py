import asyncio
import json
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer, RTCIceCandidate
import socketio

def create_peer_connection():
    return RTCPeerConnection(configuration=RTCConfiguration([RTCIceServer("stun:stun.l.google:19302")]))

async def main():
    peer_connection = create_peer_connection()

    # Socket.IO client
    sio = socketio.AsyncClient()

    @sio.event
    async def connect():
        print("Connected to the signaling server")

    @sio.event
    async def disconnect():
        print("Disconnected from the server")
        peer_connection.close()

    @sio.on('offer')
    async def handle_offer(offer_json):
        print('Received offer from Peer A')
        offer = json.loads(offer_json)

        # Send candidate to Peer A over signaling channel
        @peer_connection.on("ice_candidate")
        async def on_icecandidate(candidate):
            await sio.emit('ice_candidate', json.dumps({
                "candidate": candidate.candidate,
                "sdpMid": candidate.sdpMid,
                "sdpMLineIndex": candidate.sdpMLineIndex
            }))

        # Handle Data Channel
        @peer_connection.on("datachannel")
        def on_data_channel(channel):
            @channel.on("message")
            def on_message(message):
                print("Received message:", message)

            @channel.on("open")
            def on_open():
                print("dataChannel opened")

            @channel.on("close")
            def on_close():
                print("dataChannel closed")

        # Set remote description from Peer A
        await peer_connection.setRemoteDescription(RTCSessionDescription(sdp=offer["sdp"], type=offer["type"]))

        # Create and set local answer
        local_answer = await peer_connection.createAnswer()
        await peer_connection.setLocalDescription(local_answer)

        await sio.emit('answer', json.dumps({"sdp": peer_connection.localDescription.sdp, "type": peer_connection.localDescription.type}))
    
    # Handle ICE candidate messages
    @sio.on('ice_candidate')
    async def handle_icecandidate(data):
        try:
            print('Received ICE candidate from Peer A:', data)
            candidate_data = json.loads(data)

            # Parse the ICE candidate string
            parts = candidate_data['candidate'].split()

            # Create an RTCIceCandidate object
            ice_candidate = RTCIceCandidate(
                foundation=parts[0],
                component=int(parts[1]),
                protocol=parts[2].lower(),
                priority=int(parts[3]),
                ip=parts[4],
                port=int(parts[5]),
                type=parts[7],
                sdpMid=candidate_data.get('sdpMid'),
                sdpMLineIndex=candidate_data.get('sdpMLineIndex')
            )

            await peer_connection.addIceCandidate(ice_candidate)
            print("Added ICE candidate")
        except Exception as e:
            print(f"Error handling ICE candidate: {e}")

    # Connect to the Flask-SocketIO server
    await sio.connect('http://0.0.0.0:8080')

    # Keep the application running until it's stopped
    await sio.wait()

if __name__ == '__main__':
    asyncio.run(main())