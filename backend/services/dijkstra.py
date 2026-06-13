import heapq


def dijkstra(graph, start):
    """Run Dijkstra from `start`. Returns (distances, prev) for path reconstruction."""
    distances = {node: float("inf") for node in graph}
    prev = {node: None for node in graph}
    distances[start] = 0

    pq = [(0, start)]

    while pq:
        current_distance, current_node = heapq.heappop(pq)

        if current_distance > distances[current_node]:
            continue

        for neighbor, weight in graph.get(current_node, {}).items():
            distance = current_distance + weight

            if distance < distances.get(neighbor, float("inf")):
                distances[neighbor] = distance
                prev[neighbor] = current_node
                heapq.heappush(pq, (distance, neighbor))

    return distances, prev


def reconstruct_path(prev, target):
    """Walk back through prev pointers to reconstruct the shortest path."""
    path = []
    cur = target
    while cur is not None:
        path.append(cur)
        cur = prev.get(cur)
    path.reverse()
    return path
