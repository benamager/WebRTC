'''
Stream video from a Raspberry Pi using aiortc and latest libcamera stack to a web browser via WebRTC.
This is fantastic and has very low latency.

Tested on a Raspberry Pi 4 with Camera Module v3 running Raspberry Pi OS Lite (Bookworm, 64-bit)
'''
import json
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer, RTCIceCandidate, VideoStreamTrack
from picamera2 import Picamera2
import socketio
from av import VideoFrame
import cv2

# Constants
CAMERA_SIZE = (640, 480)
SIGNALING_SERVER_URL = 'http://192.168.1.139:8080'
SIGNALING_SERVER_TOKEN = "secureTokenGoesHere"

# Camera instance
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": CAMERA_SIZE}))
picam2.start()

class Picamera2Track(VideoStreamTrack):
    def __init__(self, camera):
        super().__init__()
        self.camera = camera
        self.running = True

    async def recv(self):
        while self.running:
            try:
                # Capture a frame from the camera
                frame = self.camera.capture_array()

                # Convert RGBA to BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

                # Convert the frame to the correct format
                av_frame = VideoFrame.from_ndarray(frame, format="bgr24")

                # Manage timestamps
                av_frame.pts, av_frame.time_base = await self.next_timestamp()

                # Return the frame
                return av_frame
            except Exception as e:
                print(f"Error capturing frame: {e}")
                # If an error occurs, stop the loop
                self.running = False

    @property
    def kind(self):
        return "video"

def create_peer_connection():
    return RTCPeerConnection(configuration=RTCConfiguration([RTCIceServer("stun:fr-turn1.xirsys.com")]))

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
        await peer_connection.close()

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
        try:
            await peer_connection.setRemoteDescription(RTCSessionDescription(sdp=offer["sdp"], type=offer["type"]))
        except Exception as e:
            print(f"Error setting remote description: {e}")

        video_track = Picamera2Track(picam2)
        peer_connection.addTrack(video_track)

        # Create and set local answer
        try:
            local_answer = await peer_connection.createAnswer()
            await peer_connection.setLocalDescription(local_answer)
        except Exception as e:
            print(f"Error creating or setting local answer: {e}")

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

    # Connect to signaling server
    try:
        await sio.connect(SIGNALING_SERVER_URL, 
                    query={"token": SIGNALING_SERVER_TOKEN})
    except Exception as e:
        print(f"Error connecting to signaling server: {e}")
        return

    # Keep application running
    await sio.wait()

if __name__ == '__main__':
    asyncio.run(main())