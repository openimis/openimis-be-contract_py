from django.db.models import Q


def filter_amount_contract(arg='amount_from', arg2='amount_to', **kwargs):
    amount_from = kwargs.get(arg)
    amount_to = kwargs.get(arg2)

    # scenario - only amount_to set
    if not amount_from and amount_to:
        return (
             Q(amount_notified__lte=amount_to, state__in=[1, 2]) |
             Q(amount_rectified__lte=amount_to, state__in=[4, 11, 3, 1]) |
             Q(amount_due__lte=amount_to, state__in=[5, 6, 7, 8, 9, 10])
        )

    # scenario - only amount_from set
    if amount_from and not amount_to:
        return (
            Q(amount_notified__gte=amount_from, state__in=[1, 2]) |
            Q(amount_rectified__gte=amount_from, state__in=[4, 11, 3, 1]) |
            Q(amount_due__gte=amount_from, state__in=[5, 6, 7, 8, 9, 10])
        )

    # scenario - both filters set
    if amount_from and amount_to:
        return (
            Q(amount_notified__gte=amount_from, amount_notified__lte=amount_to, state__in=[1, 2]) |
            Q(amount_rectified__gte=amount_from, amount_rectified__lte=amount_to, state__in=[4, 11, 3, 1]) |
            Q(amount_due__gte=amount_from, amount_due__lte=amount_to, state__in=[5, 6, 7, 8, 9, 10])
        )
