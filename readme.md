# WebRTC
A little backstory. I am tinkering around with hacking a RC-car to be controlled by a Raspberry PI with a 4G modem and tranfser its video feed to a browser - where we also control it, possible with controller support. This, as you might have guessed requires very little latency hence WebRTC.

## How does it work?

WebRTC provides standatralized APIs for handling peer to peer connections. But it isn't that easy. How would the two clients how to connect? How would they bypass NATs and firewalls? How would they....? Yes lots of questions - you will find the answers here.

You will need to understand a few concepts. Below you will see NAT, STUN, TURN, ICE, SDP and signaling which are all main parts of establishing a WebRTC connection.

### Network Address Translation (NAT)

Used in networking to enable private networks to communicate with the internet using a single public IP address. Its a common scenario when you are connected via WIFI or a mobile network. Only the router or modem you are connected to has a public IP address. Each device on the private network, however, is assigned a local IP address (like `192.168.1.10`). NAT plays a crucial role in managing and translating these IP addresses so your router or modem can communicate to the outside world on your behalf..

#### How NAT Works

When a device from your private network makes a request to the internet, the router creates a NAT table. This table is used to keep track of each devices connections and manage the translation between private and public IP addresses. Here is an example of what a NAT table might look like.

| Internal IP  | Internal Port | External IP  | Ext. Port | Dest IP       | Dest Port |
| ------------ | ------------- | ------------ | --------- | ------------- | --------- |
| 192.168.1.10 | 56234         | 203.0.113.45 | 44322     | 172.217.16.78 | 443       |

#### NAT Translation Methods

There are several methods of NAT translation, each differing in how they manage IP and port information. This is very complicated, but a simpler explanation is below. Only thing you must really know is that **WebRTC does not work properly with Symmetric NAT**.

1. **One-to-One NAT (Full-cone NAT)**: Maps a unique public IP address to a private IP address. This method is straightforward and allows for easy incoming connections.
2. **Address Restricted NAT**: Limits connections to a specific external IP address, but not a specific port. This method is more restrictive than One-to-One NAT.
3. **Port Restricted NAT**: Even more restrictive, this method allows connections only to a specific external IP address and port.
4. **Symmetric NAT**: The most restrictive form of NAT. Different external IP and port pairs are used for each destination. This method causes problems with WebRTC, because it requires consistent addressing for P2P communication.



### Session Traversal Utilities for NAT (STUN)

A server that each client ping to discover their public IP address and port assigned by a NAT device. It plays a vital role in facilitating communication between devices behind NAT and the wider Internet.

#### Key Features of STUN

- **Public IP Address and Port Discovery**: STUN allows a client behind a NAT to find out its public IP address and port. It does this by communicating with a STUN server located on the public internet.
- **Efficiency**: Running a STUN server is relatively cost-effective since its primary function is to inform clients about their public IP address and port, so no heavy lifting really. This is why Google serves free STUN servers e.g. (`stun1.l.google.com:19302`).



#### Traversal Using Relays around NAT (TURN)

A protocol that facilitates communication in scenarios where direct peer-to-peer connectivity is not possible, particularly in the case of symmetric NAT.

### How TURN Works

- **Relay Server**: TURN operates by utilizing a relay server. When devices are unable to establish a direct connection the TURN server acts as an intermediary, relaying packets between them.

- **Handling Audio and Video Packets**: TURN is used for transmitting real-time audio and video packets.

### Considerations for TURN

- **Resource Intensive**: Since TURN servers relay all traffic between communicating parties, they require significant bandwidth and processing power, especially when dealing with video and audio. Why Google does not provide this for free.



## Interactive Connectivity Establishment (ICE)

A protocol used in network communications to find all possible ways (known as **ICE candidates**) for establishing connectivity between peers, especially in environments behind a NAT.

### Key Functions of ICE

1. **Gathering ICE Candidates**: ICE collects different types of candidates representing the possible ways a device can be reached. These include.
   - **Local IP Addresses**: Direct IP addresses of the devices within the local network.
   - **Reflexive Addresses**: Public IP addresses as seen by the outside world, usually discovered through STUN.
   - **Relayed Addresses**: Addresses provided by TURN servers when direct peer-to-peer communication is not possible.
2. **Candidate Trickle**: The process of gathering ICE candidates is known as *"trickling."* This can take time, as it involves discovering and compiling a list of all possible local, reflexive, and relayed addresses for the device. So trickling send them as they are discovered of waiting for all. This both gives us faster connection speed and gather new ones after connection is established.
3. **Sharing via SDP**: Once all ICE candidates are collected, they are sent to the remote peer using the SDP.



## Session Description Protocol (SDP)

A standard format used in networking. Used in the context of WebRTC, for describing various session-related details.

### Understanding SDP

- **Description Format, Not really a Protocol?**: Despite its name, SDP is not a protocol that offers active communication or data transfer. Instead, it's a format that describes the multimedia communication session's details. It’s essentially a concise string of attributes.

- **Contents of SDP**: The SDP format is used to convey important information about the communication session, such as.
  - **ICE Candidates**: Information about possible ways to establish connectivity, as discovered by the ICE process.
  - **Networking Options**: Network-related details like IP addresses and ports.
  - **Media Options**: Specifications about the media being exchanged, including audio and video formats.
  - **Security Options**: Information on encryption and other security mechanisms to secure communication.

### SDP in WebRTC

The primary goal in a WebRTC setup is to generate an SDP at each end (by the respective users) and then exchange this SDP data between the two parties. This exchange is crucial for establishing a successful connection but is not handled by SDP itself, this is handled by signaling server. In summary, it serves as the backbone for describing and setting up communication sessions.



## Signaling in Networking

Signaling is a crucial process in networking, especially in the context of setting up communication sessions using the SDP.

### What is Signaling?

- **Role in SDP Communication**: In the realm of WebRTC and similar technologies, signaling refers to the method of exchanging SDP data between parties wishing to establish a communication session. 

- **Mechanism to Send SDP**: After generating the SDP data, which includes details about media formats, network options, and ICE candidates, each party needs to send this information to the other party they wish to communicate with. Signaling is the process used to accomplish this exchange.

In summary, signaling is a fundamental process in the setup of network communications, particularly when using WebRTC. It enables the exchange of crucial session information encapsulated in SDP.



## WebRTC Demystified

1. `A` wants to connect to `B`

2. `A` creates an "*offer*", it finds all ICE candidates, security options, audio/video options and generates the SDP. The offer is basically the SDP.

3. `A` signals the offer to `B` through websocket.

4. `B` creates the "*answer*" after setting `A`'s offer as it's local description.

   We have both a local and a remote SDP, one would be our own where the other one is other party's.

5. `B` signals the "*answer*" to `A`

6. Connection is created

In case of trickling we would not wait to find all ICE candidates, but send them as they are discovered.