import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import time
import random
import json
import os

# --- Funções Auxiliares ---

def generate_ips(subnet, num_hosts, prefix):
    base_ip_parts = subnet.split('/')[0].split('.')
    return {
        f"H{prefix}{i + 1}": f"{base_ip_parts[0]}.{base_ip_parts[1]}.{base_ip_parts[2]}.{int(base_ip_parts[3]) + i + 1}"
        for i in range(num_hosts)}


def create_default_config():
    """Cria/sobrescreve o arquivo de configuração com valores padrão."""
    config = {
        "subnets": {
            "e1": {
                "subnet": "192.168.1.0/28",
                "num_hosts": 2,
                "switch_ip": "192.168.1.30"
            },
            "e2": {
                "subnet": "192.168.1.32/28",
                "num_hosts": 2,
                "switch_ip": "192.168.1.62"
            },
            "e3": {
                "subnet": "192.168.1.64/27",
                "num_hosts": 3,
                "switch_ip": "192.168.1.78"
            },
            "e4": {
                "subnet": "192.168.1.80/27",
                "num_hosts": 3,
                "switch_ip": "192.168.1.94"
            }
        },
        "aggregation": {
            "a1": "192.168.1.97",
            "a2": "192.168.1.109"
        },
        "core": {
            "root": "192.168.1.254"
        },
        "connections": {
            "core_to_aggregation": "fibra_optica",
            "aggregation_to_edge": "fibra_optica",
            "edge_to_host": "par_trancado"
        },
        "bandwidth": {
            "core_to_aggregation": "10 Gbps",
            "aggregation_to_edge": "1 Gbps",
            "edge_to_host": "1 Gbps"
        }
    }

    file_exists = os.path.exists('network_config.json')

    with open('network_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    if file_exists:
        print("✓ Arquivo 'network_config.json' SOBRESCRITO com valores padrão.")
    else:
        print("✓ Arquivo 'network_config.json' CRIADO com valores padrão.")

    return config


def load_network_config(filename='network_config.json'):
    """Carrega a configuração da rede de um arquivo JSON."""
    if not os.path.exists(filename):
        print(f"⚠ Arquivo '{filename}' não encontrado. Criando configuração padrão...")
        return create_default_config()

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✓ Configuração carregada de '{filename}'")
        return config
    except json.JSONDecodeError:
        print(f"✗ Erro ao ler '{filename}'. Usando configuração padrão.")
        return create_default_config()

def assign_connection_types(graph, hosts):
    """
    Define os tipos de conexão obedecendo as regras de camada:
      - Core → Aggregation: fibra óptica
      - Aggregation → Edge: fibra óptica ou par trançado, consistente por switch
      - Edge → Hosts: qualquer tipo, consistente por switch
    """
    # Core → Aggregation
    for agg in ["a1", "a2"]:
        graph["root"][agg]['connection_type'] = "fibra_optica"

    # Aggregation → Edge
    agg_to_edge_type = {}  # guarda o tipo por switch de agregação
    for agg, edges in {"a1": ["e1", "e2"], "a2": ["e3", "e4"]}.items():
        tipo = random.choice(["fibra_optica", "par_trancado"])
        agg_to_edge_type[agg] = tipo
        for edge in edges:
            graph[agg][edge]['connection_type'] = tipo

    # Edge → Hosts
    for edge in ["e1", "e2", "e3", "e4"]:
        tipo = random.choice(["fibra_optica", "par_trancado", "sem_fio", "cabo_coaxial"])
        for host in hosts:
            if host.startswith("H" + edge[-1]):  # H1 → e1, H2 → e2, etc
                graph[edge][host]['connection_type'] = tipo

def setup_network_from_config(config):
    """Configura a rede com base no arquivo de configuração."""
    graph = nx.Graph()

    switches_borda = ["e1", "e2", "e3", "e4"]
    switches_agg = ["a1", "a2"]
    switch_root = "root"

    # Dicionários para armazenar IPs e hosts
    all_ips = {}
    hosts = []

    # Processar cada sub-rede
    for i, (switch, subnet_config) in enumerate(config['subnets'].items(), start=1):
        subnet = subnet_config['subnet']
        num_hosts = subnet_config['num_hosts']
        ips = generate_ips(subnet, num_hosts, str(i))
        all_ips.update(ips)
        hosts.extend(ips.keys())

    # Adicionar IPs dos switches
    for switch, subnet_config in config['subnets'].items():
        all_ips[switch] = subnet_config['switch_ip']

    # Adicionar IPs dos switches de agregação e core
    all_ips.update(config['aggregation'])
    all_ips.update(config['core'])

    # Criar grafo
    graph.add_nodes_from(hosts + switches_borda + switches_agg + [switch_root])

    # Obter tipos de conexão do config
    connections_config = config.get('connections', {
        "core_to_aggregation": "fibra_optica",
        "aggregation_to_edge": "fibra_optica",
        "edge_to_host": "par_trancado"
    })

    # Obter largura de banda do config
    bandwidth_config = config.get('bandwidth', {
        "core_to_aggregation": "10 Gbps",
        "aggregation_to_edge": "1 Gbps",
        "edge_to_host": "1 Gbps"
    })

    # Conectar switches na topologia de árvore com tipos de conexão
    # Core para Aggregation
    conn_type = connections_config.get("core_to_aggregation", "fibra_optica")
    bandwidth = bandwidth_config.get("core_to_aggregation", "10 Gbps")
    graph.add_edge("root", "a1", connection_type=conn_type, bandwidth=bandwidth)
    graph.add_edge("root", "a2", connection_type=conn_type, bandwidth=bandwidth)

    # Aggregation para Edge
    conn_type = connections_config.get("aggregation_to_edge", "fibra_optica")
    bandwidth = bandwidth_config.get("aggregation_to_edge", "1 Gbps")
    graph.add_edge("a1", "e1", connection_type=conn_type, bandwidth=bandwidth)
    graph.add_edge("a1", "e2", connection_type=conn_type, bandwidth=bandwidth)
    graph.add_edge("a2", "e3", connection_type=conn_type, bandwidth=bandwidth)
    graph.add_edge("a2", "e4", connection_type=conn_type, bandwidth=bandwidth)

    # Edge para Hosts
    conn_type = connections_config.get("edge_to_host", "par_trancado")
    bandwidth = bandwidth_config.get("edge_to_host", "1 Gbps")
    for host in hosts:
        if host.startswith('H1'):
            graph.add_edge("e1", host, connection_type=conn_type, bandwidth=bandwidth)
        elif host.startswith('H2'):
            graph.add_edge("e2", host, connection_type=conn_type, bandwidth=bandwidth)
        elif host.startswith('H3'):
            graph.add_edge("e3", host, connection_type=conn_type, bandwidth=bandwidth)
        elif host.startswith('H4'):
            graph.add_edge("e4", host, connection_type=conn_type, bandwidth=bandwidth)

    # Tabela de roteamento
    routing_table = {
        "a1": {config['subnets']['e1']['subnet']: "e1", config['subnets']['e2']['subnet']: "e2"},
        "a2": {config['subnets']['e3']['subnet']: "e3", config['subnets']['e4']['subnet']: "e4"},
        "root": {
            config['subnets']['e1']['subnet']: "a1", config['subnets']['e2']['subnet']: "a1",
            config['subnets']['e3']['subnet']: "a2", config['subnets']['e4']['subnet']: "a2"
        }
    }

    return graph, all_ips, hosts, routing_table


def setup_network_random():
    """Configura a rede de forma aleatória (comportamento original)."""
    graph = nx.Graph()

    switches_borda = ["e1", "e2", "e3", "e4"]
    switches_agg = ["a1", "a2"]
    switch_root = "root"

    # Gerando número aleatório de hosts para cada sub-rede (1 a 3 hosts)
    num_hosts_e1 = random.randint(1, 3)
    num_hosts_e2 = random.randint(1, 3)
    num_hosts_e3 = random.randint(1, 3)
    num_hosts_e4 = random.randint(1, 3)

    # Gerando IPs para cada sub-rede
    ips_e1 = generate_ips("192.168.1.0/28", num_hosts_e1, "1")
    ips_e2 = generate_ips("192.168.1.32/28", num_hosts_e2, "2")
    ips_e3 = generate_ips("192.168.1.64/27", num_hosts_e3, "3")
    ips_e4 = generate_ips("192.168.1.80/27", num_hosts_e4, "4")

    hosts = list(ips_e1.keys()) + list(ips_e2.keys()) + list(ips_e3.keys()) + list(ips_e4.keys())

    graph.add_nodes_from(hosts + switches_borda + switches_agg + [switch_root])

    # Tipos de conexão aleatórios
    connection_types = ["par_trancado", "fibra_optica", "sem_fio", "cabo_coaxial"]

    # Conectando os switches na topologia de árvore
    graph.add_edge("root", "a1", connection_type=random.choice(connection_types), bandwidth="10 Gbps")
    graph.add_edge("root", "a2", connection_type=random.choice(connection_types), bandwidth="10 Gbps")
    graph.add_edge("a1", "e1", connection_type=random.choice(connection_types), bandwidth="1 Gbps")
    graph.add_edge("a1", "e2", connection_type=random.choice(connection_types), bandwidth="1 Gbps")
    graph.add_edge("a2", "e3", connection_type=random.choice(connection_types), bandwidth="1 Gbps")
    graph.add_edge("a2", "e4", connection_type=random.choice(connection_types), bandwidth="1 Gbps")

    for host in ips_e1.keys():
        graph.add_edge("e1", host, connection_type=random.choice(connection_types), bandwidth="1 Gbps")
    for host in ips_e2.keys():
        graph.add_edge("e2", host, connection_type=random.choice(connection_types), bandwidth="1 Gbps")
    for host in ips_e3.keys():
        graph.add_edge("e3", host, connection_type=random.choice(connection_types), bandwidth="1 Gbps")
    for host in ips_e4.keys():
        graph.add_edge("e4", host, connection_type=random.choice(connection_types), bandwidth="1 Gbps")

    # Endereçamento IP de cada nó
    ip_addresses = {
        **ips_e1, **ips_e2, **ips_e3, **ips_e4,
        "e1": "192.168.1.30", "e2": "192.168.1.62",
        "e3": "192.168.1.78", "e4": "192.168.1.94",
        "a1": "192.168.1.97", "a2": "192.168.1.109",
        "root": "192.168.1.254"
    }

    # Tabela de roteamento
    routing_table = {
        "a1": {"192.168.1.0/27": "e1", "192.168.1.32/27": "e2"},
        "a2": {"192.168.1.64/28": "e3", "192.168.1.80/28": "e4"},
        "root": {
            "192.168.1.0/27": "a1", "192.168.1.32/27": "a1",
            "192.168.1.64/28": "a2", "192.168.1.80/28": "a2"
        }
    }

    return graph, ip_addresses, hosts, routing_table


# Variáveis globais
graph = None
ip_addresses = None
hosts = None
routing_table = None

# Definição de cores para cada tipo de conexão
CONNECTION_COLORS = {
    "par_trancado": "#FFA500",  # Laranja
    "fibra_optica": "#00FF00",  # Verde
    "sem_fio": "#FF1493",  # Rosa
    "cabo_coaxial": "#0000FF"  # Azul
}

CONNECTION_NAMES = {
    "par_trancado": "Par Trançado",
    "fibra_optica": "Fibra Óptica",
    "sem_fio": "Sem Fio",
    "cabo_coaxial": "Cabo Coaxial"
}

def get_path_latency(G, src, dst, packet_size_bits=8000):
    """Calcula a latência (RTT) simulada baseada na largura de banda e tipo de meio."""

    link_speed_map = {
        "par_trancado": 1_000_000_000,      # 1 Gbps
        "fibra_optica": 10_000_000_000,     # 10 Gbps
        "cabo_coaxial": 500_000_000,        # 500 Mbps
        "sem_fio": 300_000_000              # 300 Mbps
    }

    propagation_delay_map = {
        "par_trancado": 0.000005,
        "fibra_optica": 0.0000005,
        "cabo_coaxial": 0.000006,
        "sem_fio": 0.00000033
    }

    try:
        path = nx.shortest_path(G, source=src, target=dst)
        total_rtt = 0

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            dtype = G[u][v].get("connection_type", "fibra_optica")

            link_speed = link_speed_map.get(dtype, 1_000_000_000)
            prop_delay = propagation_delay_map.get(dtype, 0.000005)

            transmission_delay = packet_size_bits / link_speed
            total_rtt += (transmission_delay + prop_delay) * 2

        total_rtt *= random.uniform(0.95, 1.10)

        return total_rtt * 1000

    except nx.NetworkXNoPath:
        return float('inf')


def plot_graph(G):
    """Visualiza a topologia da rede com cores para cada tipo de conexão e IPs abaixo dos nós."""
    # Define a camada de cada nó para o layout multipartite
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

    # Posição dos nós (hierárquico)
    pos = nx.multipartite_layout(G, subset_key="layer", align="vertical")

    plt.figure(figsize=(14, 10))

    # --- Desenhar nós ---
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=2000)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')

    # --- Desenhar arestas por tipo de conexão ---
    for conn_type, color in CONNECTION_COLORS.items():
        edges_of_type = [(u, v) for u, v, data in G.edges(data=True)
                         if data.get('connection_type') == conn_type]
        if edges_of_type:
            nx.draw_networkx_edges(G, pos, edgelist=edges_of_type,
                                   edge_color=color, width=3, alpha=0.7)

    # --- Adicionar labels de IPs abaixo do nó ---
    ip_labels = {node: ip_addresses[node] for node in G.nodes if node in ip_addresses}
    offset_pos = {node: (x, y-0.1) for node, (x, y) in pos.items()}  # move o label um pouco para baixo
    nx.draw_networkx_labels(G, offset_pos, labels=ip_labels, font_size=9, font_color='black', font_weight='normal')

    # --- Legenda com velocidades dos links ---
    # Define velocidades realistas para cada tipo de conexão
    bandwidth_text = {
        "par_trancado": "1000 Mbps",
        "fibra_optica": "100000 Mbps",
        "sem_fio": "300 Mbps",
        "cabo_coaxial": "500 Mbps"
    }

    legend_elements = []
    for conn_type, color in CONNECTION_COLORS.items():
        if any(data.get("connection_type") == conn_type for _, _, data in G.edges(data=True)):
            legend_elements.append(
                mpatches.Patch(
                    color=color,
                    label=f"{CONNECTION_NAMES[conn_type]} - {bandwidth_text[conn_type]}"
                )
            )

    plt.legend(handles=legend_elements, loc='lower left', fontsize=10,
               title='Tipos de Conexão', title_fontsize=11)

    plt.title("Topologia de Rede em Árvore", fontsize=14, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    plt.show()



def display_link_capacities(G):
    """Exibe as capacidades de cada link na rede."""
    print("\n" + "=" * 80)
    print("CAPACIDADES DOS ENLACES DA REDE")
    print("=" * 80)
    print(f"{'Nó Origem':<12} {'Nó Destino':<12} {'Tipo de Conexão':<20} {'Capacidade':<15}")
    print("-" * 80)

    for u, v, data in G.edges(data=True):
        conn_type = data.get('connection_type', 'desconhecido')
        conn_name = CONNECTION_NAMES.get(conn_type, conn_type)
        bandwidth = data.get('bandwidth', 'não especificado')
        print(f"{u:<12} ↔ {v:<12} {conn_name:<20} {bandwidth:<15}")

    print("=" * 80 + "\n")


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


def display_connection_types(G):
    """Exibe os tipos de conexão de cada link na rede."""
    print("\n" + "=" * 60)
    print("TIPOS DE CONEXÃO DA REDE")
    print("=" * 60)

    # Agrupar por tipo de conexão
    connections_by_type = {}
    for u, v, data in G.edges(data=True):
        conn_type = data.get('connection_type', 'desconhecido')
        if conn_type not in connections_by_type:
            connections_by_type[conn_type] = []
        connections_by_type[conn_type].append((u, v))

    # Exibir agrupado
    for conn_type in sorted(connections_by_type.keys()):
        print(f"\n📡 {CONNECTION_NAMES.get(conn_type, conn_type.upper())}:")
        print("-" * 40)
        for u, v in sorted(connections_by_type[conn_type]):
            print(f"  {u:6} ↔ {v:6}")

    print("\n" + "=" * 60 + "\n")


def get_path_latency(G, src, dst):
    """Calcula a latência (RTT) simulada do caminho."""
    try:
        path = nx.shortest_path(G, source=src, target=dst)
        num_hops = len(path) - 1
        base_rtt = 2 * num_hops * 0.05
        rtt_sample = base_rtt * (1 + random.uniform(-0.1, 0.1))
        return rtt_sample
    except nx.NetworkXNoPath:
        return float('inf')


def get_host_addresses(G, src_host, dst_host):
    """Etapa 2: Obtém e exibe os endereços IP dos hosts de origem e destino."""
    print("\n" + "=" * 60)
    print("[Etapa 2] Obtenção de Endereços IP do Host Origem e Destino")
    print("=" * 60)

    if src_host not in G.nodes:
        print(f"\n✗ ERRO: Host '{src_host}' não existe na rede!")
        return None, None

    if dst_host not in G.nodes:
        print(f"\n✗ ERRO: Host '{dst_host}' não existe na rede!")
        return None, None

    if src_host not in ip_addresses:
        print(f"\n✗ ERRO: IP do host '{src_host}' não está mapeado!")
        return None, None

    if dst_host not in ip_addresses:
        print(f"\n✗ ERRO: IP do host '{dst_host}' não está mapeado!")
        return None, None

    src_ip = ip_addresses[src_host]
    dst_ip = ip_addresses[dst_host]

    print(f"\n✓ Host de Origem Localizado:")
    print(f"  - Nome do Host: {src_host}")
    print(f"  - Endereço IP: {src_ip}")

    print(f"\n✓ Host de Destino Localizado:")
    print(f"  - Nome do Host: {dst_host}")
    print(f"  - Endereço IP: {dst_ip}")

    if not nx.has_path(G, src_host, dst_host):
        print(f"\n✗ AVISO: Host de destino {dst_host} ({dst_ip}) é inalcançável a partir de {src_host} ({src_ip})!")
        return None, None

    print(f"\n✓ Conectividade: OK (Caminho existe entre os hosts)")
    print("=" * 60 + "\n")

    return src_ip, dst_ip


def xprobe_rtt(G, src, dst, num_samples=3):
    """Simula o XProbe (Medição de RTT) com N amostras."""
    print("\n" + "=" * 60)
    print("[Etapa 3] Simulação XProbe/RTT - Verificação de Disponibilidade")
    print("=" * 60)

    if src not in G.nodes or dst not in G.nodes:
        print(f"\n✗ ERRO: Host {src} ou {dst} não existe na rede!")
        return None

    if not nx.has_path(G, src, dst):
        print(
            f"\n✗ ERRO: Host destino {dst} ({ip_addresses[dst]}) é INALCANÇÁVEL a partir de {src} ({ip_addresses[src]})!")
        print("❌ HOST DESTINO INATIVO ou SEM CAMINHO DE REDE")
        print("=" * 60 + "\n")
        return None

    print(f"\n✓ Host Destino ATIVO e ALCANÇÁVEL")
    print(f"  - Origem: {src} ({ip_addresses[src]})")
    print(f"  - Destino: {dst} ({ip_addresses[dst]})")

    rtt_times = []

    print(f"\n--- Coleta de Amostras de RTT ---")

    path = nx.shortest_path(G, source=src, target=dst)
    print(f"  - Rota (Saltos): {' → '.join(path)}")
    print(f"  - Número de saltos: {len(path) - 1}")

    # Mostrar tipos de conexão no caminho
    print(f"\n  - Tipos de conexão no caminho:")
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        conn_type = G[u][v].get('connection_type', 'desconhecido')
        print(f"    {u} → {v}: {CONNECTION_NAMES.get(conn_type, conn_type)}")

    print()

    for i in range(num_samples):
        rtt = get_path_latency(G, src, dst)
        rtt_times.append(rtt)
        print(f"  Amostra {i + 1}: RTT = {rtt:.4f} ms")
        time.sleep(0.5)

    if rtt_times:
        rtt_mean = sum(rtt_times) / len(rtt_times)
        rtt_min = min(rtt_times)
        rtt_max = max(rtt_times)

        print("\n" + "=" * 60)
        print("✅ RESULTADO DA SIMULAÇÃO XPROBE")
        print("=" * 60)
        print(f"  RTT Mínimo: {rtt_min:.4f} ms")
        print(f"  RTT Máximo: {rtt_max:.4f} ms")
        print(f"  📊 RTT MÉDIO: {rtt_mean:.4f} ms")
        print("=" * 60 + "\n")

        return rtt_mean

    return None


def menu():
    print("\n=== Simulador de Rede ===")
    print("1. Visualizar Topologia")
    print("2. Exibir Tabelas de Roteamento")
    print("3. Exibir Tipos de Conexão")
    print("4. Exibir Capacidades dos Enlaces")
    print("5. Obter IPs e Executar Simulação XProbe/RTT")
    print("6. Reconfigurar Rede")
    print("7. Sair")
    choice = input("Escolha uma opção: ")
    return choice


def config_menu():
    print("\n=== Configuração da Rede ===")
    print("1. Carregar configuração de arquivo (network_config.json)")
    print("2. Gerar rede aleatória")
    print("3. Restaurar arquivo de configuração padrão (SOBRESCREVE)")
    choice = input("Escolha uma opção: ")
    return choice


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  SIMULADOR DE REDE HIERÁRQUICA - XPROBE")
    print("=" * 50)

    print("\n[Etapa 1] Iniciando o programa...")
    print("\n[Etapa 2] Importar/Definir Configuração da Rede")

    config_choice = config_menu()

    if config_choice == "1":
        config = load_network_config()
        graph, ip_addresses, hosts, routing_table = setup_network_from_config(config)
        assign_connection_types(graph, hosts)
        print(f"\n✓ Rede configurada a partir do arquivo.")
    elif config_choice == "2":
        graph, ip_addresses, hosts, routing_table = setup_network_random()
        assign_connection_types(graph, hosts)
        print(f"\n✓ Rede gerada aleatoriamente.")
    elif config_choice == "3":
        config = create_default_config()
        graph, ip_addresses, hosts, routing_table = setup_network_from_config(config)
        assign_connection_types(graph, hosts)
        print(f"\n✓ Rede configurada com valores padrão e pronta para uso.")
    else:
        print("Opção inválida. Usando configuração aleatória.")
        graph, ip_addresses, hosts, routing_table = setup_network_random()
        assign_connection_types(graph, hosts)

    print(f"\nHosts Gerados: {hosts}")
    print(f"Total de hosts: {len(hosts)}")

    while True:
        choice = menu()
        if choice == "1":
            plot_graph(graph)
        elif choice == "2":
            display_routing_tables(routing_table)
        elif choice == "3":
            display_connection_types(graph)
        elif choice == "4":
            display_link_capacities(graph)
        elif choice == "5":
            print("\nHosts disponíveis:", hosts)
            src = input("Digite o host de origem (ex: H11): ")
            dst = input("Digite o host de destino (ex: H21): ")

            src_ip, dst_ip = get_host_addresses(graph, src, dst)

            if src_ip is not None and dst_ip is not None:
                print("\n[Etapa 3] Executando Simulação XProbe/RTT...")
                xprobe_rtt(graph, src, dst)
        elif choice == "6":
            print("\n[Etapa 2] Reconfigurar Rede")
            config_choice = config_menu()

            if config_choice == "1":
                config = load_network_config()
                graph, ip_addresses, hosts, routing_table = setup_network_from_config(config)
                assign_connection_types(graph, hosts)
                print(f"\n✓ Rede reconfigurada a partir do arquivo.")
            elif config_choice == "2":
                graph, ip_addresses, hosts, routing_table = setup_network_random()
                assign_connection_types(graph, hosts)
                print(f"\n✓ Rede regenerada aleatoriamente.")
            elif config_choice == "3":
                config = create_default_config()
                graph, ip_addresses, hosts, routing_table = setup_network_from_config(config)
                assign_connection_types(graph, hosts)
                print(f"\n✓ Rede reconfigurada com valores padrão e pronta para uso.")
            else:
                print("Opção inválida.")

            print(f"\nHosts Gerados: {hosts}")
            print(f"Total de hosts: {len(hosts)}")
        elif choice == "7":
            print("Saindo...")
            break
        else:
            print("Opção inválida. Tente novamente.")