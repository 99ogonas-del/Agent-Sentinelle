"""
Garde-fou Sentinelle — le cœur du projet.

Ce module intercepte chaque demande de l'agent IA avant qu'elle ne parte
vers le système de paiement. Il applique 3 règles :

1. Montant maximum : si le montant dépasse 10 000 FCFA → bloqué
2. Liste blanche : si le destinataire n'est pas autorisé → bloqué
3. Journal obligatoire : si on ne peut pas écrire le journal → bloqué par défaut

Principe : "pas de trace, pas d'action" (fail-closed).
"""

import json
import os
from datetime import datetime

# ---------- Configuration ----------
MONTANT_MAX = 10000  # FCFA — au-delà, confirmation humaine requise
DESTINATAIRES_AUTORISES = ["0700000001", "0700000002", "0700000003"]
JOURNAL_PATH = os.path.join(os.path.dirname(__file__), "..", "reports", "journal_audit.log")


class GardeFou:
    """Garde-fou qui s'intercale entre l'agent IA et le système de paiement."""

    def __init__(self, montant_max=MONTANT_MAX, destinataires=None, journal_path=JOURNAL_PATH):
        self.montant_max = montant_max
        self.destinataires = destinataires or DESTINATAIRES_AUTORISES
        self.journal_path = journal_path
        self._ensure_journal_dir()

    def _ensure_journal_dir(self):
        """Crée le dossier reports/ s'il n'existe pas."""
        os.makedirs(os.path.dirname(self.journal_path), exist_ok=True)

    def _write_journal(self, entry):
        """
        Écrit une entrée dans le journal d'audit.
        Retourne True si l'écriture réussit, False sinon.
        Principe : si on ne peut pas écrire → on bloque (fail-closed).
        """
        try:
            with open(self.journal_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return True
        except (IOError, OSError, PermissionError):
            return False

    def verifier(self, action, sender=None, recipient=None, amount=None, account=None):
        """
        Vérifie si une action est autorisée.

        Retourne un dict :
        - {"autorise": True, "raison": "..."} si l'action est OK
        - {"autorise": False, "raison": "..."} si l'action est bloquée

        Les règles sont appliquées dans l'ordre :
        1. Règle 1 — Montant maximum
        2. Règle 2 — Liste blanche
        3. Règle 3 — Journal obligatoire
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
            "account": account,
        }

        # Règle 1 — Montant maximum
        if action == "send_payment" and amount is not None:
            if amount > self.montant_max:
                entry["decision"] = "BLOQUE"
                entry["raison"] = f"Montant {amount} FCFA dépasse le maximum autorisé ({self.montant_max} FCFA)"
                self._write_journal(entry)
                return {
                    "autorise": False,
                    "raison": f"Montant {amount} FCFA dépasse le maximum autorisé ({self.montant_max} FCFA). Confirmation humaine requise.",
                }

        # Règle 2 — Liste blanche
        if action == "send_payment" and recipient is not None:
            if recipient not in self.destinataires:
                entry["decision"] = "BLOQUE"
                entry["raison"] = f"Destinataire {recipient} non autorisé"
                self._write_journal(entry)
                return {
                    "autorise": False,
                    "raison": f"Destinataire {recipient} non autorisé. Liste blanche : {self.destinataires}",
                }

        # Règle 3 — Journal obligatoire (fail-closed)
        entry["decision"] = "AUTORISE"
        entry["raison"] = "Toutes les règles passées"
        if not self._write_journal(entry):
            return {
                "autorise": False,
                "raison": "Impossible d'écrire le journal d'audit. Action bloquée par défaut (fail-closed).",
            }

        return {"autorise": True, "raison": "Toutes les règles passées"}


def demo():
    """Démonstration rapide du garde-fou."""
    gf = GardeFou()

    print("=== Test 1 : Montant dans la limite ===")
    r = gf.verifier("send_payment", sender="0700000001", recipient="0700000002", amount=5000)
    print(f"  Résultat : {r}")

    print("\n=== Test 2 : Montant trop élevé ===")
    r = gf.verifier("send_payment", sender="0700000001", recipient="0700000002", amount=50000)
    print(f"  Résultat : {r}")

    print("\n=== Test 3 : Destinataire non autorisé ===")
    r = gf.verifier("send_payment", sender="0700000001", recipient="0799999999", amount=5000)
    print(f"  Résultat : {r}")

    print("\n=== Test 4 : Tout est OK ===")
    r = gf.verifier("send_payment", sender="0700000001", recipient="0700000002", amount=8000)
    print(f"  Résultat : {r}")

    print(f"\nJournal écrit dans : {gf.journal_path}")


if __name__ == "__main__":
    demo()
