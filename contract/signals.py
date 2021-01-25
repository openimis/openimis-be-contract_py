import json

from .models import Contract
from core.signals import Signal
from django.core.serializers.json import DjangoJSONEncoder

_contract_signal_params = ["contract", "user"]
signal_contract = Signal(providing_args=_contract_signal_params)


def on_contract_signal(sender, **kwargs):
    contract = kwargs["contract"]
    user = kwargs["user"]
    contract.save(username=user.username)
    historical_record = contract.history.all().first()
    contract.json_ext = json.dumps(__save_json_external(
        user_id=historical_record.user_updated.id,
        datetime=historical_record.date_updated,
        message=f"contract updated - state {historical_record.state}"
    ), cls=DjangoJSONEncoder)
    contract.save(username=user.username)
    return f"contract updated - state {contract.state}"


signal_contract.connect(on_contract_signal, dispatch_uid="on_contract_signal")


def __save_json_external(user_id, datetime, message):
    return {
        "comments": [{
            "From": "Portal/webapp",
            "user": user_id,
            "date": datetime,
            "msg": message
        }]
    }