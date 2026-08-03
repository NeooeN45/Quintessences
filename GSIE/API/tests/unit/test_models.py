"""Tests unitaires — modèles SQLAlchemy (infrastructure/models.py)."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from gsie_api.infrastructure.models import Base, TimestampMixin


def should_be_declarative_base_when_imported():
    """Base doit être une sous-classe de DeclarativeBase."""
    from sqlalchemy.orm import DeclarativeBase

    assert issubclass(Base, DeclarativeBase)


def should_have_created_at_when_timestamp_mixin_used():
    """TimestampMixin doit définir created_at avec timezone."""
    assert "created_at" in TimestampMixin.__dict__ or "created_at" in dir(TimestampMixin)


def should_have_updated_at_when_timestamp_mixin_used():
    """TimestampMixin doit définir updated_at avec timezone."""
    assert "updated_at" in TimestampMixin.__dict__ or "updated_at" in dir(TimestampMixin)


def should_create_model_with_timestamps_when_mixin_applied():
    """Un modèle utilisant TimestampMixin doit avoir created_at et updated_at.

    Note : on utilise une DeclarativeBase locale (pas le Base partagé du
    projet) pour ne pas enregistrer `test_model` dans Base.metadata — sinon
    alembic command.check() dans test_migration_baseline.py détecte une
    table non migrée et échoue (pollution de metadata entre tests).
    """
    from sqlalchemy.orm import DeclarativeBase

    class LocalBase(DeclarativeBase):
        """Base déclarative jetable, isolée du Base du projet."""

    class TestModel(TimestampMixin, LocalBase):
        __tablename__ = "test_model"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(100))

    # Vérifier que les colonnes sont présentes dans le modèle
    columns = {c.name for c in TestModel.__table__.columns}
    assert "id" in columns
    assert "name" in columns
    assert "created_at" in columns
    assert "updated_at" in columns

    # Vérifier que created_at a un server_default
    created_at_col = TestModel.__table__.c.created_at
    assert created_at_col.server_default is not None

    # Vérifier que updated_at a onupdate
    updated_at_col = TestModel.__table__.c.updated_at
    assert updated_at_col.onupdate is not None


# --- Garde : les schémas de domaine doivent rester qualifiés sur __table_args__
#
# Sans `__table_args__ = {"schema": "gsie_<domaine>"}`, la table retombe dans
# `public` pour le registre SQLAlchemy — invisible au `git diff` tant qu'on ne
# le cherche pas. Ces tests tuent les mutations `schema_*_retire`.


def should_keep_botanique_schema_on_trait_definition_when_loaded():
    """TraitDefinitionModel doit rester dans le schéma gsie_botanique."""
    from gsie_api.infrastructure.models.ecology import TraitDefinitionModel

    assert TraitDefinitionModel.__table_args__.get("schema") == "gsie_botanique"


def should_keep_foret_schema_on_management_plan_when_loaded():
    """ManagementPlanModel doit rester dans le schéma gsie_foret."""
    from gsie_api.infrastructure.models.business import ManagementPlanModel

    assert ManagementPlanModel.__table_args__.get("schema") == "gsie_foret"


def should_keep_gouvernance_schema_on_regulation_when_loaded():
    """RegulationModel doit rester dans le schéma gsie_gouvernance."""
    from gsie_api.infrastructure.models.business import RegulationModel

    assert RegulationModel.__table_args__.get("schema") == "gsie_gouvernance"


# --- Garde : le mécanisme de reversion du pseudonymat doit être isolé des
# consentements (RGPD art. 32). `data_subject` porte pseudonyme + courriel
# chiffré : la placer dans `gsie_rgpd` (au lieu de `gsie_rgpd_identites`)
# donnerait au gestionnaire des consentements le pouvoir de lever le
# pseudonymat — les deux pouvoirs se cumulent au lieu de rester distincts.


def should_keep_rgpd_identites_schema_on_data_subject_when_loaded():
    """DataSubjectModel doit rester dans gsie_rgpd_identites, pas gsie_rgpd."""
    from gsie_api.infrastructure.models.fair_rgpd import DataSubjectModel

    assert DataSubjectModel.__table_args__.get("schema") == "gsie_rgpd_identites"


def should_keep_rgpd_schema_on_rights_statement_when_loaded():
    """RightsStatementModel doit rester dans gsie_rgpd, pas dans public."""
    from gsie_api.infrastructure.models.governance import RightsStatementModel

    assert RightsStatementModel.__table_args__.get("schema") == "gsie_rgpd"


# --- Garde : les FK intra-domaine doivent être qualifiées avec le schéma.
# Une référence nue `"site_index_model.id"` ne trouve plus sa table quand
# elle a changé de schéma — NoReferencedTableError au chargement du registre.


def should_qualify_intra_foret_fk_with_schema_when_loaded():
    """FertilityClassModel.site_index_model_id doit pointer vers gsie_foret."""
    from gsie_api.infrastructure.models.forestry import FertilityClassModel

    fk = FertilityClassModel.__table__.c.site_index_model_id.foreign_keys
    assert len(fk) == 1
    target = list(fk)[0].column.table
    assert target.schema == "gsie_foret"
    assert target.name == "site_index_model"


# --- Garde : le comment SQL de human_validator doit rester en base.
# `doc=` est de la documentation Python : PostgreSQL ne la voit pas. La
# contrainte métier — human_validator obligatoire dès que status passe à
# accepted — n'existe plus que dans le code Python si le comment disparaît.


def should_have_column_comment_on_human_validator_when_loaded():
    """SilviculturalRuleModel.human_validator doit porter un comment PostgreSQL."""
    from gsie_api.infrastructure.models.forestry import SilviculturalRuleModel

    col = SilviculturalRuleModel.__table__.c.human_validator
    assert col.comment is not None, (
        "human_validator doit porter un comment PostgreSQL — sans lui, "
        "la contrainte métier n'existe plus que dans le code Python"
    )
