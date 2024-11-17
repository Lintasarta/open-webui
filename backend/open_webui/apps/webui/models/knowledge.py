import json
import logging
import time
from typing import Optional
import uuid

from open_webui.apps.webui.internal.db import Base, get_db
from open_webui.env import SRC_LOG_LEVELS
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, JSON


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# Knowledge DB Schema
####################


class Knowledge(Base):
    __tablename__ = "knowledge"

    id = Column(Text, unique=True, primary_key=True)
    user_id = Column(Text)

    name = Column(Text)
    description = Column(Text)

    data = Column(JSON, nullable=True)
    meta = Column(JSON, nullable=True)

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class KnowledgeModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str

    name: str
    description: str

    data: Optional[dict] = None
    meta: Optional[dict] = None

    created_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch


####################
# Forms
####################


class KnowledgeResponse(BaseModel):
    id: str
    name: str
    description: str
    data: Optional[dict] = None
    meta: Optional[dict] = None
    created_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch


class KnowledgeForm(BaseModel):
    name: str
    description: str
    data: Optional[dict] = None


class KnowledgeUpdateForm(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    data: Optional[dict] = None


class KnowledgeTable:
    def insert_new_knowledge(
        self, user_id: str, form_data: KnowledgeForm
    ) -> Optional[KnowledgeModel]:
        with get_db() as db:
            knowledge = KnowledgeModel(
                **{
                    **form_data.model_dump(),
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                }
            )

            try:
                result = Knowledge(**knowledge.model_dump())
                db.add(result)
                db.commit()
                db.refresh(result)
                if result:
                    return KnowledgeModel.model_validate(result)
                else:
                    return None
            except Exception:
                return None

    def get_knowledge_items(self,user_info) -> list[KnowledgeModel]:
        with get_db() as db:
            if user_info.role=="admin":
                return [
                    KnowledgeModel.model_validate(knowledge)
                    for knowledge in db.query(Knowledge)
                    .order_by(Knowledge.updated_at.desc())
                    .all()
                ]
            else:
                return [
                    KnowledgeModel.model_validate(knowledge)
                    for knowledge in db.query(Knowledge)
                    .filter_by(user_id=user_info.id)
                    .order_by(Knowledge.updated_at.desc())
                    .all()
                ]                

    def get_knowledge_by_id(self, id: str,user_info) -> Optional[KnowledgeModel]:
        try:
            with get_db() as db:
                if user_info.role=="admin":
                    knowledge = db.query(Knowledge).filter_by(id=id).first()
                else:
                    knowledge = db.query(Knowledge).filter_by(id=id,user_id=user_info.id).first()
                return KnowledgeModel.model_validate(knowledge) if knowledge else None
        except Exception:
            return None

    def update_knowledge_by_id(
        self, id: str, user_info, form_data: KnowledgeUpdateForm, overwrite: bool = False, 
    ) -> Optional[KnowledgeModel]:
        try:
            with get_db() as db:
                knowledge = self.get_knowledge_by_id(id=id,user_info=user_info)
                db.query(Knowledge).filter_by(id=id).update(
                    {
                        **form_data.model_dump(exclude_none=True),
                        "updated_at": int(time.time()),
                    }
                )
                db.commit()
                return self.get_knowledge_by_id(id=id,user_info=user_info)
        except Exception as e:
            log.exception(e)
            return None

    def delete_knowledge_by_id(self, id: str) -> bool:
        try:
            with get_db() as db:
                db.query(Knowledge).filter_by(id=id).delete()
                db.commit()
                return True
        except Exception:
            return False


Knowledges = KnowledgeTable()
