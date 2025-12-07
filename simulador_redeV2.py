import networkx as nx
import matplotlib.pyplot as plt
import time
import random
import json
import os

# --- Funções Auxiliares (Não Modificadas) ---

# Função para gerar IPs aleatórios em uma sub-rede
def generate_ips(subnet, num_hosts, prefix):
    base_ip_parts = subnet.split('/')[0].split('.')
    return {f"H{prefix}{i+1}": f"{base_ip_parts[0]}.{base_ip_parts[1]}.{base_ip_parts[2]}.{int(base_ip_parts[3]) + i + 1}" for i in range(num_hosts)}

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
    
    # Conectar switches na topologia de árvore
    graph.add_edges_from([
        ("root", "a1"), ("root", "a2"),
        ("a1", "e1"), ("a1", "e2"),
        ("a2", "e3"), ("a2", "e4"),
    ])
    
    # Conectar hosts aos switches de borda
    for host in hosts:
        if host.startswith('H1'):
            graph.add_edge("e1", host)
        elif host.startswith('H2'):
            graph.add_edge("e2", host)
        elif host.startswith('H3'):
            graph.add_edge("e3", host)
        elif host.startswith('H4'):
            graph.add_edge("e4", host)
    
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

# --- Definição da Topologia e Endereçamento (Pode variar a cada execução) ---

# Variáveis globais que serão inicializadas na configuração
graph = None
ip_addresses = None
hosts = None
routing_table = None

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

def get_host_addresses(G, src_host, dst_host):
    """Etapa 2: Obtém e exibe os endereços IP dos hosts de origem e destino."""
    print("\n" + "="*60)
    print("[Etapa 2] Obtenção de Endereços IP do Host Origem e Destino")
    print("="*60)
    
    # Validação dos hosts
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
    
    # Obter os IPs
    src_ip = ip_addresses[src_host]
    dst_ip = ip_addresses[dst_host]
    
    # Exibir informações de origem
    print(f"\n✓ Host de Origem Localizado:")
    print(f"  - Nome do Host: {src_host}")
    print(f"  - Endereço IP: {src_ip}")
    
    # Exibir informações de destino
    print(f"\n✓ Host de Destino Localizado:")
    print(f"  - Nome do Host: {dst_host}")
    print(f"  - Endereço IP: {dst_ip}")
    
    # Verificar conectividade
    if not nx.has_path(G, src_host, dst_host):
        print(f"\n✗ AVISO: Host de destino {dst_host} ({dst_ip}) é inalcançável a partir de {src_host} ({src_ip})!")
        return None, None
    
    print(f"\n✓ Conectividade: OK (Caminho existe entre os hosts)")
    print("="*60 + "\n")
    
    return src_ip, dst_ip

def xprobe_rtt(G, src, dst, num_samples=3):
    """Simula o XProbe (Medição de RTT) com N amostras."""
    print("\n" + "="*60)
    print("[Etapa 3] Simulação XProbe/RTT - Verificação de Disponibilidade")
    print("="*60)
    
    # Validação básica dos hosts
    if src not in G.nodes or dst not in G.nodes:
        print(f"\n✗ ERRO: Host {src} ou {dst} não existe na rede!")
        return None
    
    # Verificação de conectividade (host destino ativo)
    if not nx.has_path(G, src, dst):
        print(f"\n✗ ERRO: Host destino {dst} ({ip_addresses[dst]}) é INALCANÇÁVEL a partir de {src} ({ip_addresses[src]})!")
        print("❌ HOST DESTINO INATIVO ou SEM CAMINHO DE REDE")
        print("="*60 + "\n")
        return None
    
    print(f"\n✓ Host Destino ATIVO e ALCANÇÁVEL")
    print(f"  - Origem: {src} ({ip_addresses[src]})")
    print(f"  - Destino: {dst} ({ip_addresses[dst]})")

    rtt_times = []
    
    print(f"\n--- Coleta de Amostras de RTT ---")
    
    path = nx.shortest_path(G, source=src, target=dst)
    print(f"  - Rota (Saltos): {' → '.join(path)}")
    print(f"  - Número de saltos: {len(path) - 1}\n")

    for i in range(num_samples):
        # Simula o tempo de latência de ida e volta
        rtt = get_path_latency(G, src, dst)
        rtt_times.append(rtt)
        print(f"  Amostra {i+1}: RTT = {rtt:.4f} ms")
        time.sleep(0.5) # Simula um pequeno intervalo entre as amostras

    # Cálculo do RTT Médio
    if rtt_times:
        rtt_mean = sum(rtt_times) / len(rtt_times)
        rtt_min = min(rtt_times)
        rtt_max = max(rtt_times)
        
        print("\n" + "="*60)
        print("✅ RESULTADO DA SIMULAÇÃO XPROBE")
        print("="*60)
        print(f"  RTT Mínimo: {rtt_min:.4f} ms")
        print(f"  RTT Máximo: {rtt_max:.4f} ms")
        print(f"  📊 RTT MÉDIO: {rtt_mean:.4f} ms")
        print("="*60 + "\n")
        
        return rtt_mean
    
    return None
    
# --- Funções do Menu (Modificadas) ---

def menu():
    print("\n=== Simulador de Rede ===")
    print("1. Visualizar Topologia")
    print("2. Exibir Tabelas de Roteamento")
    print("3. Obter IPs e Executar Simulação XProbe/RTT")
    print("4. Reconfigurar Rede")
    print("5. Sair")
    choice = input("Escolha uma opção: ")
    return choice

def config_menu():
    print("\n=== Configuração da Rede ===")
    print("1. Carregar configuração de arquivo (network_config.json)")
    print("2. Gerar rede aleatória")
    print("3. Restaurar arquivo de configuração padrão (SOBRESCREVE)")
    choice = input("Escolha uma opção: ")
    return choice

# --- Execução do Programa (Modificada) ---
if __name__ == "__main__":
    print("\n" + "="*50)
    print("  SIMULADOR DE REDE HIERÁRQUICA - XPROBE")
    print("="*50)
    
    # Etapa 1: Iniciar o programa
    print("\n[Etapa 1] Iniciando o programa...")
    
    # Etapa 2: Importar/definir a configuração da rede
    print("\n[Etapa 2] Importar/Definir Configuração da Rede")
    
    config_choice = config_menu()
    
    if config_choice == "1":
        config = load_network_config()
        graph, ip_addresses, hosts, routing_table = setup_network_from_config(config)
        print(f"\n✓ Rede configurada a partir do arquivo.")
    elif config_choice == "2":
        graph, ip_addresses, hosts, routing_table = setup_network_random()
        print(f"\n✓ Rede gerada aleatoriamente.")
    elif config_choice == "3":
        config = create_default_config()
        graph, ip_addresses, hosts, routing_table = setup_network_from_config(config)
        print(f"\n✓ Rede configurada com valores padrão e pronta para uso.")
    else:
        print("Opção inválida. Usando configuração aleatória.")
        graph, ip_addresses, hosts, routing_table = setup_network_random()
    
    print(f"\nHosts Gerados: {hosts}")
    print(f"Total de hosts: {len(hosts)}")

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
            
            # Etapa 2: Obter endereços IP
            src_ip, dst_ip = get_host_addresses(graph, src, dst)
            
            # Se a Etapa 2 foi bem-sucedida, executar a Etapa 3 (XProbe/RTT)
            if src_ip is not None and dst_ip is not None:
                print("\n[Etapa 3] Executando Simulação XProbe/RTT...")
                xprobe_rtt(graph, src, dst)
        elif choice == "4":
            print("\n[Etapa 2] Reconfigurar Rede")
            config_choice = config_menu()
            
            if config_choice == "1":
                config = load_network_config()
                graph, ip_addresses, hosts, routing_table = setup_network_from_config(config)
                print(f"\n✓ Rede reconfigurada a partir do arquivo.")
            elif config_choice == "2":
                graph, ip_addresses, hosts, routing_table = setup_network_random()
                print(f"\n✓ Rede regenerada aleatoriamente.")
            elif config_choice == "3":
                config = create_default_config()
                graph, ip_addresses, hosts, routing_table = setup_network_from_config(config)
                print(f"\n✓ Rede reconfigurada com valores padrão e pronta para uso.")
            else:
                print("Opção inválida.")
            
            print(f"\nHosts Gerados: {hosts}")
            print(f"Total de hosts: {len(hosts)}")
        elif choice == "5":
            print("Saindo...")
            break
        else:
            print("Opção inválida. Tente novamente.")