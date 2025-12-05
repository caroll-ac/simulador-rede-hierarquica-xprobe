import networkx as nx
import matplotlib.pyplot as plt
import time
import random

# Função para gerar IPs aleatórios em uma sub-rede
def generate_ips(subnet, num_hosts, prefix):
    base_ip = subnet.split('/')[0]
    return {f"H{prefix}{i+1}": f"{base_ip[:-1]}{i+2}" for i in range(num_hosts)}

# Função para criar o grafo
graph = nx.Graph()

# Definição dos elementos da rede
switches_borda = ["e1", "e2", "e3", "e4"]
switches_agg = ["a1", "a2"]
switch_root = "root"

# Gerando número aleatório de hosts para cada sub-rede (1 a 20 hosts)
num_hosts_e1 = random.randint(1, 10)
num_hosts_e2 = random.randint(1, 10)
num_hosts_e3 = random.randint(1, 20)
num_hosts_e4 = random.randint(1, 20)

# Gerando IPs para cada sub-rede
ips_e1 = generate_ips("192.168.1.0/27", num_hosts_e1, "1")  
ips_e2 = generate_ips("192.168.1.32/27", num_hosts_e2, "2")  
ips_e3 = generate_ips("192.168.1.64/28", num_hosts_e3, "3")  
ips_e4 = generate_ips("192.168.1.80/28", num_hosts_e4, "4") 

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

# Endereçamento IP de cada nó
ip_addresses = {
    **ips_e1, **ips_e2, **ips_e3, **ips_e4,
    "e1": "192.168.1.1", "e2": "192.168.1.33",
    "e3": "192.168.1.65", "e4": "192.168.1.81",
    "a1": "192.168.1.97", "a2": "192.168.1.109",
    "root": "192.168.1.254"
}

# Tabela de roteamento para cada switch
routing_table = {
    "a1": {"192.168.1.0/27": "e1", "192.168.1.32/27": "e2"},
    "a2": {"192.168.1.64/28": "e3", "192.168.1.80/28": "e4"},
    "root": {
        "192.168.1.0/27": "a1", "192.168.1.32/27": "a1",
        "192.168.1.64/28": "a2", "192.168.1.80/28": "a2"
    },
    "e1": {ip: host for host, ip in ips_e1.items()},
    "e2": {ip: host for host, ip in ips_e2.items()},
    "e3": {ip: host for host, ip in ips_e3.items()},
    "e4": {ip: host for host, ip in ips_e4.items()}
}

# Função para visualizar o grafo
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

# Função para simular Ping
def ping(G, src, dst):
    if src not in G.nodes or dst not in G.nodes:
        print(f" Nó {src} ou {dst} não existe no grafo!")
        return
    
    if not nx.has_path(G, src, dst):
        print(f" Host {dst} inalcançável a partir de {src}!")
        return
    
    print(f" RTT de {src} ({ip_addresses[src]}) para {dst} ({ip_addresses[dst]})")
    path = nx.shortest_path(G, source=src, target=dst)
    
    for node in path:
        time.sleep(0.3)  # Simula o atraso de rede
        print(f" Passando por: {node} ({ip_addresses[node]})")

    print(f" Resposta recebida! Pacotes enviados: {len(path)}, Tempo médio: {len(path) * 0.3:.2f} ms\n")

# Função para simular Traceroute
def traceroute(G, src, dst):
    if src not in G.nodes or dst not in G.nodes:
        print(f" Nó {src} ou {dst} não existe no grafo!")
        return
    
    if not nx.has_path(G, src, dst):
        print(f" Rota para {dst} não encontrada!")
        return
    
    print(f" Traceroute de {src} ({ip_addresses[src]}) para {dst} ({ip_addresses[dst]})")
    path = nx.shortest_path(G, source=src, target=dst)
    
    for i, node in enumerate(path):
        time.sleep(0.3)  # Simula o atraso de rede
        print(f"{i + 1}: {node} ({ip_addresses[node]})")

    print(f" Traceroute completo! Saltos: {len(path) - 1}, Tempo total: {(len(path) - 1) * 0.3:.2f} ms\n")

# Menu interativo
def menu():
    print("=== Simulador de Rede ===")
    print("1. RTT")
    print("2. Traceroute")
    print("3. Sair")
    choice = input("Escolha uma opção: ")
    return choice

# Execução do programa
if __name__ == "__main__":
    plot_graph(graph)
    while True:
        choice = menu()
        if choice == "1":
            src = input("Digite o host de origem (ex: H11): ")
            dst = input("Digite o host de destino (ex: H21): ")
            ping(graph, src, dst)
        elif choice == "2":
            src = input("Digite o host de origem (ex: H11): ")
            dst = input("Digite o host de destino (ex: H21): ")
            traceroute(graph, src, dst)
        elif choice == "3":
            print("Saindo...")
            break
        else:
            print("Opção inválida. Tente novamente.")