class InvitationError(Exception):
    pass


class InvitationExpired(InvitationError):
    pass


class InvitationAlreadyAccepted(InvitationError):
    pass


class InvitationEmailMismatch(InvitationError):
    pass
