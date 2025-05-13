# transport-protocol
A simple transport layer protocol built on top of UDP for a data communications course. 

## Description
This mini-project is completed for a data communications course at Simon Fraser University (SFU). It involves implementing a flavor of connection-oriented, reliable, and pipelined protocol with flow and congestion control mechanisms. The data exchanged only involves chat messages between a client and a server where messages may not be received on either end correctly due to simulated data loss. 

For more information, the included pdf report in this repository covers this project and its mechanisms more in depth.

## Requirements
``>= python 3.9.1``

This project was tested with python 3.9.1 but other versions may be sufficient.  

## Usage
To use this project, run the server file first in one console: <br/>
``python udp_server.py``<br/>

Then the client file in another console: <br/>
``python udp_client.py``

After doing so, a connection will be established automatically and the client will take in any message to be sent to the server. Information will be displayed in the console as the server and client communicate with data loss simulated.

## Group Members
- Amy Jia Ying Tan
- Timothy Tan

