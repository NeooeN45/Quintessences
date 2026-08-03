"""Contrat SQLAlchemy des tables d'identité isolées."""

from gsie_api.infrastructure.models.accounts import (
    AccountRoleModel,
    IdentityProviderLinkModel,
    LocalCredentialModel,
    UserAccountModel,
)


def should_keep_all_identity_tables_in_rgpd_identity_schema() -> None:
    models = (
        UserAccountModel,
        IdentityProviderLinkModel,
        LocalCredentialModel,
        AccountRoleModel,
    )

    assert {model.__table__.schema for model in models} == {"gsie_rgpd_identites"}


def should_define_unique_provider_issuer_subject_constraint() -> None:
    constraint_names = {
        constraint.name for constraint in IdentityProviderLinkModel.__table__.constraints
    }

    assert "uq_identity_provider_link_provider_issuer_subject" in constraint_names
