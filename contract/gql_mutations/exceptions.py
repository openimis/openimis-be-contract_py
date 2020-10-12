
class ContractNotExistException(Exception):

    def __init__(self, contract_uuid):
        self.contract_uuid = contract_uuid
        self.message = 'Contract with uuid {} does not exist'.format(self.contract_uuid)
        super().__init__(self.message)


class ContractValidationException(Exception):

    def __init__(self, contract, *invalidation_reasons):
        self.contract = contract
        self.errors = invalidation_reasons
        self.message = self._build_error_msg()
        super().__init__(self.message)

    def _build_error_msg(self):
        msg = ",\n".join(self.errors)
        return "Validation for contract with uuid {uuid} failed, reasons:\n" \
               "{msg}".format(uuid=self.contract['uuid'], msg=msg)
