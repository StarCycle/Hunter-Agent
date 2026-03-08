from __future__ import annotations

from pathlib import Path

from hunter_agent.common.schemas import (
    SkillBExportOutput,
    SkillBFindOutput,
    SkillBInput,
    SkillBUpsertOutput,
    TalentBulkUpsertInput,
    TalentBulkUpsertOutput,
)
from hunter_agent.db.repo import TalentRepository
from hunter_agent.services.export_service import ExportService
from hunter_agent.services.talent_service import TalentService


def run_talent_database_sync(payload: dict, repo: TalentRepository) -> dict:
    input_obj = SkillBInput.model_validate(payload)
    service = TalentService(repo=repo)
    if input_obj.action == "find":
        assert input_obj.name is not None
        result = service.find_by_name(input_obj.name)
        return SkillBFindOutput(name=input_obj.name, matches=result).model_dump()
    if input_obj.action == "upsert":
        assert input_obj.profile is not None
        upserted = service.upsert(input_obj.profile)
        return SkillBUpsertOutput(profile=upserted).model_dump()

    output = Path(input_obj.out_csv) if input_obj.out_csv else Path("exports/talents.csv")
    path = ExportService(repo=repo).export_flat_csv(output)
    return SkillBExportOutput(output=str(path)).model_dump()


def run_talent_database_bulk_upsert(payload: dict, repo: TalentRepository) -> dict:
    input_obj = TalentBulkUpsertInput.model_validate(payload)
    service = TalentService(repo=repo)
    profiles = service.bulk_upsert(input_obj.profiles)
    return TalentBulkUpsertOutput(profiles=profiles).model_dump()
