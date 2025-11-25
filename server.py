import socket
import os
import threading
import uuid
from error_handler import HTTPErrorHandler

HOST = "0.0.0.0"
PORT = 8081
BASE_DIR = "files"

clientes_conectados = {}
contador_clientes = 0

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
    """Obtiene la dirección MAC del servidor usando uuid"""
    try:
        # Obtener el nodo de red (MAC address)
        mac_num = uuid.getnode()
        
        # Verificar si es una MAC válida (no es la dirección por defecto)
        if (mac_num >> 40) % 2 == 1:
            return "MAC virtual o no disponible"
        
        # Convertir a formato MAC estándar (XX:XX:XX:XX:XX:XX)
        mac_str = ':'.join(('%012X' % mac_num)[i:i+2] for i in range(0, 12, 2))
        return mac_str
    except Exception as e:
        return f"Error al obtener MAC: {str(e)}"

def analizar_headers_http(request):
    """Analiza y muestra los headers HTTP organizados por categorías"""
    lines = request.splitlines()
    if not lines:
        return
    
    # Línea de request
    print("=== REQUEST LINE ===")
    print(lines[0])
    print()
    
    # Headers organizados
    print("=== HEADERS HTTP ===")
    headers = {}
    for line in lines[1:]:
        if not line.strip():  # Línea vacía fin de headers
            break
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.strip()] = value.strip()
    
    # Mostrar por categorías
    print("Headers de Conexion:")
    for key in ['Host', 'Connection']:
        if key in headers:
            print(f"  {key}: {headers[key]}")
    
    print("\nHeaders de User-Agent:")
    for key in ['User-Agent', 'sec-ch-ua', 'sec-ch-ua-mobile', 'sec-ch-ua-platform']:
        if key in headers:
            print(f"  {key}: {headers[key]}")
    
    print("\nHeaders de Accept:")
    for key in ['Accept', 'Accept-Encoding', 'Accept-Language']:
        if key in headers:
            print(f"  {key}: {headers[key]}")
    
    print("\nHeaders de Seguridad:")
    for key in ['Cache-Control', 'Upgrade-Insecure-Requests', 'Sec-Fetch-Site', 
                'Sec-Fetch-Mode', 'Sec-Fetch-User', 'Sec-Fetch-Dest']:
        if key in headers:
            print(f"  {key}: {headers[key]}")
    
    print("\nHeaders de Cache:")
    for key in ['Cache-Control', 'Pragma']:
        if key in headers:
            print(f"  {key}: {headers[key]}")

def analizar_capas_red(addr, request):
    """Analiza y muestra información de las diferentes capas de red"""
    lines = request.splitlines()
    if not lines:
        return
    
    first_line = lines[0]
    parts = first_line.split()
    if len(parts) >= 3:
        method, uri, http_version = parts[0], parts[1], parts[2]
    else:
        method, uri, http_version = "Unknown", "Unknown", "Unknown"
    
    print("=== ANALISIS POR CAPAS DE RED ===")
    
    print("Capa de Aplicacion (HTTP):")
    print(f"  Metodo: {method}")
    print(f"  URI: {uri}")
    print(f"  Version HTTP: {http_version}")
    
    print("\nCapa de Transporte (TCP):")
    print(f"  Puerto origen (cliente): {addr[1]}")
    print(f"  Puerto destino (servidor): {PORT}")
    print(f"  Protocolo: TCP")
    
    print("\nCapa de Red (IP):")
    print(f"  Direccion IP origen: {addr[0]}")
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"  Direccion IP destino: {local_ip}")
    except:
        print(f"  Direccion IP destino: No disponible")
    print(f"  Protocolo: IPv4")
    
    print("\nCapa de Enlace (Ethernet):")
    mac_servidor = obtener_direccion_mac()
    print(f"  Direccion MAC servidor: {mac_servidor}")
    print(f"  Direccion MAC cliente: No disponible (nivel aplicacion)")
    print(f"  Tipo de trama: Ethernet II")
    print(f"  Nota: Comunicacion local via loopback - MACs fisicas no utilizadas")

def manejar_cliente(conn, addr, client_id):
    client_name = f"Cliente-{client_id}"
    clientes_conectados[client_id] = {
        'name': client_name,
        'addr': addr,
        'connected': True
    }
    
    print(f"\n[{client_name}] CONEXION ACEPTADA")
    print(f"[{client_name}] Direccion remota: {addr[0]}:{addr[1]}")

    try:
        request = conn.recv(1024).decode(errors="ignore")
        if not request:
            print(f"[{client_name}] Request vacio")
            conn.close()
            return

        print(f"\n[{client_name}] === ANALISIS COMPLETO DEL REQUEST ===")
        
        # Análisis por capas de red
        analizar_capas_red(addr, request)
        
        # Análisis detallado de headers HTTP
        analizar_headers_http(request)
        
        print(f"\n[{client_name}] === CONTENIDO COMPLETO DEL REQUEST ===")
        print("=" * 60)
        print(request)
        print("=" * 60)

        # Procesamiento del request
        lines = request.splitlines()
        if not lines:
            error_msg = HTTPErrorHandler.bad_request(conn)
            print(f"[{client_name}] {error_msg}")
            return

        first_line = lines[0]
        parts = first_line.split()
        if len(parts) < 3:
            error_msg = HTTPErrorHandler.bad_request(conn)
            print(f"[{client_name}] {error_msg}")
            return

        method, uri, version = parts[0], parts[1], parts[2]
        print(f"[{client_name}] Resumen: Metodo={method}, URI={uri}, Version={version}")

        # Validaciones
        if method != "GET":
            error_msg = HTTPErrorHandler.method_not_implemented(conn, method)
            print(f"[{client_name}] {error_msg}")
            return

        if version not in ["HTTP/1.0", "HTTP/1.1"]:
            error_msg = HTTPErrorHandler.http_version_not_supported(conn, version)
            print(f"[{client_name}] {error_msg}")
            return

        # Resolver archivo
        if uri == "/":
            filename = "index.html"
        else:
            filename = uri.lstrip("/")

        filepath = os.path.join(BASE_DIR, filename)
        print(f"[{client_name}] Buscando archivo: {filename}")

        if not os.path.exists(filepath):
            error_msg = HTTPErrorHandler.not_found(conn, filename)
            print(f"[{client_name}] {error_msg}")
            return

        # Servir archivo
        content_type = get_content_type(filename)
        with open(filepath, "rb") as f:
            body_bytes = f.read()

        success_msg = HTTPErrorHandler.success_response(conn, content_type, body_bytes)
        print(f"[{client_name}] {success_msg}")
        print(f"[{client_name}] Archivo servido: {filename}")
        print(f"[{client_name}] Tamaño: {len(body_bytes)} bytes")
        print(f"[{client_name}] Content-Type: {content_type}")

    except Exception as e:
        error_msg = HTTPErrorHandler.internal_server_error(conn, str(e))
        print(f"[{client_name}] {error_msg}")
    finally:
        conn.close()
        clientes_conectados[client_id]['connected'] = False
        print(f"[{client_name}] CONEXION CERRADA")
        print(f"[ESTADISTICAS] Clientes activos: {len([c for c in clientes_conectados.values() if c['connected']])}")

def main():
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

    print("=" * 60)
    print("SERVIDOR HTTP MULTIHILO - ANALISIS DE CAPAS DE RED")
    print(f"Escuchando en: {HOST}:{PORT}")
    print(f"Directorio base: {BASE_DIR}")
    print(f"MAC del servidor: {obtener_direccion_mac()}")
    print("=" * 60)

    global contador_clientes

    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
        print(f"Directorio '{BASE_DIR}' creado")

    while True:
        print("\nEsperando conexiones...")
        conn, addr = server.accept()
        contador_clientes += 1
        client_id = contador_clientes

        thread = threading.Thread(target=manejar_cliente, args=(conn, addr, client_id))
        thread.daemon = True
        thread.start()
        print(f"[THREAD] Hilo {client_id} iniciado")

if __name__ == "__main__":
    main()
