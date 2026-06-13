import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from data.graph import graph
from data.servers import servers
from services.dijkstra import dijkstra, reconstruct_path

app = Flask(__name__)
CORS(app, origins="*")

API_HOST = os.environ.get("API_HOST", "http://localhost:5000")


@app.route("/find-server", methods=["POST"])
def find_server():
    data = request.get_json(force=True)

    user_location = data.get("location", "").strip()
    video = data.get("video", "video_1")

    if not user_location:
        return jsonify({"error": "Location is required"}), 400

    # Case-insensitive match
    location_key = next(
        (k for k in graph if k.lower() == user_location.lower()), None
    )
    if location_key is None:
        return jsonify({"error": f"Unknown location: {user_location}"}), 400

    # Run Dijkstra (returns distances + prev for path reconstruction)
    distances, prev = dijkstra(graph, location_key)

    # Filter to server nodes only
    server_distances = {s: distances.get(s, float("inf")) for s in servers}
    nearest_server = min(server_distances, key=server_distances.get)
    min_distance = server_distances[nearest_server]

    # Reconstruct the exact shortest path
    path = reconstruct_path(prev, nearest_server)

    # All servers ranked by distance (useful for the UI to show alternatives)
    ranked_servers = sorted(
        [{"server": s, "distance": server_distances[s]} for s in servers],
        key=lambda x: x["distance"],
    )

    video_url = f"{API_HOST}/static/videos/{video}.mp4"

    return jsonify({
        "user_location": location_key,
        "selected_server": nearest_server,
        "distance": min_distance,
        "path": path,                  # ← exact node sequence from user → server
        "ranked_servers": ranked_servers,
        "video_url": video_url,
    })


@app.route("/videos", methods=["GET"])
def list_videos():
    static_dir = os.path.join(os.path.dirname(__file__), "static", "videos")
    videos = []
    if os.path.exists(static_dir):
        for f in os.listdir(static_dir):
            if f.endswith(".mp4"):
                name = f.replace(".mp4", "")
                videos.append({
                    "id": name,
                    "title": name.replace("_", " ").title(),
                    "url": f"{API_HOST}/static/videos/{f}",
                })
    return jsonify(videos)


@app.route("/graph", methods=["GET"])
def get_graph():
    """Expose the graph topology so the frontend can use the exact same data."""
    return jsonify({
        "nodes": list(graph.keys()),
        "servers": servers,
        "edges": [
            {"from": a, "to": b, "weight": w}
            for a, neighbors in graph.items()
            for b, w in neighbors.items()
        ],
    })


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "CDN Backend running", "version": "3.0",
                    "endpoints": ["/find-server", "/videos", "/graph"]})


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=debug, port=port)
