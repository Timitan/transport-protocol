import struct
import random
from socket import *


def main():
    server_name = 'localhost'
    server_port = 12000
    receiver_window = 10
    header_length = 6  # BBI = 1 + 1 + 4 = 6 bytes
    loss_probability = 0.2

    server_socket = socket(AF_INET,SOCK_DGRAM)
    server_socket.bind((server_name, server_port))

    connections = {}

    print("The server is ready to receive")
    while True:
        message, client_address = server_socket.recvfrom(2048)

        # simulate loss by receiving packet and continuing
        if random.random() < loss_probability:
            print("Dropped packet: " + message[header_length:].decode())
            continue

        # header flags
        conn_flag = 0
        fin_flag = 0
        ack_seq = 0

        # CONNECTION ORIENTED AND FEEDBACK:
        # Split the decoded_msg up to find the header fields (CONN, FIN, ACK, PAYLOAD, etc)
        if client_address in connections:
            client_conn = connections[client_address]
            (conn_flag, fin_flag, seq_num) = struct.unpack("!BBI", message[:header_length])
            decoded_message = message[header_length:].decode()
            print("Received: " + decoded_message)

            # CONNECTION ORIENTED: Terminate connection once fin_flag is set, Note: only one connection supported
            if fin_flag == 1:
                print("Connection Close for " + str(client_conn))
                del connections[client_address]
                payload = b""
            else:
                # ERROR AND LOSS DETECTION: Acknowledgements for sequence numbers for packets
                if seq_num != client_conn["ACK"]:
                    # If it isn't the expected ACK number, Re-ACK highest sequence number
                    ack_seq = client_conn["ACK"]
                else:
                    # Update the highest sequence number for this connection
                    client_conn["ACK"] = seq_num + 1
                    ack_seq = client_conn["ACK"]

                payload = b""
        else:
            print("Connected to: " + str(client_address))
            connections[client_address] = {"ACK": ack_seq}
            payload = b""
            conn_flag = 1

        # FLOW CONTROL: Advertise receiver window size to prevent senders from overwhelming the receiver
        client_message = struct.pack("!BBII", conn_flag, fin_flag, ack_seq, receiver_window) + payload

        # Send window size to sender for flow control
        server_socket.sendto(client_message, client_address)

        if fin_flag == 1:
            break

    server_socket.close()


if __name__ == "__main__":
    main()