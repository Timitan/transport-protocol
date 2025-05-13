import struct
import time
from socket import *
from _thread import *
import threading
import random

lock1 = threading.Lock()
lock2 = threading.Lock()
conn_lock = threading.Lock()

server_name = 'localhost'
server_port = 12000
window_size = 3
receiver_window = window_size
message_array = []
time_oldest_packet = -1
base = 0
timeout = 2
loss_probability = 0.2
connected = False
closed = False

# header flags
conn_flag = 1
fin_flag = 0
seq_num = 0
header_length = 6  # BBI = 1 + 1 + 4 = 6 bytes
receiver_header_length = 10  # BBI = 1 + 1 + 4 + 4 = 10 bytes
packet_length = 12

client_socket = socket(AF_INET, SOCK_DGRAM)


def chunk_byte_string(string, length):
    return list(string[0+i:length+i] for i in range(0, len(string), length))


def construct_packet(data):
    header = struct.pack("!BBI", conn_flag, fin_flag, seq_num)
    constructed_packet = header + data

    return constructed_packet


def deconstruct_packet(data):
    (conn_flag1, fin_flag1, ack_num1, receiver_window1) = struct.unpack("!BBII", data[:receiver_header_length])
    payload_message = data[receiver_header_length:].decode()

    return conn_flag1, fin_flag1, ack_num1, payload_message, receiver_window1


def send_packets_in_window():
    global seq_num, base, window_size, message_array
    # PIPELINING PROTOCOL: Send multiple packets within window
    while seq_num < base + window_size and seq_num < len(message_array):
        packet_payload = message_array[seq_num]
        print("\nPIPELINING - Sent packet | payload: " + packet_payload.decode() + " | baseNum: " + str(base) + " | seqNum: " + str(seq_num))
        packet = construct_packet(packet_payload)
        seq_num += 1

        client_socket.sendto(packet, (server_name, server_port))


# Timeout for feedback mechanism
def timer():
    global conn_flag, time_oldest_packet, seq_num, base, window_size, receiver_window

    # ERROR AND LOSS RECOVERY: Set timer for oldest un-ACKED packet
    while conn_flag == 1:
        delta = time.time() - time_oldest_packet

        # Timeout only if there is data to send
        if delta > timeout and base < seq_num:
            seq_num = base
            send_packets_in_window()
            time_oldest_packet = time.time()

            # CONGESTION CONTROL: Half sender window by half after loss
            halved_window = int(window_size / 2)

            # FLOW CONTROL: Limit window size to receiver window to prevent overwhelming it
            new_window_size = min(max(1, halved_window), receiver_window)

            print("\nCONGESTION CONTROL - Halved Window Size: " + str(window_size) + "->" + str(new_window_size))
            window_size = new_window_size


def send_connection_request():
    global conn_flag, fin_flag, seq_num
    hdr = struct.pack("!BBI", conn_flag, fin_flag, seq_num)
    client_message = hdr + b'Connection Info'
    client_socket.sendto(client_message, (server_name, server_port))
    print("\nINFO - Connection Info Sent")


def connection_timer():
    global time_oldest_packet, fin_flag

    # CONNECTION-ORIENTED PROTOCOL: Closing and initiating the connection
    while not connected and not closed:
        delta = time.time() - time_oldest_packet

        if delta > timeout:
            send_connection_request()
            time_oldest_packet = time.time()


def send_data():
    global conn_flag, fin_flag, seq_num, base, time_oldest_packet, connected, closed, receiver_window, window_size

    # CONNECTION-ORIENTED PROTOCOL:
    # Automatically send/ resend connection messages
    time_oldest_packet = time.time()
    start_new_thread(connection_timer, ())
    send_connection_request()
    print("INFO - Initializing Connection...")

    server_message, server_address = client_socket.recvfrom(2048)
    (conn_flag, fin_flag, seq_num, receiver_window) = struct.unpack("!BBII", server_message[:receiver_header_length])
    connected = True

    # FLOW CONTROL: Ensure starting window size is limited to the receiver window size
    window_size = min(window_size, receiver_window)

    print("INFO - Connected")

    start_new_thread(receive_packets, ())
    start_new_thread(timer, ())

    print("MESSAGE - Start typing to send messages to the server")

    # connection established loop
    while conn_flag == 1:
        # Send packets
        if seq_num >= len(message_array) and fin_flag == 0:
            message = input("")

            # CONNECTION-ORIENTED PROTOCOL: Close the connection
            if message == "quit":
                # Connection closure
                fin_flag = 1
                connected = False
                conn_flag = 0

                time_oldest_packet = time.time()
                start_new_thread(connection_timer, ())
                send_connection_request()

                server_message, server_address = client_socket.recvfrom(2048)
                (conn_flag, fin_flag, seq_num, receiver_window) \
                    = struct.unpack("!BBII", server_message[:receiver_header_length])
                closed = True
                print("INFO - Connection Close")
                break

            chunked_message = chunk_byte_string(message.encode(), packet_length)
            message_array.extend(chunked_message)
            print("INFO - All messages sent: " + str(message_array))
            print("INFO - baseNum: " + str(base) + " | seqNum: " + str(seq_num))

            time_oldest_packet = time.time()

        send_packets_in_window()

    lock1.release()


def receive_packets():
    global conn_flag, fin_flag, base, time_oldest_packet, window_size, receiver_window
    while conn_flag == 1:
        server_message, server_address = client_socket.recvfrom(2048)
        conn_flag, fin_flag, ack_num, payload, receiver_window = deconstruct_packet(server_message)

        # simulate loss by receiving packet and continuing
        if random.random() < loss_probability:
            print("\nLOSS - Dropped ACK for: " + str(ack_num-1))
            continue

        if ack_num > base:
            base = ack_num
            time_oldest_packet = time.time()

        # CONGESTION CONTROL: AIMD, additively increase window size every RTT
        # FLOW CONTROL: limit window size to receiver window to prevent overwhelming the receiver
        new_window_size = min(window_size+1, receiver_window)
        print("\nCONGESTION CONTROL - Increased Window Size: " + str(window_size) + "->" + str(new_window_size))
        window_size = new_window_size

        print("\nINFO - Received ACK (conn_flag, fin_flag, ack_num, payload): " + str((conn_flag, fin_flag, ack_num, payload)))

    lock2.release()


def main():
    start_new_thread(send_data, ())

    lock1.acquire()
    lock2.acquire()

    while lock1.locked() and lock2.locked():
        continue


if __name__ == "__main__":
    main()

