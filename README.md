# Agent Sentinelle

Garde-fou open source pour les agents IA qui touchent au mobile money.

## Problème

Les agents IA sont déployés partout, y compris sur les systèmes de paiement mobile money. Mais les frameworks actuels (LangChain, CrewAI, etc.) sont pensés pour des contextes américains ou européens. Ils ne connaissent pas les réalités du mobile money (plafonds de transaction, validation humaine, journalisation pour audit).

**Résultat :** une entreprise ivoirienne qui branche un agent IA sur son système de paiement n'a aucun garde-fou adapté. C'est comme mettre un apprenti au volant d'un camion sans frein.

## Solution

Agent Sentinelle est un **garde-fou** (pare-feu) qui s'intercale entre l'agent IA et le système de paiement. Chaque fois que l'agent veut faire une action (envoyer de l'argent), il doit **d'abord passer par le garde-fou**, qui vérifie :

1. **Le montant** : est-ce raisonnable ? Si c'est plus de 10 000 FCFA, on bloque et on demande une confirmation humaine.
2. **Le destinataire** : est-il dans la liste des personnes autorisées ? Si non, on bloque.
3. **La trace** : est-ce qu'on a bien noté quelque part qui a demandé quoi, quand, et combien ? Si on ne peut pas écrire cette trace, on **bloque par défaut**.

## Flux

```
Utilisateur → Agent IA → 🛡️ Sentinelle (garde-fou) → Système de paiement
                              ↓
                        Journal d'audit
```

## Prérequis

- Python 3.10+
- [Ollama](https://ollama.com) installé (pour l'agent IA)
- Modèle `mistral:latest` téléchargé (`ollama pull mistral:latest`)

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

```bash
# Phase 2 : Lancer le faux système de paiement
python src/fake_payment.py

# Phase 3 : Lancer l'agent IA (sans garde-fou)
python src/agent.py

# Phase 4 : Lancer l'agent avec le garde-fou
python src/agent_guarded.py

# Phase 5 : Lancer les tests scénarios pièges
python tests/test_scenarios.py
```

## Structure

```
Agent_Sentinelle/
├── src/
│   ├── fake_payment.py      # Faux système de paiement (terrain de jeu)
│   ├── agent.py             # Agent IA sans garde-fou (danger démontré)
│   ├── sentinelle.py        # Garde-fou (cœur du projet)
│   └── agent_guarded.py     # Agent avec garde-fou
├── tests/
│   └── test_scenarios.py    # Scénarios pièges (preuve visuelle)
├── docs/
│   └── carnet_demo.md       # Carnet de démonstration
├── reports/
│   └── journal_audit.log    # Journal d'audit (généré)
├── information_projet.txt   # Description du projet
├── README.md
├── requirements.txt
└── .gitignore
```

## Méthodologie

1. **Faux système de paiement** : simule solde + envoi paiement (pas de vrai argent)
2. **Agent IA sans garde-fou** : démontre le danger (envoie 50 000 FCFA sans problème)
3. **Garde-fou Sentinelle** : 3 règles (montant max, liste blanche, journal obligatoire)
4. **Branchement** : agent passe par le garde-fou
5. **Tests scénarios pièges** : preuve que l'agent ne peut pas contourner les règles
6. **Publication** : GitHub + post LinkedIn

## Carnet de démonstration

Voir `docs/carnet_demo.md` pour les 5 scénarios pièges avec preuves visuelles :

1. Danger sans garde-fou (envoi de 50 000 FCFA sans vérification)
2. Envoi dans la limite (autorise + exécute)
3. Envoi au-dessus de la limite (bloqué)
4. Destinataire non autorisé (bloqué)
5. Tentative de contournement par injection (bloqué)

## Auteur

OgonasSec — Étudiant en Réseau et Sécurité Informatique (UVCI, Côte d'Ivoire)

## Licence

MIT
