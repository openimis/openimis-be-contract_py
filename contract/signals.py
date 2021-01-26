import json

from .models import Contract
from core.signals import Signal
from django.core.serializers.json import DjangoJSONEncoder

_contract_signal_params = ["contract", "user"]
_contract_approve_signal_params = ["contract", "user", "contract_details_list", "service_object", "payment_service"]
signal_contract = Signal(providing_args=_contract_signal_params)
signal_contract_approve = Signal(providing_args=_contract_signal_params)


def on_contract_signal(sender, **kwargs):
    contract = kwargs["contract"]
    user = kwargs["user"]
    __save_or_update_contract(contract=contract, user=user)
    return f"contract updated - state {contract.state}"


def on_contract_approve_signal(sender, **kwargs):
    # approve scenario
    user = kwargs["user"]
    contract_to_approve = kwargs["contract"]
    contract_details_list = kwargs["contract_details_list"]
    contract_service = kwargs["service_object"]
    payment_service = kwargs["payment_service"]
    # contract valuation
    contract_contribution_plan_details = contract_service.evaluate_contract_valuation(
        contract_details_result=contract_details_list,
        save=True
    )
    contract_to_approve.amount_rectified = contract_contribution_plan_details["total_amount"]
    from core import datetime
    now = datetime.datetime.now()
    # format payment data
    payment_data = {
        "expected_amount": contract_to_approve.amount_rectified,
        "request_date": now,
    }
    payment_details_data = payment_service.collect_payment_details(contract_contribution_plan_details["contribution_plan_details"])
    result_payment = payment_service.create(payment=payment_data, payment_details=payment_details_data)
    # STATE_EXECUTABLE
    contract_to_approve.state = 5
    contract_to_approve.json_ext = json.dumps(
        {"payment_uuid": result_payment["data"]["uuid"]},
        cls=DjangoJSONEncoder
    )
    approved_contract = __save_or_update_contract(contract=contract_to_approve, user=user)
    print(approved_contract)
    return approved_contract


signal_contract.connect(on_contract_signal, dispatch_uid="on_contract_signal")
signal_contract_approve.connect(on_contract_approve_signal, dispatch_uid="on_contract_approve_signal")


def __save_json_external(user_id, datetime, message):
    return {
        "comments": [{
            "From": "Portal/webapp",
            "user": user_id,
            "date": datetime,
            "msg": message
        }]
    }


def __save_or_update_contract(contract, user):
    contract.save(username=user.username)
    historical_record = contract.history.all().first()
    contract.json_ext = json.dumps(__save_json_external(
        user_id=historical_record.user_updated.id,
        datetime=historical_record.date_updated,
        message=f"contract updated - state {historical_record.state}"
    ), cls=DjangoJSONEncoder)
    print("saved")
    contract.save(username=user.username)
    return contract


#def __create_paymen(contract)