# WebRTC
## I am learning WebRTC, and here is my playground.

I am tinkering around with hacking a RC-car to be controlled by a Raspberry PI with a 4G modem and tranfser its video feed to a browser - where we also control it, possible with controller support. This, as you might have guessed, requires very little latency hence WebRTC.

## How does it work?

Normally when we want to connect two clients we would use something like websockets or UDP to relay control signals or video from RPI to browser, but.... latency. Data needs to travel first from client A to the server, get handled and then passed onto client B, but with WebRTC we get a peer to peer connection, perfect!

But it isn't that easy. How would the two clients know who to connect to? Yes, the signaling server. This is a simple Websocket server that passes SDP and ICE candidates to each other and lets them connect.

Trickle ICE, is a way to send ICE candidates as they are discovered, instead of waiting for all of them to be discovered and then send them all at once. This allows us to start the connection faster and send candidates as they are discovered.

... to be continued