from __future__ import annotations

from hunter_agent.common.schemas import SkillBFindOutput, SkillBInput, SkillBUpsertOutput
from hunter_agent.db.repo import TalentRepository
from hunter_agent.services.talent_service import TalentService


def run_talent_database_sync(payload: dict, repo: TalentRepository) -> dict:
    input_obj = SkillBInput.model_validate(payload)
    service = TalentService(repo=repo)
    if input_obj.action == "find":
        assert input_obj.name is not None
        result = service.find_by_name(input_obj.name)
        return SkillBFindOutput(name=input_obj.name, matches=result).model_dump()
    assert input_obj.profile is not None
    upserted = service.upsert(input_obj.profile)
    return SkillBUpsertOutput(profile=upserted).model_dump()
