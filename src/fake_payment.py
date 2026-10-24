"""
Faux système de paiement — terrain de jeu pour Agent Sentinelle.

Simule deux actions :
- Vérifier le solde d'un compte
- Envoyer un paiement à un numéro

Pas de vrai argent. Tout se passe en local.
"""

import json
import http.server
import socketserver
from datetime import datetime

PORT = 5000

# Comptes simulés
ACCOUNTS = {
    "0700000001": {"name": "Koné Aya", "balance": 50000},
    "0700000002": {"name": "Traoré Moussa", "balance": 30000},
    "0700000003": {"name": "Bamba Fatou", "balance": 100000},
}

# Destinataires autorisés (liste blanche)
AUTHORIZED_RECIPIENTS = ["0700000001", "0700000002", "0700000003"]

# Journal des transactions
TRANSACTIONS = []


class PaymentHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {"error": "JSON invalide"})
            return

        action = data.get("action")

        if action == "check_balance":
            self._check_balance(data)
        elif action == "send_payment":
            self._send_payment(data)
        else:
            self._respond(400, {"error": f"Action inconnue : {action}"})

    def _check_balance(self, data):
        account = data.get("account")
        if account not in ACCOUNTS:
            self._respond(404, {"error": "Compte introuvable"})
            return
        self._respond(200, {
            "account": account,
            "name": ACCOUNTS[account]["name"],
            "balance": ACCOUNTS[account]["balance"],
        })

    def _send_payment(self, data):
        sender = data.get("sender")
        recipient = data.get("recipient")
        amount = data.get("amount")

        if sender not in ACCOUNTS:
            self._respond(404, {"error": "Compte expéditeur introuvable"})
            return
        if recipient not in ACCOUNTS:
            self._respond(404, {"error": "Compte destinataire introuvable"})
            return
        if not isinstance(amount, (int, float)) or amount <= 0:
            self._respond(400, {"error": "Montant invalide"})
            return
        if ACCOUNTS[sender]["balance"] < amount:
            self._respond(400, {"error": "Solde insuffisant"})
            return

        # Exécuter le paiement
        ACCOUNTS[sender]["balance"] -= amount
        ACCOUNTS[recipient]["balance"] += amount

        tx = {
            "timestamp": datetime.now().isoformat(),
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
            "status": "success",
        }
        TRANSACTIONS.append(tx)

        self._respond(200, {
            "status": "success",
            "message": f"Paiement de {amount} FCFA envoyé à {ACCOUNTS[recipient]['name']}",
            "transaction": tx,
        })

    def _respond(self, status_code, body):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body, ensure_ascii=False).encode())

    def log_message(self, format, *args):
        pass  # Silence les logs HTTP


def start_server():
    with socketserver.TCPServer(("", PORT), PaymentHandler) as httpd:
        print(f"[FAKE PAYMENT] Serveur démarré sur http://localhost:{PORT}")
        print(f"[FAKE PAYMENT] Comptes disponibles : {list(ACCOUNTS.keys())}")
        print(f"[FAKE PAYMENT] Ctrl+C pour arrêter")
        httpd.serve_forever()


if __name__ == "__main__":
    start_server()
