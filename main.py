
from dotenv import load_dotenv
import os 
from mistralai import Mistral
import re

load_dotenv()

api_key_mistral = os.getenv("API_KEY_MISTRAL")

# Connexion au client
client = Mistral(api_key=api_key_mistral)

model_name = "mistral-small-latest"

def llm_inference(prompt: str) -> str:
    """
    Réalise une inférence via l'API Mistral AI.
    Plus de GPU, plus de torch, juste une requête web.
    """
    try:
        response = client.chat.complete(
            model="mistral-small-latest", # On utilise Devstral-Small via API
            messages=[
                # On envoie tout le prompt formaté comme un message utilisateur.
                # Le modèle est assez intelligent pour suivre les instructions internes.
                {"role": "user", "content": prompt} 
            ],
            temperature=0.1, # Faible température pour être rigoureux sur le format
            max_tokens=1000  # On limite la longueur de la réponse
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erreur API : {e}"
    

def ask_human(ask: str) -> str: 
    """Ask human to input a text.
    
    Parameters
    ----------
    ask: str
        The request asked to the user.
        
    Returns
    -------
    str
        The user answer.
    """
    return input(ask)

#Fonction pour permettre à l'agent de proposer à l'utilisateur de télécharger un document ou une photo
def upload(name: str) -> str:
    """Propose a user to upload a document/picture.

    Parameters
    ----------
    name: str
        The name/type of document expected.
        
    Returns
    -------
    str
        The name of the document.
    """
    # 1. On met le script en pause pour simuler la fenêtre d'upload
    input(f"\n[Agent IA attend un fichier] 📁 Veuillez charger : {name} \n>>> (Appuyez sur Entrée pour simuler l'envoi) ")
    
    # 2. ON RETOURNE UN TEXTE DE SUCCÈS À L'AGENT (Très important !)
    return f"Le document {name} a été uploadé avec succès."

tools = {
    "AskHuman": ask_human,
    "Upload": upload
}

#Cette fonction permet de formater le prompt envoyé au LLM.
def format_prompt(history: list[str]) -> str:
    """Template de prompt pour l'agent ReAct."""
    prompt = """
Tu es un agent IA spécialiste de la déclaration de sinistres pour une assurance habitation. Tu utilises des étapes de réflexion et action pour répondre à la demande des assurés concernant leur déclaration de sinistres. 

## Contexte

Afin de pouvoir répondre à l'assuré, tu trouveras ci-dessous les éléments de contexte spécifiques aux processus de la déclaration de sinistres, et les garanties de l'assuré.

--------

{processus}

--------

## Actions

Voici les actions disponibles.

{actions}

Voici quelques exemples de réflexions et d'actions.

## Exemple

### Entrée

Question: J'ai eu un sinistre hier.

### Sortie

Thought: J'ai besoin de connaître le type de sinistre.
Action: AskHuman
Arguments:
  ask=Quel type de sinistre avez-vous eu ?

## Exemple

### Entrée

Question: Il y a eu une tempête ce matin avec des grêlons, et ma baie vitré à été impactée (ci-joint la photo).

### Sortie

Thought: J'ai toute les informations concernant le processus "3. Bris de glace".
Answer: Suite du processus. 

## Règles

- Si tu ne trouves pas d'outil approprié, ne fournis pas d'action et donne simplement la réponse.
- Lorsque tu fournis des arguments, tu dois les définir sous la forme `nom_argument=valeur_argument`, avec une ligne par argument.
- Tu ne dois pas ré-écrire dans la sortie, ce qu'il y a en entrée.
- Tu dois juste afficher la sortie qui est censé être la suite du raisonnement entrée : tu ne dois avoir qu'une seule paire réflexion/action, ou directement la réponse.
- Tu dois supposer que nous sommes en 2026 si l'utilisateur n'indique pas d'année spécifique.
- Tu dois t'assurer que conformément au processus lié au sinistre, toutes les informations ont bien été récoltées de la part de l'utilisateur.
- Évite de ré-utiliser des éléments du processus dans tes raisonnements : ces derniers doivent être succincts.
- Tu ne dois fournir la réponse finale qu'une fois tous les attendus de l'assuré pour le type de sinistre actuel (date du sinistre, documents, détails, etc) ont bien été renseignés.
- Ne demande pas plusieurs informations en une seule fois, mais fait-le étapes par étapes.

## Inférence

Propose maintenant une nouvelle réflexion et une nouvelle action et/ou réponse pour l'historique suivant.

### Entrée

{history}

### Sortie

""".strip()
    actions = "\n\n".join([
        f"### Action `{t}`\n\n{tools[t].__doc__}"
        for t in tools
    ])
    return prompt.format(
        actions=actions,
        processus=open("./processus.md", "r").read(),
        history="\n".join([x.strip() for x in history])
    )


# permet de **parser** la réponse du LLM, notamment de récupérer correctement les arguments ou la réponse finale.
def parse_output(output: str) -> tuple[str, ...]:
    """Permet de traiter la sortie ReAct d'un LLM."""
    action_match = re.search(r"Action: (\w+)", output)
    arguments_match = re.search(r"Arguments:([\s\S]*)", output)
    answer_match = re.search(r"Answer: (.*)", output)

    if answer_match:
        return "answer", answer_match.group(1).strip()
    elif action_match:
        tool_name = action_match.group(1)
        tool_input = {}
        if arguments_match is not None:
            for arg in arguments_match.group(1).split("\n"):
                if len(arg.strip()) == 0:
                    continue
                
                # NOUVELLE REGEX : Accepte "ask=valeur" OU "ask: valeur"
                argument_re = re.search(r"^\s*(.*?)\s*[=:]\s*(.*)$", arg) 
                
                if argument_re is None or len(argument_re.groups()) != 2:
                    raise ValueError(f"Impossible to parse argument '{arg}' for action '{tool_name}'.")
                
                key = argument_re.group(1).strip()
                value = argument_re.group(2).strip()
                
                # Si le modèle a rajouté des guillemets autour de la phrase, on les enlève
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                    
                tool_input[key] = value
                
        return "action", tool_name, tool_input
    else:
        return "thought", output.strip()
    
# Agent ReAct : permet de créer la boucle réflexion/action de notre agent ReAct.
def react_agent(question: str, max_turns: int = 10):
    """Implémente un agent ReAct simple.
    
    Args:
        question (str): La question à poser à l'agent.
        max_turns (int, optional): Le nombre maximum de tours de réflexion/action. Par défaut 10.
        
    Returns:
        str: L'historique complet de l'agent, y compris la réponse finale.
    """
    history = [f"Question: {question}"]
    for i in range(max_turns):
        prompt = format_prompt(history)
        output = llm_inference(prompt)
        print("-" * 20)
        print(f"Étape {i+1}")
        print("-" * 20)
        print(output)
        step_type, *content = parse_output(output)
        if step_type == "action":
            tool_name, tool_input = content
            if tool_name in tools:
                history.append(f"Thought: Je vais utiliser l'outil {tool_name}.")
                if tool_input:
                    observation = tools[tool_name](**tool_input)
                    history.append(f"Action: {tool_name}[{tool_input}]")
                else:
                    observation = tools[tool_name]()
                    history.append(f"Action: {tool_name}")
                history.append(f"Observation: {observation}")
            else:
                history.append(f"Observation: Error - Unknown tool {tool_name}")
        elif step_type == "answer":
            history.append(f"Answer: {content[0]}")
            return "\n".join(history)
        else:
            history.append(f"Thought: {content[0]}")
    return "\n".join(history) + "\nAnswer: Could not reach a conclusion."


if __name__ == "__main__":
    # Point d'entrée du script
    result = "Je veux déclarer un sinistre."
    react_agent(result)
