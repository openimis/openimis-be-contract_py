from .models import Contract
from core.signals import Signal

_contract_signal_params = ["contract", "user"]
signal_contract = Signal(providing_args=_contract_signal_params)


def on_contract_signal(sender, **kwargs):
    contract = kwargs["contract"]
    user = kwargs["user"]
    contract.save(username=user.username)
    return "contract updated"


signal_contract.connect(on_contract_signal, dispatch_uid="on_contract_signal")
