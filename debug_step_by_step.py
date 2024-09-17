from llm_model import *

def print_logical_steps(logical_steps):
    """Função auxiliar para depurar e imprimir os passos lógicos da saída do step_1."""
    
    # Imprime os passos lógicos, um por linha
    print("Passos lógicos gerados:")
    steps_list = logical_steps.steps.split('\n')  # Divide os passos por linhas
    for i, step in enumerate(steps_list, 1):
        print(f"Step {i}: {step}")

    print("\n")

def debug_step_1(pergunta):
    """Função para testar o step_1_comprehend_question com uma pergunta."""
    
    passos_logicos = step_1_comprehend_question(pergunta)
    print_logical_steps(pergunta, passos_logicos)

def debug_step_2(pergunta):
    """Função para testar o step_2_generate_flags com uma pergunta."""
    
    # Primeiro, executa o step_1 para obter os passos lógicos
    passos_logicos = step_1_comprehend_question(pergunta)
    
    # Agora, executa o step_2 para gerar as flags com base nos passos lógicos
    flags = step_2_generate_flags(passos_logicos)
    
    # Imprime as flags geradas
    print(f"Flags geradas: {flags.dict()}")
    print("\n")

def debug_step_3(pergunta):
    """Função para testar o step_3_process_with_flags com uma pergunta."""
    
    # Step 1: Compreensão da pergunta para obter os passos lógicos
    passos_logicos = step_1_comprehend_question(pergunta)
    
    # Step 2: Geração de flags com base nos passos lógicos
    flags = step_2_generate_flags(passos_logicos)
    
    # Step 3: Processamento com base nas flags geradas
    processed_data, _ = step_3_process_with_flags(flags)
    
    # Imprime o resultado do processamento
    print(f"Resultado do processamento: {processed_data}")
    print("\n")


def debug_step_4(pergunta):
    """Função para testar o step_4_generate_answer com uma pergunta."""
    
    # Step 1: Compreensão da pergunta para obter os passos lógicos
    passos_logicos = step_1_comprehend_question(pergunta)
    
    # Step 2: Geração de flags com base nos passos lógicos
    flags = step_2_generate_flags(passos_logicos)
    
    # Step 3: Processamento com base nas flags geradas
    processed_data, _ = step_3_process_with_flags(pergunta, flags)
    
    # Step 4: Geração da resposta com base nos dados processados
    resposta = step_4_generate_response(processed_data)
    
    # Imprime a resposta gerada
    print(f"Resposta gerada: {resposta}")
    print("\n")

if __name__ == "__main__":
    perguntas_debug = [
        "Qual o bitrate médio dentro de cada rajada para o cliente rj e o servidor pi no período entre as 08 e 09h do dia 07/06/2024?",
        "Qual a latência nas medições que coincidem com a janela de tempo das rajadas de medição de bitrate para o cliente rj e o servidor pi no período entre as 08 e 09h do dia 07/06/2024?",
        "Qual cliente tem a pior qualidade de recepção de vídeo entre as 08 e 09h do dia 07/06/2024?",
        "Qual servidor fornece a QoE mais consistente para o cliente rj entre as 08 e 09h do dia 07/06/2024?",
        "Qual é a melhor estratégia de troca de servidor para maximizar a qualidade de experiência do cliente rj entre as 08 e 09h do dia 07/06/2024?",
        "Se a latência aumentar 20%, como isso afeta a QoE do cliente rj e servidor pi entre as 08 e 09h do dia 07/06/2024?",
    ]
        
    perguntas_fora_escopo = [
        "Qual o endereço de IP do cliente rj na rede?",
        "Qual é a previsão do tempo para amanhã?"
    ]   

    for pergunta in perguntas_debug:
        # Imprime a pergunta
        print(f"Pergunta: {pergunta}")
        # debug_step_1(pergunta)
        # debug_step_2(pergunta)
        # debug_step_3(pergunta)
        responder_pergunta(pergunta)

    for pergunta in perguntas_fora_escopo:
        # Imprime a pergunta
        print(f"Pergunta: {pergunta}")
        responder_pergunta(pergunta)