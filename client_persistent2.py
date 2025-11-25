import socket
import sys
import time

def main():
    if len(sys.argv) != 4:
        print("Uso: python client_persistent2.py <server_host> <server_port> <filename>")
        sys.exit(1)

    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    filename = sys.argv[3]

    print(f"CLIENTE PERSISTENTE 2 - Conectando a {server_host}:{server_port}")
    print("COMPORTAMIENTO: Conexion indefinida - Envia requests cada 8s")
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        print("Estableciendo conexion...")
        client.connect((server_host, server_port))
        print("Conexion establecida - Modo PERSISTENTE INDEFINIDO")

        request_count = 0
        
        while True:
            request_count += 1
            print(f"\n--- CLIENTE 2 - Request #{request_count} ---")
            
            # Rotar entre archivos
            files_rotation = [filename, "prueba.txt", "index.html"]
            current_file = files_rotation[request_count % len(files_rotation)]
            
            request_line = f"GET /{current_file} HTTP/1.1\r\n"
            headers = (
                f"Host: {server_host}\r\n"
                "User-Agent: Cliente-Persistente-2/1.0\r\n"
                "Connection: keep-alive\r\n"
                "\r\n"
            )
            http_request = request_line + headers

            print(f"Enviando request para: {current_file}")
            client.sendall(http_request.encode())

            # Leer respuesta
            response = b""
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                response += chunk
                if b"\r\n\r\n" in response:
                    headers_end = response.find(b"\r\n\r\n") + 4
                    headers_part = response[:headers_end]
                    if b"Content-Length:" in headers_part:
                        content_length_pos = headers_part.find(b"Content-Length:") + 15
                        content_length_end = headers_part.find(b"\r\n", content_length_pos)
                        content_length = int(headers_part[content_length_pos:content_length_end].strip())
                        total_expected = headers_end + content_length
                        if len(response) >= total_expected:
                            break
                    else:
                        if chunk.endswith(b"\r\n") or len(chunk) < 4096:
                            break

            status_code = response.split(b' ')[1].decode()
            print(f"Respuesta #{request_count} recibida - Status: {status_code}")

            print(f"CLIENTE 2: Esperando 8 segundos para siguiente request...")
            time.sleep(8)

    except KeyboardInterrupt:
        print("\nCLIENTE 2: Interrumpido por usuario")
    except Exception as e:
        print(f"Error en el cliente persistente 2: {e}")
    finally:
        client.close()
        print("CLIENTE 2: Conexion cerrada")

if __name__ == "__main__":
    main()