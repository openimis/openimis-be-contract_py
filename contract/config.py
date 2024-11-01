CONTRACT_STATE = {
    "ContractState": [
        {
            "value": "1",
            "label": {"fr": "Demande d'information", "en": "Request for information"},
        },
        {"value": "2", "label": {"fr": "Brouillon", "en": "Draft"}},
        {"value": "3", "label": {"fr": "Offre", "en": "offer"}},
        {"value": "4", "label": {"fr": "En negociation", "en": "Negotiable"}},
        {"value": "5", "label": {"fr": "Apprové", "en": "executable"}},
        {"value": "6", "label": {"fr": "addendum", "en": "addendum"}},
        {"value": "7", "label": {"fr": "En cours", "en": "effective"}},
        {"value": "8", "label": {"fr": "Appliqué", "en": "executed"}},
        {"value": "9", "label": {"fr": "Suspendu", "en": "Disputed"}},
        {"value": "10", "label": {"fr": "Terminé", "en": "terminated"}},
        {"value": "11", "label": {"fr": "révision demandé", "en": "counter"}},
    ]
}


def get_message_approved_contract(
    code, name, contact_name, due_amount, payment_reference, language="en"
):
    message_payment_notification = {
        "payment_notification": {
            "en": f"""
                 Dear {contact_name}

                 The contract {code} - {name} was approved.
                 Please proceed to the payment of {due_amount} with the reference {payment_reference}.

                 Best regards,
                 """,
            "fr": f"""
                 Monsieur, Madame {contact_name}

                 le contract {code} - {name} à été apprové.
                 Veuillez faire un paiement de < CONTRACT - DUEAMOUNT > avec la référence {payment_reference}.

                 Meilleurs Salutations
                 """,
        }
    }
    return message_payment_notification["payment_notification"][language]


def get_message_counter_contract(code, name, contact_name, language="en"):
    message_payment_notification = {
        "payment_notification": {
            "en": f"""
                 Dear {contact_name}

                 The contract {code} - {name} was counter.
                 Please proceed recheck the information and correct the issues,
                 in case of questions please check contact us.

                 Best regards,
                 """,
            "fr": f"""
                 Monsieur, Madame {contact_name}

                 le contract {code} - {name} à été contré.
                 Veuillez verifier les information saisie, en cas de question veuillez nous contacter.

                 Meilleurs Salutations
                 """,
        }
    }
    return message_payment_notification["payment_notification"][language]
