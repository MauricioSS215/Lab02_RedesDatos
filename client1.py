import socket
import sys
import time

def main():
    if len(sys.argv) != 4:
        print("Uso: python client1.py <server_host> <server_port> <filename>")
        sys.exit(1)

    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    filename = sys.argv[3]

    print(f"CLIENTE 1 - Conectando a {server_host}:{server_port}")
    print(f"Solicitando archivo: {filename}")
    
    # Crear socket TCP
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Conectar al servidor
        print("Estableciendo conexion...")
        client.connect((server_host, server_port))
        print("Conexion establecida")

        # Pequeña pausa para diferenciar clientes
        time.sleep(0.5)

        # Armar el request HTTP
        request_line = f"GET /{filename} HTTP/1.1\r\n"
        headers = (
            f"Host: {server_host}\r\n"
            "User-Agent: Cliente-1/1.0\r\n"
            "Connection: close\r\n"
            "\r\n"
        )
        http_request = request_line + headers

        print("ENVIANDO REQUEST:")
        print("=" * 40)
        print(http_request)
        print("=" * 40)

        # Enviar request
        client.sendall(http_request.encode())

        print("Esperando respuesta del servidor...")

        # Leer respuesta
        response_chunks = []
        while True:
            data = client.recv(4096)
            if not data:
                break
            response_chunks.append(data)

        # Unir todo
        response = b"".join(response_chunks)

        print("RESPUESTA RECIBIDA:")
        print("=" * 50)
        try:
            # Mostrar headers y parte del body si es texto
            response_text = response.decode(errors="ignore")
            lines = response_text.split('\n')
            # Mostrar solo primeras 20 líneas para no saturar
            for i, line in enumerate(lines[:20]):
                print(line)
            if len(lines) > 20:
                print("... (respuesta truncada)")
        except UnicodeDecodeError:
            print("[Contenido binario - mostrando primeros 200 bytes]")
            print(response[:200])
            print("...")
        print("=" * 50)

    except Exception as e:
        print(f"Error en el cliente 1: {e}")
    finally:
        client.close()
        print("Conexion cerrada - Cliente 1 finalizado")


if __name__ == "__main__":
    main()