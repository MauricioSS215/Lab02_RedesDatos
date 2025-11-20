import socket
import sys

def main():
    if len(sys.argv) != 4:
        print("Uso: python client.py <server_host> <server_port> <filename>")
        sys.exit(1)

    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    filename = sys.argv[3]

    # Crear socket TCP
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Conectar al servidor
        client.connect((server_host, server_port))

        # Armar el request HTTP (siempre GET, como dice el enunciado)
        request_line = f"GET /{filename} HTTP/1.1\r\n"
        headers = (
            f"Host: {server_host}\r\n"
            "Connection: close\r\n"
            "\r\n"
        )
        http_request = request_line + headers

        print("===== REQUEST ENVIADO =====")
        print(http_request)
        print("===========================\n")

        # Enviar request
        client.sendall(http_request.encode())

        print("===== RESPUESTA DEL SERVIDOR =====\n")

        # Leer hasta que el servidor cierre la conexión
        response_chunks = []
        while True:
            data = client.recv(4096)
            if not data:
                break
            response_chunks.append(data)

        # Unir todo
        response = b"".join(response_chunks)

        # Mostrar tal cual (puede incluir binario si es imagen)
        try:
            print(response.decode(errors="ignore"))
        except UnicodeDecodeError:
            # Por las dudas, si hay binario raro
            print(response)

    except Exception as e:
        print("Error en el cliente:", e)
    finally:
        client.close()


if __name__ == "__main__":
    main()
