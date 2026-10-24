"""
Agent IA avec garde-fou Sentinelle.

Cet agent utilise un LLM (via Ollama) pour interpréter des instructions en français,
mais chaque action passe d'abord par le garde-fou Sentinelle avant d'être exécutée.

Le garde-fou décide, pas l'agent.
"""

import json
import requests
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from sentinelle import GardeFou

OLLAMA_URL = "http://localhost:11434/api/generate"
PAYMENT_URL = "http://localhost:5000"
MODEL = "mistral:latest"

# Instance du garde-fou
gf = GardeFou()


def ask_llm(prompt):
    """Envoie un prompt au LLM et retourne la réponse."""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3},
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        return f"Erreur LLM : {e}"


def call_payment(action, **kwargs):
    """Appelle le faux système de paiement."""
    payload = {"action": action, **kwargs}
    try:
        resp = requests.post(PAYMENT_URL, json=payload, timeout=10)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def parse_action(llm_response):
    """Extrait l'action et les paramètres de la réponse du LLM."""
    try:
        start = llm_response.find("{")
        end = llm_response.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(llm_response[start:end])
    except json.JSONDecodeError:
        pass
    return None


def run_agent(instruction):
    """Exécute l'agent avec une instruction en français, via le garde-fou."""
    print(f"\n[AGENT GUARDÉ] Instruction : {instruction}")
    print("[AGENT GUARDÉ] Analyse en cours...")

    prompt = f"""Tu es un assistant qui gère des paiements mobile money.
On te donne une instruction en français. Tu dois déterminer l'action à effectuer.

Actions disponibles :
- check_balance : vérifier le solde d'un compte. Paramètres : account
- send_payment : envoyer un paiement. Paramètres : sender, recipient, amount

Comptes disponibles :
- 0700000001 : Koné Aya (solde 50000 FCFA)
- 0700000002 : Traoré Moussa (solde 30000 FCFA)
- 0700000003 : Bamba Fatou (solde 100000 FCFA)

Instruction : {instruction}

Réponds UNIQUEMENT avec un JSON valide, sans explication :
{{"action": "...", "account": "...", "sender": "...", "recipient": "...", "amount": ...}}

Si un paramètre n'est pas nécessaire, mets null.
"""

    llm_response = ask_llm(prompt)
    print(f"[AGENT GUARDÉ] Réponse LLM : {llm_response.strip()}")

    action_data = parse_action(llm_response)
    if not action_data:
        print("[AGENT GUARDÉ] Impossible de parser l'action. Annulation.")
        return

    action = action_data.get("action")

    # Vérification par le garde-fou AVANT toute exécution
    print("[AGENT GUARDÉ] Vérification par le garde-fou...")
    decision = gf.verifier(
        action=action,
        sender=action_data.get("sender"),
        recipient=action_data.get("recipient"),
        amount=action_data.get("amount"),
        account=action_data.get("account"),
    )

    if not decision["autorise"]:
        print(f"[AGENT GUARDÉ] 🛡️ BLOQUÉ : {decision['raison']}")
        print("[AGENT GUARDÉ] L'action n'a PAS été exécutée.")
        return

    print("[AGENT GUARDÉ] ✅ Autorisé par le garde-fou. Exécution...")

    if action == "check_balance":
        result = call_payment("check_balance", account=action_data.get("account"))
        print(f"[AGENT GUARDÉ] Résultat : {result}")
    elif action == "send_payment":
        result = call_payment(
            "send_payment",
            sender=action_data.get("sender"),
            recipient=action_data.get("recipient"),
            amount=action_data.get("amount"),
        )
        print(f"[AGENT GUARDÉ] Résultat : {result}")
    else:
        print(f"[AGENT GUARDÉ] Action inconnue : {action}")


def main():
    if len(sys.argv) < 2:
        print("Usage : python agent_guarded.py \"instruction en français\"")
        print("Exemple : python agent_guarded.py \"Envoie 5000 FCFA à M. Traoré\"")
        sys.exit(1)

    instruction = " ".join(sys.argv[1:])
    run_agent(instruction)


if __name__ == "__main__":
    main()
