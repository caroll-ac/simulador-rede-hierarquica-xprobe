import networkx as nx
import matplotlib.pyplot as plt
import time
import random

# --- Funções Auxiliares (Não Modificadas) ---

# Função para gerar IPs aleatórios em uma sub-rede
def generate_ips(subnet, num_hosts, prefix):
    base_ip_parts = subnet.split('/')[0].split('.')
    return {f"H{prefix}{i+1}": f"{base_ip_parts[0]}.{base_ip_parts[1]}.{base_ip_parts[2]}.{int(base_ip_parts[3]) + i + 1}" for i in range(num_hosts)}

# --- Definição da Topologia e Endereçamento (Pode variar a cada execução) ---

graph = nx.Graph()

# Definição dos elementos da rede
switches_borda = ["e1", "e2", "e3", "e4"]
switches_agg = ["a1", "a2"]
switch_root = "root"

# Gerando número aleatório de hosts para cada sub-rede (1 a 3 hosts)
num_hosts_e1 = random.randint(1, 3)
num_hosts_e2 = random.randint(1, 3)
num_hosts_e3 = random.randint(1, 3)
num_hosts_e4 = random.randint(1, 3)

# Gerando IPs para cada sub-rede
# OBSERVAÇÃO: Os IPs dos hosts começam em X.X.X.1 na função generate_ips.
ips_e1 = generate_ips("192.168.1.0/27", num_hosts_e1, "1")  # e.g., 192.168.1.1, 192.168.1.2...
ips_e2 = generate_ips("192.168.1.32/27", num_hosts_e2, "2") # e.g., 192.168.1.33, 192.168.1.34...
ips_e3 = generate_ips("192.168.1.64/28", num_hosts_e3, "3") # e.g., 192.168.1.65, 192.168.1.66...
ips_e4 = generate_ips("192.168.1.80/28", num_hosts_e4, "4") # e.g., 192.168.1.81, 192.168.1.82...

hosts = list(ips_e1.keys()) + list(ips_e2.keys()) + list(ips_e3.keys()) + list(ips_e4.keys())

graph.add_nodes_from(hosts + switches_borda + switches_agg + [switch_root])

# Conectando os switches na topologia de árvore
graph.add_edges_from([
    ("root", "a1"), ("root", "a2"),
    ("a1", "e1"), ("a1", "e2"),
    ("a2", "e3"), ("a2", "e4"),
])

for host in ips_e1.keys():
    graph.add_edge("e1", host)
for host in ips_e2.keys():
    graph.add_edge("e2", host)
for host in ips_e3.keys():
    graph.add_edge("e3", host)
for host in ips_e4.keys():
    graph.add_edge("e4", host)

# Endereçamento IP de cada nó (Ajuste para garantir que switches não usem IPs de hosts)
ip_addresses = {
    **ips_e1, **ips_e2, **ips_e3, **ips_e4,
    "e1": "192.168.1.30", "e2": "192.168.1.62", # IPs finais das sub-redes
    "e3": "192.168.1.78", "e4": "192.168.1.94",
    "a1": "192.168.1.97", "a2": "192.168.1.109",
    "root": "192.168.1.254"
}

# Tabela de roteamento para cada switch (Apenas para roteadores/Aggregation/Core)
routing_table = {
    "a1": {"192.168.1.0/27": "e1", "192.168.1.32/27": "e2"},
    "a2": {"192.168.1.64/28": "e3", "192.168.1.80/28": "e4"},
    "root": {
        "192.168.1.0/27": "a1", "192.168.1.32/27": "a1",
        "192.168.1.64/28": "a2", "192.168.1.80/28": "a2"
    }
}

def plot_graph(G):
    layers = {}
    layers["root"] = 0
    layers["a1"] = 1
    layers["a2"] = 1
    layers["e1"] = 2
    layers["e2"] = 2
    layers["e3"] = 2
    layers["e4"] = 2
    for host in hosts:
        layers[host] = 3

    for node, layer in layers.items():
        G.nodes[node]["layer"] = layer

    pos = nx.multipartite_layout(G, subset_key="layer", align="vertical")

    nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=2000, font_size=10, font_weight='bold')
    plt.title("Topologia de Rede em Árvore")
    plt.show()

# As tabelas dos switches de borda (e1-e4) são implícitas, contendo apenas as rotas diretas para os hosts

# --- Novas Funções para o Projeto ---

def display_routing_tables(tables):
    """Exibe as tabelas de roteamento dos nós Core e Aggregation."""
    print("\n--- Tabelas de Roteamento (Core e Aggregation) ---")
    for router, table in tables.items():
        if router in ["root", "a1", "a2"]:
            print(f"\n### Tabela de Roteamento de {router} ({ip_addresses[router]})")
            print("---------------------------------")
            print("| Rede de Destino | Próximo Salto |")
            print("|-----------------|---------------|")
            for network, next_hop in table.items():
                print(f"| {network:<15} | {next_hop:<13} |")
            print("---------------------------------")
    print("----------------------------------------------------\n")

def get_path_latency(G, src, dst):
    """Calcula a latência (RTT) simulada do caminho."""
    try:
        path = nx.shortest_path(G, source=src, target=dst)
        # O RTT é proporcional ao número de saltos no caminho de ida e volta
        # Latência de um link = 0.05 segundos. RTT = 2 * (n_saltos * latência)
        # Randomiza um pouco para simular a variação do RTT
        num_hops = len(path) - 1 
        base_rtt = 2 * num_hops * 0.05  
        rtt_sample = base_rtt * (1 + random.uniform(-0.1, 0.1)) # Variação de +-10%
        return rtt_sample
    except nx.NetworkXNoPath:
        return float('inf')

def xprobe_rtt(G, src, dst, num_samples=3):
    """Simula o XProbe (Medição de RTT) com N amostras."""
    if src not in G.nodes or dst not in G.nodes:
        print(f" Erro: Host {src} ou {dst} não existe na rede!")
        return
    
    if not nx.has_path(G, src, dst):
        print(f" Host {dst} inalcançável a partir de {src}!")
        return

    rtt_times = []
    
    print(f"\n---  Simulação XProbe/RTT ---")
    print(f" Origem: {src} ({ip_addresses[src]})")
    print(f" Destino: {dst} ({ip_addresses[dst]})")
    
    path = nx.shortest_path(G, source=src, target=dst)
    print(f" Rota (Saltos): {path}")

    for i in range(num_samples):
        # Simula o tempo de latência de ida e volta
        rtt = get_path_latency(G, src, dst)
        rtt_times.append(rtt)
        print(f" Amostra {i+1}: RTT = {rtt:.4f} ms")
        time.sleep(0.5) # Simula um pequeno intervalo entre as amostras

    # Cálculo do RTT Médio
    if rtt_times:
        rtt_mean = sum(rtt_times) / len(rtt_times)
        print("\n--- ✅ Estatísticas do XProbe (RTT) ---")
        print(f" RTT Mínimo: {min(rtt_times):.4f} ms")
        print(f" RTT Máximo: {max(rtt_times):.4f} ms")
        print(f" **RTT MÉDIO (3 Amostras): {rtt_mean:.4f} ms**")
    
# --- Funções do Menu (Modificadas) ---

def menu():
    print("\n=== Simulador de Rede ===")
    print("1. Visualizar Topologia")
    print("2. Exibir Tabelas de Roteamento (Quadro 1)")
    print("3. Simulação XProbe/RTT (Quadro 1)")
    print("4. Sair")
    choice = input("Escolha uma opção: ")
    return choice

# --- Execução do Programa (Modificada) ---
if __name__ == "__main__":
    
    print(f"Hosts Gerados: {hosts}")

    while True:
        choice = menu()
        if choice == "1":
            plot_graph(graph)
        elif choice == "2":
            display_routing_tables(routing_table)
        elif choice == "3":
            print("\nHosts disponíveis:", hosts)
            src = input("Digite o host de origem (ex: H11): ")
            dst = input("Digite o host de destino (ex: H21): ")
            xprobe_rtt(graph, src, dst)
        elif choice == "4":
            print("Saindo...")
            break
        else:
            print("Opção inválida. Tente novamente.")