from django.utils.safestring import mark_safe
from django import template

register = template.Library()

@register.simple_tag
def criterio_avaliado(solicitacao, criterio):
    criterio_avaliado = solicitacao.criterioavaliado_set.filter(criterio=criterio).first()
    checked = 'checked' if criterio_avaliado and criterio_avaliado.confere else ''
    return mark_safe(f'<input type="checkbox" name="criterio" value="{criterio.pk}" {checked} /> {criterio}')
