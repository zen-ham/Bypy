import socket
import stun


def get_external_ip():
    nat_type, external_ip, external_port = stun.
    print(f"External IP: {external_ip}, External Port: {external_port}")
    return external_ip, external_port


def run_server():
    external_ip, external_port = get_external_ip()

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind to the external IP and port
    sock.bind(('', external_port))
    print(f"Server listening on {external_ip}:{external_port}")

    # Wait for a client to connect
    while True:
        data, addr = sock.recvfrom(1024)
        print(f"Received message from {addr}: {data.decode()}")
        sock.sendto(b"Hello from the server!", addr)


if __name__ == "__main__":
    run_server()
