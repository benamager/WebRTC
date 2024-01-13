import asyncio
import json
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer

async def connect_to_peer_a(remote_sdp):
    peer_connection = RTCPeerConnection(
        configuration=RTCConfiguration([
            RTCIceServer("stun:stun.l.google:19302"),
            ]))

    # Handle ICE candidates (may need a signaling mechanism to communicate with Peer A)
    @peer_connection.on("icecandidate")
    def on_ice_candidate(candidate):
        print("New ICE candidate:", candidate)

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
    await peer_connection.setRemoteDescription(RTCSessionDescription(sdp=remote_sdp, type="offer"))

    # Create and set local answer
    local_answer = await peer_connection.createAnswer()
    await peer_connection.setLocalDescription(local_answer)

    return json.dumps({"sdp": peer_connection.localDescription.sdp, "type": peer_connection.localDescription.type})

# Main function to start the connection
async def main():
    remote_sdp_and_type = json.loads(input("Enter remote SDP from Peer A: "))
    remote_sdp_from_peer_a = RTCSessionDescription(sdp=remote_sdp_and_type["sdp"], type=remote_sdp_and_type["type"])

    answer_sdp = await connect_to_peer_a(remote_sdp_and_type["sdp"])
    print("------")
    print(answer_sdp)

    while True:
      await asyncio.sleep(1)  # Sleeps for 1 second

# Run the main function
asyncio.run(main())
