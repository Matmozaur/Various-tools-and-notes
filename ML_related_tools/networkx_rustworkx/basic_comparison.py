import networkx as nx
import rustworkx as rx
import time
import random


def generate_random_weighted_graph(n_nodes, n_edges, weight_range=(1, 10)):
    G = nx.gnm_random_graph(n_nodes, n_edges, seed=42, directed=False)
    for u, v in G.edges():
        G[u][v]['weight'] = random.randint(*weight_range)
    return G


def nx_dijkstra_all_pairs(G):
    start = time.time()
    lengths = dict(nx.all_pairs_dijkstra_path_length(G, weight='weight'))
    end = time.time()
    print(f"[networkx] Dijkstra all-pairs took: {end - start:.4f} seconds")
    return lengths


def rx_from_networkx(G_nx):
    node_map = {node: i for i, node in enumerate(G_nx.nodes())}
    G_rx = rx.PyGraph()
    G_rx.add_nodes_from([None] * len(node_map))

    for u, v, data in G_nx.edges(data=True):
        weight = data.get('weight', 1.0)
        G_rx.add_edge(node_map[u], node_map[v], weight)

    return G_rx, node_map


def rx_dijkstra_all_pairs(G_rx):
    start = time.time()
    result = {}
    for node in range(len(G_rx.nodes())):
        paths = rx.graph_dijkstra_shortest_path_lengths(
            G_rx, node, edge_cost_fn=lambda edge: edge
        )
        paths_dict = {node: 0}  # add self-distance
        paths_dict.update(paths)
        result[node] = paths_dict
    end = time.time()
    print(f"[rustworkx] Dijkstra all-pairs took: {end - start:.4f} seconds")
    return result


def compare_results(nx_lengths, rx_lengths, node_map):
    discrepancies = 0

    for u_nx in nx_lengths:
        u_rx = node_map[u_nx]
        for v_nx in nx_lengths[u_nx]:
            v_rx = node_map[v_nx]
            nx_dist = nx_lengths[u_nx][v_nx]
            rx_dist = rx_lengths[u_rx][v_rx] if v_rx in rx_lengths[u_rx] else float('inf')
            if nx_dist != rx_dist:
                print(f"Mismatch: {u_nx} -> {v_nx}, networkx={nx_dist}, rustworkx={rx_dist}")
                discrepancies += 1

    print(f"Discrepancies found: {discrepancies}")


if __name__ == "__main__":
    print("Generating random graph...")
    G_nx = generate_random_weighted_graph(n_nodes=500, n_edges=5000)

    print("\nRunning Dijkstra on networkx...")
    nx_lengths = nx_dijkstra_all_pairs(G_nx)

    print("\nConverting to rustworkx...")
    G_rx, node_map = rx_from_networkx(G_nx)

    print("\nRunning Dijkstra on rustworkx...")
    rx_lengths = rx_dijkstra_all_pairs(G_rx)

    print("\nComparing results...")
    compare_results(nx_lengths, rx_lengths, node_map)
