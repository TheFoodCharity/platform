from django import forms, template

register = template.Library()

# DaisyUI class strings keyed by lowercased widget class name.
_WIDGET_CLASSES: dict[str, str] = {
    "textinput": "input w-full aria-invalid:input-error",
    "emailinput": "input w-full aria-invalid:input-error",
    "urlinput": "input w-full aria-invalid:input-error",
    "passwordinput": "input w-full aria-invalid:input-error",
    "numberinput": "input w-full aria-invalid:input-error",
    "dateinput": "input w-full aria-invalid:input-error",
    "datetimeinput": "input w-full aria-invalid:input-error",
    "timeinput": "input w-full aria-invalid:input-error",
    "textarea": "textarea w-full resize-y aria-invalid:textarea-error",
    "checkboxinput": "checkbox aria-invalid:checkbox-error",
    "select": "select w-full aria-invalid:select-error",
    "selectmultiple": "select w-full aria-invalid:select-error",
    "nullbooleanselect": "select w-full aria-invalid:select-error",
}

# Fallback: check if a widget inherits from one of these base types.
_FALLBACK_BASES: list[tuple[type, str]] = [
    (forms.TextInput, "input w-full aria-invalid:input-error"),
    (forms.Textarea, "textarea w-full resize-y aria-invalid:textarea-error"),
    (forms.Select, "select w-full aria-invalid:select-error"),
    (forms.CheckboxInput, "checkbox aria-invalid:checkbox-error"),
]


def _daisyui_class(widget: forms.Widget) -> str:
    name = widget.__class__.__name__.lower()
    if name in _WIDGET_CLASSES:
        return _WIDGET_CLASSES[name]
    for base, css in _FALLBACK_BASES:
        if isinstance(widget, base):
            return css
    return ""


class ThemedFieldNode(template.Node):
    def __init__(self, field_var: str) -> None:
        self.field_var = template.Variable(field_var)

    def render(self, context: template.Context) -> str:
        field = self.field_var.resolve(context)
        # Handle MultiWidget by iterating sub-widgets; otherwise treat as single.
        widgets = getattr(field.field.widget, "widgets", None)
        if widgets:
            for widget in widgets:
                _inject(widget)
        else:
            _inject(field.field.widget)
        return str(field)


def _inject(widget: forms.Widget) -> None:
    css = _daisyui_class(widget)
    if not css:
        return
    existing = widget.attrs.get("class", "")
    widget.attrs["class"] = f"{existing} {css}".strip() if existing else css


@register.tag(name="themed_field")
def themed_field(parser: template.base.Parser, token: template.base.Token) -> ThemedFieldNode:
    parts = token.split_contents()
    if len(parts) != 2:
        raise template.TemplateSyntaxError(f"'{parts[0]}' tag requires exactly one argument")
    return ThemedFieldNode(parts[1])


@register.filter
def is_checkbox(field: forms.BoundField) -> bool:
    return isinstance(field.field.widget, forms.CheckboxInput)
