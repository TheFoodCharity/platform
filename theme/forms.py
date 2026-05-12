from typing import ClassVar

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout


class ThemedFormHelper(FormHelper):
    form_tag = False


class ThemedFormMixin:
    """Attach a ThemedFormHelper so {% crispy form %} renders fields only (no <form> tag).
    Forms that need a custom Layout() should assign self.helper.layout in their __init__."""

    layout: ClassVar[Layout | None] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = ThemedFormHelper(self)
        if self.layout is not None:
            self.helper.layout = self.layout
