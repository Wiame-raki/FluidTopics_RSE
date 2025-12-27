
#  Fluid Topics - Mesure d'Impact Carbone IA & Traduction

Ce projet vise à modéliser, simuler et mesurer l'empreinte énergétique et carbone des services d'Intelligence Artificielle (GenAI) et de Traduction Automatique (NMT) orchestrés par la plateforme Fluid Topics.

Dans une architecture distribuée de type **"Black Box"** (où les calculs sont effectués par des tiers comme OpenAI ou DeepL), ce code propose une méthodologie d'estimation basée sur des **proxies de consommation** et des **simulations volumétriques**.


##  Objectifs du Projet

1. **Simuler les volumes de données :** Convertir des logs d'usage (nombre d'appels API) en métriques physiques (tokens, caractères) en fonction des profils utilisateurs (Chatbot vs Traduction).
2. **Estimer l'énergie (kWh) :** Appliquer des coefficients issus de l'état de l'art (2025) pour distinguer la consommation statique (latence) de la consommation dynamique (génération).
3. **Calculer l'impact carbone () :** Convertir l'énergie en émissions selon l'intensité carbone du mix électrique.


## 📂 Structure du Projet

```text
FluidTopics_RSE/
│
├── data/
│   └── 2025-FluidTopics-daily-analytics.yaml  # Fichier source (Logs d'usage)
│
├── output/
│   └── rapport_carbone_simule.csv             # Résultat généré par le script
│
├── measure_simulation.py                      # Script principal de calcul 
│
├── requirements.txt                           # Liste des dépendances Python
└── README.md                                  # Documentation du projet

```


## ⚙️ Installation

### Pré-requis

* Python 3.8 ou supérieur
* Pip (gestionnaire de paquets)

### Installation des dépendances

Exécutez la commande suivante pour installer les librairies nécessaires (`pandas`, `pyyaml`) :

```bash
pip install pandas pyyaml

```



## 🚀 Utilisation

1. Placez votre fichier de logs brut dans le dossier `data/` (par défaut : `2025-FluidTopics-daily-analytics.yaml`).
2. Lancez le script de simulation :

```bash
python measure_simulation.py

```

3. Le script affichera un résumé dans la console et générera le fichier détaillé `output/rapport_carbone_simule.csv`.

---

##  Méthodologie et Hypothèses

Ce projet repose sur une simulation déterministe. Les volumes de données ne sont pas mesurés en temps réel (données non disponibles dans les logs actuels) mais **reconstitués** selon des règles métier.

### 1. Paramètres de Simulation (`SIMULATION_PARAMS`)

Ces constantes sont définies dans le script `measure_simulation.py` et peuvent être ajustées pour créer des scénarios (ex: Scénario "Documentation Lourde").

| Paramètre | Valeur par défaut | Description |
| --- | --- | --- |
| `TOPIC_SIZE_CHARS` | 3000 | Taille moyenne d'un topic documentaire (en caractères). |
| `PROMPT_SIZE_CHARS` | 500 | Taille moyenne du prompt utilisateur. |
| `OUTPUT_SIZE_CHARS` | 350 | Taille moyenne de la réponse générée par l'IA. |
| `CHATBOT_CONTEXT` | 3 | Nombre moyen de topics injectés dans le contexte du Chatbot. |

### 2. Règles de Calcul Volumétrique

* **Profil Chatbot :**
* 
* 


* **Profil Completion :**
* 
* 


* **Profil Traduction :**
* 
*  (Ratio 1:1)



### 3. Modèle Énergétique (État de l'Art 2025)

* **Pour les LLM (GenAI) :** Utilisation d'un modèle hybride combinant coût par token et coût temporel (latence).


* **Pour la NMT (Traduction) :** Modèle linéaire basé sur les caractères.



---

## 📊 Interprétation des Résultats

Le fichier de sortie (`rapport_carbone_simule.csv`) contient les colonnes suivantes :

* `date` : Jour de l'analyse.
* `profile_type` : Type d'usage (chatbots, translations, completions).
* `count` : Nombre d'appels API réels (source YAML).
* `simulated_tokens` : Volume de tokens estimé par la simulation.
* `energy_kwh` : Consommation électrique totale estimée (incluant PUE 1.2).
* `carbon_gCO2` : Impact carbone basé sur un mix global (475 gCO2/kWh).




## 📝 Licence

Ce projet est réalisé dans un cadre académique en partenariat avec Fluid Topics. Usage interne réservé.