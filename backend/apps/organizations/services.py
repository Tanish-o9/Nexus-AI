from django.utils.text import slugify
from .models import Organization, Membership


def create_organization(name: str, created_by) -> Organization:
    slug = _unique_slug(name)
    org = Organization.objects.create(name=name, slug=slug, created_by=created_by)
    Membership.objects.create(
        user=created_by, organization=org, role=Membership.Role.OWNER
    )
    return org


def _unique_slug(name: str) -> str:
    base = slugify(name)
    slug, counter = base, 1
    while Organization.objects.filter(slug=slug).exists():
        slug = f'{base}-{counter}'
        counter += 1
    return slug
