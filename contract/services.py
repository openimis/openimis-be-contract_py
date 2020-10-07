import core


@core.comparable
class PolicyHolderContract(object):

    def __init__(self, policy_holder):
        self.policy_holder = policy_holder
        pass

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def submit(self, submit):
        pass

    def amend(self, submit):
        pass

    def create(self, contract):
        pass

    def update(self, contract):
        pass

    def delete(self, contract):
        pass


@core.comparable
class PolicyHolderContractDetails(object):

    def __init__(self, policy_holder):
        self.policy_holder = policy_holder
        pass

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__


@core.comparable
class Payment(object):

    def __init__(self, policy_holder):
        self.policy_holder = policy_holder
        pass

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def submit(self, payment):
        pass

    def create(self, payment):
        pass

    def update(self, payment):
        pass

    def delete(self, payment):
        pass

    def assign_credit_note(self, payment):
        pass
