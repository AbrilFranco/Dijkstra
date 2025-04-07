from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import heapq
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64
import os

app = Flask(__name__)
CORS(app)

# ---------------- Dijkstra ----------------
def dijkstra(graph, start):
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    previous_nodes = {node: None for node in graph}
    queue = [(0, start)]

    while queue:
        current_distance, current_node = heapq.heappop(queue)

        if current_distance > distances[current_node]:
            continue

        for neighbor, weight in graph[current_node].items():
            distance = current_distance + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous_nodes[neighbor] = current_node
                heapq.heappush(queue, (distance, neighbor))

    return distances, previous_nodes

def shortest_path(previous_nodes, end):
    path = []
    while end is not None:
        path.append(end)
        end = previous_nodes[end]
    return path[::-1]

# ---------------- Función para generar el diagrama ----------------
def generar_diagrama(grafo, ruta):
    G = nx.Graph()

    # Añadir nodos y aristas al grafo de NetworkX
    for nodo in grafo:
        for vecino, peso in grafo[nodo].items():
            G.add_edge(nodo, vecino, weight=peso)

    # Configurar los nodos
    pos = nx.spring_layout(G)  # Posición de los nodos

    # Dibuja el grafo
    plt.figure(figsize=(8, 6))
    nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=2000, font_size=12)
    
    # Dibuja la ruta más corta con un color diferente
    if ruta:
        edges = [(ruta[i], ruta[i + 1]) for i in range(len(ruta) - 1)]
        nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color="red", width=2)

    # Mostrar las distancias de los arcos
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    # Guardar la imagen como un archivo base64
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format="png")
    img_bytes.seek(0)
    img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
    plt.close()

    return img_base64

# ---------------- Rutas Flask ----------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/resolver_dijkstra', methods=['POST'])
def resolver_dijkstra():
    try:
        data = request.get_json()  # Obtener los datos enviados como JSON
        nodos = data.get("nodos", [])
        conexiones = data.get("conexiones", [])
        inicio = data.get("inicio")
        fin = data.get("fin")

        # Verifica que los datos sean válidos
        if not nodos or not conexiones or not inicio or not fin:
            return jsonify({"error": "Datos incompletos"}), 400

        # Construir grafo
        grafo = {nodo: {} for nodo in nodos}
        for conexion in conexiones:
            origen = conexion["origen"]
            destino = conexion["destino"]
            peso = float(conexion["peso"])
            grafo[origen][destino] = peso
            grafo[destino][origen] = peso  # Si es no dirigido

        # Calcular distancias y ruta más corta
        distancias, anteriores = dijkstra(grafo, inicio)
        ruta = shortest_path(anteriores, fin)

        # Reemplazar float('inf') por None (null en JSON)
        distancias = {k: (v if v != float('inf') else None) for k, v in distancias.items()}

        # Generar diagrama
        imagen_base64 = generar_diagrama(grafo, ruta)

        return jsonify({
            "distancias": distancias,
            "ruta": ruta,
            "distancia_total": distancias.get(fin),  # Si es None, será null en JSON
            "imagen": imagen_base64
        })

    except Exception as e:
        # En caso de error, devolver un mensaje claro
        return jsonify({"error": str(e)}), 500

# ---------------- Main ----------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT',5000)) 
    app.run(host='0.0.0.0',port=port)










