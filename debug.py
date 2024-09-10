from llm_model import *

def print_logical_steps(question, logical_steps):
    """Função auxiliar para depurar e imprimir os passos lógicos da saída do step_1."""
    
    # Imprime os passos lógicos, um por linha
    print("Passos lógicos gerados:")
    steps_list = logical_steps.steps.split('\n')  # Divide os passos por linhas
    for i, step in enumerate(steps_list, 1):
        print(f"Step {i}: {step}")

    print("\n")

def debug_step_1(perguntas):
    """Função para testar o step_1_comprehend_question com uma lista de perguntas."""
    
    # Itera sobre a lista de perguntas e processa cada uma
    for pergunta in perguntas:
        # Imprime a pergunta
        print(f"Pergunta: {pergunta}\n")
        passos_logicos = step_1_comprehend_question(pergunta)
        print_logical_steps(pergunta, passos_logicos)

def debug_step_2(perguntas):
    """Função para testar o step_2_generate_flags com uma lista de perguntas."""
    
    # Itera sobre a lista de perguntas e processa cada uma
    for pergunta in perguntas:
        print(f"\nPergunta: {pergunta}")
        
        # Primeiro, executa o step_1 para obter os passos lógicos
        passos_logicos = step_1_comprehend_question(pergunta)
        # print_logical_steps(pergunta, passos_logicos)
        
        # Agora, executa o step_2 para gerar as flags com base nos passos lógicos
        flags = step_2_generate_flags(passos_logicos)
        
        # Imprime as flags geradas
        print(f"Flags geradas: {flags.dict()}")
        print("\n")

def debug_step_3(perguntas):
    """Função para testar o step_3_process_with_flags com uma lista de perguntas."""
    
    # Itera sobre a lista de perguntas e processa cada uma
    for pergunta in perguntas:
        print(f"\nPergunta: {pergunta}")
        
        # Step 1: Compreensão da pergunta para obter os passos lógicos
        passos_logicos = step_1_comprehend_question(pergunta)
        
        # Step 2: Geração de flags com base nos passos lógicos
        flags = step_2_generate_flags(passos_logicos)
        
        # Step 3: Processamento com base nas flags geradas
        processed_data = step_3_process_with_flags(flags)
        
        # Imprime o resultado do processamento
        print(f"Resultado do processamento: {processed_data}")



if __name__ == "__main__":
    perguntas_debug = [
    "Qual cliente tem a pior qualidade de recepção de vídeo ao longo do tempo para o cliente rj e servidor pi entre 07/06/2024 e 10/06/2024?",
    # "Qual servidor fornece a QoE mais consistente para o cliente rj entre 07/06/2024 e 10/06/2024?",
    # "Qual é a melhor estratégia de troca de servidor para maximizar a qualidade de experiência do cliente rj entre 07/06/2024 e 10/06/2024?",
    # "Se a latência aumentar 20%, como isso afeta a QoE do cliente rj e servidor pi entre 07/06/2024 e 10/06/2024?",
    # "Qual o bitrate médio dentro de cada rajada para o cliente rj e o servidor pi no período entre 07/06/2024 e 10/06/2024?",
    # "Qual a latência nas medições que coincidem com a janela de tempo das rajadas de medição de bitrate para o cliente rj e o servidor pi no período entre 07/06/2024 e 10/06/2024?",
]
    perguntas_fora_escopo = [
    "Qual o endereço de IP do cliente rj na rede?",
    "Qual é a previsão do tempo para amanhã?"
]   
    debug_step_1(perguntas_debug)
    debug_step_2(perguntas_debug)
    debug_step_3(perguntas_debug)

    # debug_step_3(perguntas_fora_escopo)