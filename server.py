import socket
import os
import threading
import uuid
import time
import json
from error_handler import HTTPErrorHandler
from clients_handler import ClientsHandler

HOST = "0.0.0.0"
PORT = 8081
BASE_DIR = "files"

# Handler global para todos los clientes
clients_handler = ClientsHandler()

def get_content_type(filename):
    if filename.endswith(".html"):
        return "text/html; charset=utf-8"
    elif filename.endswith(".txt"):
        return "text/plain; charset=utf-8"
    elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
        return "image/jpeg"
    elif filename.endswith(".png"):
        return "image/png"
    else:
        return "application/octet-stream"

def obtener_direccion_mac():
    try:
        mac_num = uuid.getnode()
        if (mac_num >> 40) % 2 == 1:
            return "MAC virtual o no disponible"
        mac_str = ':'.join(('%012X' % mac_num)[i:i+2] for i in range(0, 12, 2))
        return mac_str
    except Exception as e:
        return f"Error al obtener MAC: {str(e)}"

def manejar_request_admin(conn, request, client_name):
    """Maneja los requests de administración"""
    lines = request.splitlines()
    if not lines:
        return
    
    first_line = lines[0]
    parts = first_line.split()
    if len(parts) < 2:
        return
    
    method, path = parts[0], parts[1]
    
    print(f"[ADMIN] {method} {path} from {client_name}")
    
    if method == 'GET' and path == '/admin-stats':
        # Devolver estadísticas en JSON
        stats = clients_handler.get_stats()
        response_json = json.dumps(stats, ensure_ascii=False)
        
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            f"Content-Length: {len(response_json)}\r\n"
            "Connection: keep-alive\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "\r\n"
            f"{response_json}"
        )
        conn.sendall(response.encode())
        
    elif method == 'POST' and path == '/admin-disconnect-all':
        # Desconectar todos los clientes
        disconnected_count = clients_handler.disconnect_all_clients()
        response_data = json.dumps({
            "message": f"Desconectados {disconnected_count} clientes",
            "disconnected_count": disconnected_count
        })
        
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            f"Content-Length: {len(response_data)}\r\n"
            "Connection: keep-alive\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "\r\n"
            f"{response_data}"
        )
        conn.sendall(response.encode())
        
    elif method == 'POST' and path.startswith('/admin-disconnect-client/'):
        # Desconectar cliente específico
        try:
            client_id = int(path.split('/')[-1])
            success = clients_handler.disconnect_client(client_id)
            
            if success:
                response_data = json.dumps({"message": f"Cliente {client_id} desconectado"})
            else:
                response_data = json.dumps({"message": f"Error desconectando cliente {client_id}"})
                
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(response_data)}\r\n"
                "Connection: keep-alive\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                "\r\n"
                f"{response_data}"
            )
            conn.sendall(response.encode())
        except:
            HTTPErrorHandler.bad_request(conn)
            
    elif method == 'POST' and path == '/admin-broadcast':
        # Broadcast message a todos los clientes
        try:
            # Extraer el cuerpo del request
            body = request.split('\r\n\r\n')[1] if '\r\n\r\n' in request else '{}'
            data = json.loads(body)
            message = data.get('message', 'Mensaje de broadcast')
            
            sent_count = clients_handler.broadcast_message(message)
            response_data = json.dumps({
                "message": f"Mensaje enviado a {sent_count} clientes",
                "sent_count": sent_count
            })
            
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(response_data)}\r\n"
                "Connection: keep-alive\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                "\r\n"
                f"{response_data}"
            )
            conn.sendall(response.encode())
        except:
            HTTPErrorHandler.bad_request(conn)
            
    elif method == 'GET' and path.startswith('/admin-client-details/'):
        # Detalles de cliente específico
        try:
            client_id = int(path.split('/')[-1])
            client_info = clients_handler.get_client_info(client_id)
            
            if client_info:
                response_data = json.dumps({
                    "client_id": client_id,
                    "name": client_info['name'],
                    "address": f"{client_info['addr'][0]}:{client_info['addr'][1]}",
                    "connected": client_info['connected'],
                    "request_count": client_info['request_count'],
                    "last_activity": time.strftime('%H:%M:%S', time.localtime(client_info['last_activity']))
                })
            else:
                response_data = json.dumps({"error": "Cliente no encontrado"})
                
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(response_data)}\r\n"
                "Connection: keep-alive\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                "\r\n"
                f"{response_data}"
            )
            conn.sendall(response.encode())
        except:
            HTTPErrorHandler.bad_request(conn)
            
    elif method == 'GET' and path == '/admin':
        # Servir la página de administración
        admin_file_path = os.path.join(BASE_DIR, 'admin.html')
        if os.path.exists(admin_file_path):
            with open(admin_file_path, 'rb') as f:
                content = f.read()
            
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(content)}\r\n"
                "Connection: close\r\n"
                "\r\n"
            )
            conn.sendall(response.encode() + content)
        else:
            HTTPErrorHandler.not_found(conn, 'admin.html')
    
    else:
        HTTPErrorHandler.not_found(conn, path)

def procesar_request(conn, client_name, client_id, request):
    lines = request.splitlines()
    if not lines:
        return True  # Mantener conexión

    first_line = lines[0]
    parts = first_line.split()
    if len(parts) < 3:
        HTTPErrorHandler.bad_request(conn)
        return True  # Mantener conexión

    method, uri, version = parts[0], parts[1], parts[2]
    
    # Actualizar actividad del cliente
    clients_handler.update_client_activity(client_id)
    
    connection_keep_alive = True  # Siempre mantener conexión
    
    print(f"[{client_name}] Conexion persistente: {connection_keep_alive}")

    if method != "GET":
        HTTPErrorHandler.method_not_implemented(conn, method)
        return True  # Mantener conexión

    if version not in ["HTTP/1.0", "HTTP/1.1"]:
        HTTPErrorHandler.http_version_not_supported(conn, version)
        return True  # Mantener conexión

    if uri == "/":
        filename = "index.html"
    else:
        filename = uri.lstrip("/")

    filepath = os.path.join(BASE_DIR, filename)
    print(f"[{client_name}] Buscando archivo: {filename}")

    if not os.path.exists(filepath):
        HTTPErrorHandler.not_found(conn, filename)
        return True  # Mantener conexión

    content_type = get_content_type(filename)
    with open(filepath, "rb") as f:
        body_bytes = f.read()

    # Siempre enviar Connection: keep-alive
    header = (
        "HTTP/1.1 200 OK\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body_bytes)}\r\n"
        "Connection: keep-alive\r\n"
        "\r\n"
    )
    
    conn.sendall(header.encode() + body_bytes)
    print(f"[{client_name}] 200 OK - Archivo: {filename} ({len(body_bytes)} bytes)")
    
    return True  # Siempre mantener conexión

def manejar_cliente(conn, addr, client_id, client_name):
    """Maneja un cliente de forma persistente indefinida"""
    
    print(f"\n[{client_name}] CONEXION ACEPTADA")
    print(f"[{client_name}] Direccion remota: {addr[0]}:{addr[1]}")
    
    try:
        while True:
            conn.settimeout(30.0)
            
            try:
                data = conn.recv(8192)  # Aumentar buffer para requests más grandes
                if not data:
                    print(f"[{client_name}] Cliente cerro la conexion")
                    break
                    
                request = data.decode(errors="ignore")
                
                # Verificar si es un request de administración
                if request.startswith('GET /admin-') or request.startswith('POST /admin-') or request.startswith('GET /admin'):
                    print(f"[{client_name}] Request de administracion recibido")
                    manejar_request_admin(conn, request, client_name)
                else:
                    print(f"\n[{client_name}] NUEVO REQUEST RECIBIDO")
                    print("=" * 40)
                    print(request.split('\n')[0])
                    print("=" * 40)

                    procesar_request(conn, client_name, client_id, request)
                    clients_handler.print_stats()
                
            except socket.timeout:
                print(f"[{client_name}] Timeout de lectura - Conexion mantenida")
                continue
            except Exception as e:
                print(f"[{client_name}] Error leyendo request: {e}")
                break
                
    except Exception as e:
        print(f"[{client_name}] Error en manejo de cliente: {e}")
    finally:
        clients_handler.disconnect_client(client_id)
        print(f"[{client_name}] CONEXION CERRADA")
        clients_handler.print_stats()

def iniciar_servidor():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)

    print("=" * 60)
    print("SERVIDOR HTTP - CONEXIONES PERSISTENTES INDEFINIDAS")
    print(f"Escuchando en: {HOST}:{PORT}")
    print(f"Directorio base: {BASE_DIR}")
    print(f"MAC del servidor: {obtener_direccion_mac()}")
    print("=" * 60)

    # Comando thread para manejar desconexiones
    def comando_handler():
        while True:
            try:
                cmd = input("\nComando (q=quit, stats=estadisticas, disconnect=desconectar todos): ").strip().lower()
                if cmd == 'q':
                    print("Cerrando servidor...")
                    clients_handler.disconnect_all_clients()
                    os._exit(0)
                elif cmd == 'stats':
                    clients_handler.print_stats()
                elif cmd == 'disconnect':
                    disconnected = clients_handler.disconnect_all_clients()
                    print(f"Desconectados {disconnected} clientes")
                elif cmd == 'broadcast':
                    msg = input("Mensaje para broadcast: ")
                    sent = clients_handler.broadcast_message(msg)
                    print(f"Mensaje enviado a {sent} clientes")
            except:
                break

    # Iniciar thread de comandos
    comando_thread = threading.Thread(target=comando_handler, daemon=True)
    comando_thread.start()

    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
        print(f"Directorio '{BASE_DIR}' creado")

    while True:
        print("\nEsperando conexiones...")
        conn, addr = server.accept()
        
        # Agregar cliente al handler
        client_id, client_name = clients_handler.add_client(conn, addr)

        # Iniciar thread para el cliente
        thread = threading.Thread(target=manejar_cliente, args=(conn, addr, client_id, client_name))
        thread.daemon = True
        thread.start()
        print(f"[THREAD] Hilo para {client_name} iniciado")

if __name__ == "__main__":
    iniciar_servidor()