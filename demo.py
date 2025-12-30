import time

# ==============================================================================
# 1. CONSTANTES BACKEND (Ce que l'utilisateur ne voit pas)
# ==============================================================================
# Ces valeurs restent fixes car elles dépendent de l'infrastructure Fluid Topics
CONSTANTS = {
    "PUE": 1.2,
    "CARBON_INTENSITY": 475,          # gCO2/kWh
    "LLM_ENERGY_PER_1K_TOKENS": 0.0006, 
    "LLM_STATIC_POWER_KW": 0.250,       
    "LLM_AVG_LATENCY_S": 2.0,
    "TOKENS_PER_CHAR": 0.25
}

# Paramètres par défaut (si on appuie juste sur Entrée)
DEFAULT_TOPIC_SIZE = 3000
DEFAULT_CONTEXT_DOCS = 3

def get_real_conversation_params():
    print(f"\n{'='*60}")
    print(f"🎤 DÉMO INTERACTIVE : ANALYSEZ VOTRE PROMPT EN TEMPS RÉEL")
    print(f"{'='*60}")

    # 1. Récupérer le Prompt réel (La "Convo")
    print("\n✍️  Veuillez saisir votre question (Prompt) ci-dessous :")
    user_prompt = input("> ")
    
    if not user_prompt.strip():
        user_prompt = "Quelle est mon empreinte carbone ?" # Valeur par défaut
        print(f"   (Aucune saisie, utilisation du prompt par défaut : '{user_prompt}')")

    prompt_size = len(user_prompt)

    # 2. Configurer le contexte (Le "Backend")
    print(f"\n📚 Configuration du contexte documentaire (Appuyez sur Entrée pour défaut):")
    
    try:
        t_size = input(f"   - Taille moyenne d'un document (défaut {DEFAULT_TOPIC_SIZE} car.) : ")
        topic_size = int(t_size) if t_size.strip() else DEFAULT_TOPIC_SIZE
        
        n_docs = input(f"   - Nombre de documents lus par l'IA (défaut {DEFAULT_CONTEXT_DOCS}) : ")
        context_docs = int(n_docs) if n_docs.strip() else DEFAULT_CONTEXT_DOCS
        
    except ValueError:
        print("   ⚠️ Saisie invalide, utilisation des valeurs par défaut.")
        topic_size = DEFAULT_TOPIC_SIZE
        context_docs = DEFAULT_CONTEXT_DOCS

    # 3. Estimation de la réponse
    output_size = 350 # Moyenne standard pour une réponse de chatbot

    return {
        "TOPIC_SIZE_CHARS": topic_size,
        "PROMPT_SIZE_CHARS": prompt_size,
        "OUTPUT_SIZE_CHARS": output_size,
        "CHATBOT_CONTEXT_TOPICS": context_docs,
        "USER_TEXT": user_prompt
    }

def calculate_impact(params):
    # Calcul des volumes
    input_context_chars = params["CHATBOT_CONTEXT_TOPICS"] * params["TOPIC_SIZE_CHARS"]
    input_total_chars = input_context_chars + params["PROMPT_SIZE_CHARS"]
    total_chars = input_total_chars + params["OUTPUT_SIZE_CHARS"]
    total_tokens = total_chars * CONSTANTS["TOKENS_PER_CHAR"]

    # Calcul Énergétique
    energy_dynamic = (total_tokens / 1000) * CONSTANTS["LLM_ENERGY_PER_1K_TOKENS"]
    duration_hours = CONSTANTS["LLM_AVG_LATENCY_S"] / 3600
    energy_static = duration_hours * CONSTANTS["LLM_STATIC_POWER_KW"]
    
    total_energy = (energy_dynamic + energy_static) * CONSTANTS["PUE"]
    carbon_g = total_energy * CONSTANTS["CARBON_INTENSITY"]

    # Affichage des résultats
    print(f"\n{'-'*60}")
    print(f"📊 RÉSULTATS POUR : \"{params['USER_TEXT'][:50]}...\"")
    print(f"{'-'*60}")
    
    print(f"1️⃣  CE QUE VOUS AVEZ ÉCRIT :")
    print(f"    Taille du prompt       : {params['PROMPT_SIZE_CHARS']} caractères")
    
    print(f"\n2️⃣  CE QUE L'IA A LU (INVISIBLE) :")
    print(f"    Documents consultés    : {params['CHATBOT_CONTEXT_TOPICS']} docs")
    print(f"    Volume documentaire    : {input_context_chars} caractères")
    print(f"    ➔ L'IA a lu {input_context_chars // params['PROMPT_SIZE_CHARS']} fois plus de texte que vous n'en avez écrit !")

    print(f"\n3️⃣  IMPACT PHYSIQUE :")
    print(f"    Volume total traité    : {total_tokens:.0f} Tokens")
    print(f"    🔋 Énergie consommée   : {total_energy:.6f} kWh")
    print(f"    🌍 Empreinte Carbone   : {carbon_g:.4f} gCO2e")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    # Boucle pour tester plusieurs phrases d'affilée
    while True:
        sim_params = get_real_conversation_params()
        calculate_impact(sim_params)
        
        again = input("Voulez-vous tester une autre phrase ? (o/n) : ")
        if again.lower() != 'o':
            break