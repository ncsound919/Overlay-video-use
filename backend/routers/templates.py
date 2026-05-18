from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Template, User
from schemas import TemplateCreate, TemplateResponse
from services.template_service import get_default_templates
from auth import get_current_user

router = APIRouter()


@router.get("/", response_model=list[TemplateResponse])
def list_templates(category: str = "", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Template)
    if category:
        query = query.filter(Template.category == category)
    templates = query.all()
    defaults = get_default_templates()
    result = []
    for key, val in defaults.items():
        if not category or val["category"] == category:
            result.append(TemplateResponse(id=0, name=val["name"], description=val["description"],
                          category=val["category"], config=val["config"], created_at=None))
    result.extend(templates)
    return result


@router.post("/", response_model=TemplateResponse)
def create_template(data: TemplateCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    template = Template(name=data.name, description=data.description, category=data.category, config=data.config)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if template_id == 0:
        defaults = get_default_templates()
        if defaults:
            first = next(iter(defaults.values()))
            return TemplateResponse(id=0, name=first["name"], description=first["description"],
                          category=first["category"], config=first["config"], created_at=None)
        raise HTTPException(404, "Default template not found")
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(404, "Template not found")
    return template


@router.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(404, "Template not found")
    db.delete(template)
    db.commit()
    return {"ok": True}
