import socket, stun, zhmiscellany


zhmiscellany.misc.die_on_key()


def get_external_ip():
    # Use a specific STUN server
    stun_server = ('stun.l.google.com', 19302)
    nat_type, external_ip, external_port = stun.get_ip_info(stun_host=stun_server[0], stun_port=stun_server[1])

    if external_ip is None or external_port is None:
        print("Failed to get external IP and port.")
    else:
        print(f"External IP: {external_ip}, External Port: {external_port}")

    return external_ip, external_port


def run_client(server_ip, server_port):
    external_ip, external_port = get_external_ip()

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Send a message to the server
    message = b"Hello from the client!"
    sock.sendto(message, (server_ip, server_port))
    print(f"Sent message to {server_ip}:{server_port}")

    # Receive the server's response
    data, addr = sock.recvfrom(1024)
    print(f"Received response from server: {data.decode()}")


if __name__ == "__main__":
    # Replace with the external IP and port of the server
    SERVER_IP = "1.145.97.238"
    SERVER_PORT = 4208
    run_client(SERVER_IP, SERVER_PORT)
