import yaml
import pandas as pd
import os

# 1. PARAMÈTRES DE SIMULATION (D'après 2025-FluidTopic-analytics-explanations.md)

SIMULATION_PARAMS = {
    "TOPIC_SIZE_CHARS": 3000,      # Taille moyenne d'un topic (caractères)
    "PROMPT_SIZE_CHARS": 500,      # Taille moyenne du prompt utilisateur
    "OUTPUT_SIZE_CHARS": 350,      # Moyenne entre 200 et 400 chars (réponse IA)
    "CHATBOT_CONTEXT_TOPICS": 3,   # Nombre moyen de topics injectés dans le contexte (1-50)
    
    # Facteurs de conversion
    "TOKENS_PER_CHAR": 0.25,       # Approx: 1 token ~= 4 chars (Anglais/Français)
}


# 2. CONSTANTES ÉNERGÉTIQUES ( État de l'Art)


CONSTANTS = {
    "PUE": 1.2,
    "CARBON_INTENSITY": 475,          # gCO2/kWh (Global Cloud Mix)
    
    # LLM (Generation)
    "LLM_ENERGY_PER_1K_TOKENS": 0.0006, # Mixte Prompt/Decode
    "LLM_STATIC_POWER_KW": 0.250,       # Conso carte graphique active
    "LLM_AVG_LATENCY_S": 2.0,           # Temps estimé par requête (pour le statique)

    # NMT (Traduction)
    "NMT_ENERGY_PER_CHAR": 0.000004,    # DeepL Proxy
}

# ==============================================================================
# 3. MOTEUR DE SIMULATION ET CALCUL
# ==============================================================================

def process_genai_data(yaml_data):
    """
    Traite la section 'genai' du YAML en appliquant les règles de simulation.
    """
    records = []
    
    if 'genai' not in yaml_data:
        print(" Section 'genai' introuvable dans le YAML.")
        return pd.DataFrame()

    genai_section = yaml_data['genai']
    
    # On itère sur les clés (chatbots, completions, translations...)
    for profile_type, data_list in genai_section.items():
        if not isinstance(data_list, list):
            continue # On ignore les descriptions ou métadonnées
            
        print(f"   -> Traitement du profil : {profile_type} ({len(data_list)} jours)")
        
        for entry in data_list:
            date = entry.get('date')
            count = entry.get('count', 0)
            
            # --- ÉTAPE A : SIMULATION DES VOLUMES ---
            estimated_chars_input = 0
            estimated_chars_output = 0
            is_translation = False
            
            # Règle 1 : CHATBOT (Input = n*topics + prompt | Output = generated)
            if 'chatbot' in profile_type.lower():
                input_context = (SIMULATION_PARAMS["CHATBOT_CONTEXT_TOPICS"] * SIMULATION_PARAMS["TOPIC_SIZE_CHARS"])
                estimated_chars_input = input_context + SIMULATION_PARAMS["PROMPT_SIZE_CHARS"]
                estimated_chars_output = SIMULATION_PARAMS["OUTPUT_SIZE_CHARS"]
                
            # Règle 2 : COMPLETION (Input = topic + prompt | Output = generated)
            elif 'completion' in profile_type.lower():
                estimated_chars_input = SIMULATION_PARAMS["TOPIC_SIZE_CHARS"] + SIMULATION_PARAMS["PROMPT_SIZE_CHARS"]
                estimated_chars_output = SIMULATION_PARAMS["OUTPUT_SIZE_CHARS"]
                
            # Règle 3 : TRANSLATION (Input = topic | Output = topic)
            elif 'translation' in profile_type.lower() or 'nmt' in profile_type.lower():
                is_translation = True
                estimated_chars_input = SIMULATION_PARAMS["TOPIC_SIZE_CHARS"]
                estimated_chars_output = SIMULATION_PARAMS["TOPIC_SIZE_CHARS"]
            
            # Calcul des totaux pour la journée
            daily_total_chars = (estimated_chars_input + estimated_chars_output) * count
            daily_total_tokens = daily_total_chars * SIMULATION_PARAMS["TOKENS_PER_CHAR"]
            
            # --- ÉTAPE B : CALCUL ÉNERGÉTIQUE ---
            energy_kwh = 0
            
            if is_translation:
                # Formule NMT : basée sur les caractères
                energy_kwh = daily_total_chars * CONSTANTS["NMT_ENERGY_PER_CHAR"]
            else:
                # Formule LLM : basée sur les tokens + latence statique
                # Estimation temps total = count * latence moyenne
                total_duration_hours = (count * CONSTANTS["LLM_AVG_LATENCY_S"]) / 3600
                
                energy_dynamic = (daily_total_tokens / 1000) * CONSTANTS["LLM_ENERGY_PER_1K_TOKENS"]
                energy_static = total_duration_hours * CONSTANTS["LLM_STATIC_POWER_KW"]
                energy_kwh = energy_dynamic + energy_static

            energy_kwh *= CONSTANTS["PUE"]
            carbon_g = energy_kwh * CONSTANTS["CARBON_INTENSITY"]

            records.append({
                'date': date,
                'profile_type': profile_type,
                'count': count,
                'simulated_tokens': int(daily_total_tokens),
                'simulated_chars': int(daily_total_chars),
                'energy_kwh': round(energy_kwh, 6),
                'carbon_gCO2': round(carbon_g, 2)
            })

    return pd.DataFrame(records)

# 4. EXÉCUTION PRINCIPALE

def main():
    input_file = 'data/2025-FluidTopics-daily-analytics.yaml'
    output_file = 'output/rapport_carbone_simule.csv'
    
    if not os.path.exists(input_file):
        print(f" Erreur: Fichier {input_file} introuvable.")
        return

    print(f" Lecture du fichier : {input_file}")
    with open(input_file, 'r') as f:
        try:
            yaml_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f" Erreur YAML : {e}")
            return

    # Traitement
    print("  Lancement de la simulation basée sur les profils...")
    df = process_genai_data(yaml_data)
    
    if df.empty:
        print(" Aucune donnée générée. Vérifiez les clés du YAML (chatbots, completions...).")
        return

    # Résultats Aggrégés
    total_co2 = df['carbon_gCO2'].sum() / 1000 # kg
    total_kwh = df['energy_kwh'].sum()
    
    print("-" * 60)
    print("RÉSULTATS DE LA SIMULATION")
    print("-" * 60)
    print(f"Nombre de jours analysés : {len(df)}")
    print(f"Total Requêtes (Count)   : {df['count'].sum()}")
    print(f"Volume Simulé (Tokens)   : {df['simulated_tokens'].sum():,}")
    print("-" * 60)
    print(f" CONSO ÉLECTRIQUE      : {total_kwh:.4f} kWh")
    print(f" EMPREINTE CARBONE     : {total_co2:.2f} kgCO2e")
    print("-" * 60)

    # Export
    df.to_csv(output_file, index=False)
    print(f" Rapport détaillé exporté : {output_file}")

if __name__ == "__main__":
    main()