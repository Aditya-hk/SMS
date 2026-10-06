
"""Frontend compatibility API for the Smart Municipal Corporation UI.

The original backend exposes normalized CRUD endpoints. The supplied frontend
was written against a richer UI API (joined names, current-user operations,
and {success, data} envelopes). This router bridges the two without changing
the existing DBMS CRUD endpoints.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.dependencies import get_db
from backend.security import hash_password, verify_password
from backend.models.user import User
from backend.models.citizen import Citizen
from backend.models.officer import Officer
from backend.models.contractor import Contractor
from backend.models.location import Location
from backend.models.road import Road
from backend.models.pipeline import Pipeline
from backend.models.project import Project
from backend.models.project_progress import ProjectProgress
from backend.models.payment import Payment
from backend.models.maintenance import Maintenance
from backend.models.complaint import Complaint
from backend.models.complaint_status_history import ComplaintStatusHistory
from backend.models.feedback import Feedback
from backend.models.alert import Alert

router = APIRouter(prefix="/api/ui", tags=["frontend"])

def ok(data=None, message="OK"):
    return {"success": True, "message": message, "data": data}

def _json(v):
    if isinstance(v, (Decimal,)):
        return float(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v

def as_date(v):
    if v in (None, ""): return None
    if isinstance(v, date): return v
    return date.fromisoformat(v)

def _user_token(user_id: int) -> str:
    # Local/demo token. For production, replace this with JWT/OAuth.
    return f"user-{user_id}"

def current_user(authorization: Optional[str] = Header(default=None),
                 db: Session = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Login required")
    token = authorization.split(" ", 1)[1].strip()
    if not token.startswith("user-"):
        raise HTTPException(401, "Invalid session")
    try:
        uid = int(token[5:])
    except ValueError:
        raise HTTPException(401, "Invalid session")
    user = db.query(User).filter(User.id == uid).first()
    if not user or not user.is_active:
        raise HTTPException(401, "Invalid session")
    return user

def user_dict(u):
    return {
        "id": u.id, "full_name": u.full_name, "email": u.email,
        "phone": u.phone, "role": u.role, "is_active": bool(u.is_active)
    }

def location_dict(l):
    return {"id": l.id, "area_name": l.area_name, "ward": l.ward, "pincode": l.pincode}

def complaint_dict(c, db):
    loc = db.query(Location).filter(Location.id == c.location_id).first()
    citizen = db.query(User).filter(User.id == c.citizen_id).first()
    officer = db.query(User).filter(User.id == c.assigned_officer_id).first() if c.assigned_officer_id else None
    history = db.query(ComplaintStatusHistory).filter(
        ComplaintStatusHistory.complaint_id == c.id
    ).order_by(ComplaintStatusHistory.changed_at.asc()).all()
    fb = db.query(Feedback).filter(Feedback.complaint_id == c.id).first()
    return {
        "id": c.id, "citizen_id": c.citizen_id, "citizen_name": citizen.full_name if citizen else None,
        "title": c.title, "description": c.description, "category": c.category,
        "location_id": c.location_id, "area_name": loc.area_name if loc else None,
        "ward": loc.ward if loc else None, "complaint_date": c.complaint_date,
        "status": c.status, "assigned_officer_id": c.assigned_officer_id,
        "officer_name": officer.full_name if officer else None,
        "created_at": c.created_at, "updated_at": c.updated_at,
        "history": [{
            "id": h.id, "old_status": h.old_status, "new_status": h.new_status,
            "changed_by": h.changed_by,
            "changed_by_name": (db.query(User.full_name).filter(User.id == h.changed_by).scalar()) or "Unknown",
            "remarks": h.remarks, "changed_at": h.changed_at
        } for h in history],
        "feedback": ({"id": fb.id, "rating": fb.rating, "comment": fb.comment, "created_at": fb.created_at} if fb else None)
    }

def project_dict(p, db):
    loc = db.query(Location).filter(Location.id == p.location_id).first()
    road = db.query(Road).filter(Road.id == p.road_id).first() if p.road_id else None
    officer = db.query(User).filter(User.id == p.officer_id).first()
    contractor = db.query(User).filter(User.id == p.contractor_id).first()
    contractor_profile = db.query(Contractor).filter(Contractor.user_id == p.contractor_id).first()
    return {
        "id": p.id, "title": p.title, "description": p.description,
        "location_id": p.location_id, "area_name": loc.area_name if loc else None,
        "ward": loc.ward if loc else None, "road_id": p.road_id,
        "road_name": road.name if road else None, "pipeline_id": p.pipeline_id,
        "officer_id": p.officer_id, "officer_name": officer.full_name if officer else None,
        "contractor_id": p.contractor_id, "company_name": contractor_profile.company_name if contractor_profile else (contractor.full_name if contractor else None),
        "budget": float(p.budget), "start_date": p.start_date,
        "expected_completion_date": p.expected_completion_date,
        "actual_completion_date": p.actual_completion_date, "status": p.status,
        "progress_percent": p.progress_percent, "remarks": p.remarks, "created_at": p.created_at
    }

def road_dict(r, db, details=False):
    loc = db.query(Location).filter(Location.id == r.location_id).first()
    d = {
        "id": r.id, "location_id": r.location_id, "name": r.name,
        "area_name": loc.area_name if loc else None, "ward": loc.ward if loc else None,
        "pincode": loc.pincode if loc else None, "length_km": float(r.length_km),
        "width_m": float(r.width_m), "road_condition": r.road_condition,
        "last_maintained_date": r.last_maintained_date
    }
    if details:
        ps = db.query(Project).filter(Project.road_id == r.id).all()
        ms = db.query(Maintenance).filter(Maintenance.road_id == r.id).all()
        d["projects"] = [project_dict(p, db) for p in ps]
        d["maintenance"] = [{"id": m.id, "description": m.description, "status": m.status,
                             "maintenance_date": m.maintenance_date} for m in ms]
    return d

def pipeline_dict(p, db):
    loc = db.query(Location).filter(Location.id == p.location_id).first()
    return {"id": p.id, "location_id": p.location_id, "name": p.name,
            "pipeline_type": p.pipeline_type, "length_km": float(p.length_km),
            "status": p.status, "installed_year": p.installed_year,
            "area_name": loc.area_name if loc else None, "ward": loc.ward if loc else None}

def contractor_dict(c, db):
    u = db.query(User).filter(User.id == c.user_id).first()
    total = db.query(Project).filter(Project.contractor_id == c.user_id).count()
    completed = db.query(Project).filter(Project.contractor_id == c.user_id, Project.status == "COMPLETED").count()
    ongoing = db.query(Project).filter(Project.contractor_id == c.user_id, Project.status == "IN_PROGRESS").count()
    return {"id": c.user_id, "user_id": c.user_id, "company_name": c.company_name,
            "license_no": c.license_no, "address": c.address,
            "full_name": u.full_name if u else None, "email": u.email if u else None,
            "phone": u.phone if u else None, "is_active": bool(u.is_active) if u else False,
            "total_projects": total, "completed_projects": completed,
            "ongoing_projects": ongoing}

def officer_dict(o, db):
    u = db.query(User).filter(User.id == o.user_id).first()
    return {"id": o.user_id, "user_id": o.user_id, "full_name": u.full_name if u else None,
            "email": u.email if u else None, "phone": u.phone if u else None,
            "department": o.department, "designation": o.designation,
            "is_active": bool(u.is_active) if u else False}

# ---------------- AUTH ----------------
@router.post("/auth/login")
def ui_login(body: dict, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == body.get("email")).first()
    if not u or not verify_password(body.get("password", ""), u.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return ok({"token": _user_token(u.id), "user": user_dict(u)}, "Login successful")

@router.post("/auth/register")
def ui_register(body: dict, db: Session = Depends(get_db)):
    email = body.get("email")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "Email already registered")
    u = User(full_name=body["full_name"], email=email,
             password_hash=hash_password(body["password"]),
             phone=body.get("phone") or None, role="CITIZEN", is_active=True)
    db.add(u); db.flush()
    db.add(Citizen(user_id=u.id, address=body.get("address") or None, ward=body.get("ward") or None))
    db.commit(); db.refresh(u)
    return ok(user_dict(u), "Registration successful")

@router.get("/auth/me")
def ui_me(user=Depends(current_user), db: Session = Depends(get_db)):
    d = user_dict(user)
    if user.role == "CITIZEN":
        c = db.query(Citizen).filter(Citizen.user_id == user.id).first()
        if c: d.update({"address": c.address, "ward": c.ward})
    return ok(d)

@router.put("/auth/me")
def ui_update_me(body: dict, user=Depends(current_user), db: Session = Depends(get_db)):
    if body.get("full_name"): user.full_name = body["full_name"]
    if "phone" in body: user.phone = body.get("phone") or None
    if user.role == "CITIZEN":
        c = db.query(Citizen).filter(Citizen.user_id == user.id).first()
        if not c:
            c = Citizen(user_id=user.id); db.add(c)
        c.address = body.get("address")
        c.ward = body.get("ward")
    db.commit(); db.refresh(user)
    return ok(user_dict(user), "Profile updated")

@router.post("/auth/logout")
def ui_logout():
    return ok(None, "Logged out")

# ---------------- LOCATIONS ----------------
@router.get("/locations")
def ui_locations(db: Session = Depends(get_db)):
    return ok([location_dict(x) for x in db.query(Location).all()])

@router.post("/locations")
def ui_create_location(body: dict, user=Depends(current_user), db: Session = Depends(get_db)):
    l = Location(area_name=body["area_name"], ward=body["ward"], pincode=body["pincode"])
    db.add(l); db.commit(); db.refresh(l)
    return ok(location_dict(l), "Location created")

@router.put("/locations/{location_id}")
def ui_update_location(location_id: int, body: dict, user=Depends(current_user), db: Session = Depends(get_db)):
    l = db.query(Location).filter(Location.id == location_id).first()
    if not l: raise HTTPException(404, "Location not found")
    for k in ("area_name", "ward", "pincode"):
        if k in body: setattr(l, k, body[k])
    db.commit(); return ok(location_dict(l), "Location updated")

@router.delete("/locations/{location_id}")
def ui_delete_location(location_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    l = db.query(Location).filter(Location.id == location_id).first()
    if not l: raise HTTPException(404, "Location not found")
    db.delete(l); db.commit(); return ok(None, "Location deleted")

# ---------------- COMPLAINTS ----------------
@router.get("/complaints")
def ui_complaints(status: Optional[str] = None, user=Depends(current_user), db: Session = Depends(get_db)):
    q = db.query(Complaint)
    if user.role == "CITIZEN":
        q = q.filter(Complaint.citizen_id == user.id)
    elif user.role == "OFFICER":
        q = q.filter(Complaint.assigned_officer_id == user.id)
    if status:
        q = q.filter(Complaint.status == status)
    return ok([complaint_dict(c, db) for c in q.order_by(Complaint.id.desc()).all()])

@router.post("/complaints")
def ui_create_complaint(body: dict, user=Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "CITIZEN": raise HTTPException(403, "Citizen access required")
    loc = db.query(Location).filter(Location.id == int(body["location_id"])).first()
    if not loc: raise HTTPException(404, "Location not found")
    c = Complaint(citizen_id=user.id, title=body["title"], description=body["description"],
                  category=body["category"], location_id=int(body["location_id"]),
                  complaint_date=as_date(body["complaint_date"]), status="SUBMITTED")
    db.add(c); db.commit(); db.refresh(c)
    db.add(ComplaintStatusHistory(complaint_id=c.id, old_status=None, new_status="SUBMITTED",
                                  changed_by=user.id, remarks="Complaint submitted"))
    db.commit()
    return ok(complaint_dict(c, db), "Complaint submitted")

@router.get("/complaints/{complaint_id}")
def ui_get_complaint(complaint_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c: raise HTTPException(404, "Complaint not found")
    if user.role == "CITIZEN" and c.citizen_id != user.id: raise HTTPException(403, "Access denied")
    return ok(complaint_dict(c, db))

@router.get("/complaints/track/{complaint_id}")
def ui_track_complaint(complaint_id: int, db: Session = Depends(get_db)):
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c: raise HTTPException(404, "Complaint not found")
    return ok(complaint_dict(c, db))

@router.put("/complaints/{complaint_id}/status")
def ui_status(complaint_id: int, body: dict, user=Depends(current_user), db: Session = Depends(get_db)):
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not c: raise HTTPException(404, "Complaint not found")
    if user.role == "CITIZEN" and c.citizen_id != user.id: raise HTTPException(403, "Access denied")
    old = c.status; new = body.get("status")
    if new not in {"SUBMITTED","ASSIGNED","IN_PROGRESS","RESOLVED","CLOSED","REJECTED"}:
        raise HTTPException(400, "Invalid complaint status")
    c.status = new
    db.add(ComplaintStatusHistory(complaint_id=c.id, old_status=old, new_status=new,
                                  changed_by=user.id, remarks=body.get("remarks")))
    db.commit(); db.refresh(c)
    return ok(complaint_dict(c, db), "Complaint status updated")

@router.put("/complaints/{complaint_id}/assign")
def ui_assign(complaint_id: int, body: dict, user=Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "ADMIN": raise HTTPException(403, "Admin access required")
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    officer_id = int(body["officer_id"])
    o = db.query(User).filter(User.id == officer_id, User.role == "OFFICER").first()
    if not c or not o: raise HTTPException(404, "Complaint or officer not found")
    old = c.status; c.assigned_officer_id = officer_id; c.status = "ASSIGNED"
    db.add(ComplaintStatusHistory(complaint_id=c.id, old_status=old, new_status="ASSIGNED",
                                  changed_by=user.id, remarks="Assigned to officer"))
    db.commit(); db.refresh(c)
    return ok(complaint_dict(c, db), "Complaint assigned")

# ---------------- FEEDBACK ----------------
@router.get("/feedback")
def ui_feedback(user=Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Feedback).all()
    out=[]
    for f in rows:
        c=db.query(Complaint).filter(Complaint.id==f.complaint_id).first()
        citizen=db.query(User).filter(User.id==f.citizen_id).first()
        out.append({"id":f.id,"complaint_id":f.complaint_id,"complaint_title":c.title if c else None,
                    "citizen_id":f.citizen_id,"citizen_name":citizen.full_name if citizen else None,
                    "rating":f.rating,"comment":f.comment,"created_at":f.created_at})
    return ok(out)

@router.post("/feedback")
def ui_feedback_create(body: dict, user=Depends(current_user), db: Session = Depends(get_db)):
    cid=int(body["complaint_id"])
    c=db.query(Complaint).filter(Complaint.id==cid).first()
    if not c or c.citizen_id != user.id: raise HTTPException(403,"You can only review your own complaint")
    if db.query(Feedback).filter(Feedback.complaint_id==cid).first(): raise HTTPException(400,"Feedback already exists")
    f=Feedback(complaint_id=cid,citizen_id=user.id,rating=int(body["rating"]),comment=body.get("comment"))
    db.add(f); db.commit(); db.refresh(f)
    return ok({"id":f.id,"complaint_id":f.complaint_id,"citizen_id":f.citizen_id,
               "rating":f.rating,"comment":f.comment,"created_at":f.created_at},"Feedback submitted")

# ---------------- ALERTS ----------------
@router.get("/alerts")
def ui_alerts(user=Depends(current_user), db: Session = Depends(get_db)):
    return ok([{"id":a.id,"title":a.title,"message":a.message,"severity":a.severity,"audience":a.audience,"expires_at":a.expires_at,"created_by":a.created_by,"created_at":a.created_at} for a in db.query(Alert).order_by(Alert.created_at.desc()).all()])

@router.get("/alerts/public")
def ui_public_alerts(db: Session = Depends(get_db)):
    rows=db.query(Alert).filter(Alert.audience=="PUBLIC").order_by(Alert.created_at.desc()).all()
    return ok([{"id":a.id,"title":a.title,"message":a.message,"severity":a.severity,
                "audience":a.audience,"expires_at":a.expires_at,"created_by":a.created_by,
                "created_at":a.created_at} for a in rows])

@router.post("/alerts")
def ui_create_alert(body: dict, user=Depends(current_user), db: Session = Depends(get_db)):
    a = Alert(title=body["title"], message=body["message"], severity=body["severity"],
              audience=body["audience"], expires_at=as_date(body.get("expires_at")),
              created_by=user.id)
    db.add(a); db.commit(); db.refresh(a)
    return ok({"id":a.id,"title":a.title,"message":a.message,"severity":a.severity,
               "audience":a.audience,"expires_at":a.expires_at,"created_by":a.created_by,
               "created_at":a.created_at}, "Alert created")

@router.put("/alerts/{alert_id}")
def ui_update_alert(alert_id:int, body:dict, user=Depends(current_user), db:Session=Depends(get_db)):
    a=db.query(Alert).filter(Alert.id==alert_id).first()
    if not a: raise HTTPException(404,"Alert not found")
    for k in ("title","message","severity","audience"):
        if k in body: setattr(a,k,body[k])
    if "expires_at" in body: a.expires_at=as_date(body["expires_at"])
    db.commit()
    return ok({"id":a.id,"title":a.title,"message":a.message,"severity":a.severity,
               "audience":a.audience,"expires_at":a.expires_at,"created_by":a.created_by,
               "created_at":a.created_at}, "Alert updated")

@router.delete("/alerts/{alert_id}")
def ui_delete_alert(alert_id:int, user=Depends(current_user), db:Session=Depends(get_db)):
    a=db.query(Alert).filter(Alert.id==alert_id).first()
    if not a: raise HTTPException(404,"Alert not found")
    db.delete(a); db.commit(); return ok(None,"Alert deleted")

# ---------------- OFFICERS ----------------
@router.get("/officers")
def ui_officers(user=Depends(current_user), db: Session = Depends(get_db)):
    return ok([officer_dict(o,db) for o in db.query(Officer).all()])

@router.post("/officers")
def ui_create_officer(body: dict, user=Depends(current_user), db: Session = Depends(get_db)):
    if user.role != "ADMIN": raise HTTPException(403,"Admin access required")
    if db.query(User).filter(User.email==body["email"]).first(): raise HTTPException(400,"Email already registered")
    u=User(full_name=body["full_name"],email=body["email"],password_hash=hash_password(body["password"]),
           phone=body.get("phone"),role="OFFICER",is_active=True)
    db.add(u); db.flush()
    db.add(Officer(user_id=u.id,department=body.get("department"),designation=body.get("designation")))
    db.commit(); db.refresh(u)
    return ok(officer_dict(db.query(Officer).get(u.id),db),"Officer created")

@router.put("/officers/{user_id}")
def ui_update_officer(user_id:int, body:dict, user=Depends(current_user), db:Session=Depends(get_db)):
    if user.role!="ADMIN": raise HTTPException(403,"Admin access required")
    u=db.query(User).filter(User.id==user_id,User.role=="OFFICER").first()
    o=db.query(Officer).filter(Officer.user_id==user_id).first()
    if not u or not o: raise HTTPException(404,"Officer not found")
    for k in ("full_name","phone"): 
        if k in body: setattr(u,k,body[k])
    if "is_active" in body: u.is_active=bool(int(body["is_active"]))
    for k in ("department","designation"):
        if k in body: setattr(o,k,body[k])
    db.commit()
    return ok(officer_dict(o,db),"Officer updated")

@router.delete("/officers/{user_id}")
def ui_delete_officer(user_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    if user.role!="ADMIN": raise HTTPException(403,"Admin access required")
    o=db.query(Officer).filter(Officer.user_id==user_id).first()
    u=db.query(User).filter(User.id==user_id).first()
    if not o or not u: raise HTTPException(404,"Officer not found")
    db.delete(o); db.delete(u); db.commit(); return ok(None,"Officer deleted")

# ---------------- CONTRACTORS ----------------
@router.get("/contractors/details")
def ui_contractor_details(db:Session=Depends(get_db)):
    return ok([contractor_dict(c,db) for c in db.query(Contractor).all()])

@router.get("/contractors")
def ui_contractors(db:Session=Depends(get_db)):
    return ok([contractor_dict(c,db) for c in db.query(Contractor).all()])

@router.post("/contractors")
def ui_create_contractor(body:dict,user=Depends(current_user),db:Session=Depends(get_db)):
    if user.role!="ADMIN": raise HTTPException(403,"Admin access required")
    if db.query(User).filter(User.email==body["email"]).first(): raise HTTPException(400,"Email already registered")
    if db.query(Contractor).filter(Contractor.license_no==body["license_no"]).first(): raise HTTPException(400,"License already registered")
    u=User(full_name=body["full_name"],email=body["email"],password_hash=hash_password(body["password"]),
           phone=body.get("phone"),role="CONTRACTOR",is_active=True)
    db.add(u); db.flush(); db.add(Contractor(user_id=u.id,company_name=body.get("company_name"),
                                             license_no=body["license_no"],address=body.get("address")))
    db.commit(); db.refresh(u)
    return ok(contractor_dict(db.query(Contractor).get(u.id),db),"Contractor created")

@router.put("/contractors/{user_id}")
def ui_update_contractor(user_id:int,body:dict,user=Depends(current_user),db:Session=Depends(get_db)):
    if user.role!="ADMIN": raise HTTPException(403,"Admin access required")
    u=db.query(User).filter(User.id==user_id,User.role=="CONTRACTOR").first()
    c=db.query(Contractor).filter(Contractor.user_id==user_id).first()
    if not u or not c: raise HTTPException(404,"Contractor not found")
    for k in ("full_name","phone"): 
        if k in body: setattr(u,k,body[k])
    if "is_active" in body: u.is_active=bool(int(body["is_active"]))
    for k in ("company_name","license_no","address"):
        if k in body: setattr(c,k,body[k])
    db.commit(); return ok(contractor_dict(c,db),"Contractor updated")

@router.delete("/contractors/{user_id}")
def ui_delete_contractor(user_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    if user.role!="ADMIN": raise HTTPException(403,"Admin access required")
    c=db.query(Contractor).filter(Contractor.user_id==user_id).first()
    u=db.query(User).filter(User.id==user_id).first()
    if not c or not u: raise HTTPException(404,"Contractor not found")
    db.delete(c); db.delete(u); db.commit(); return ok(None,"Contractor deleted")

# ---------------- ROADS ----------------
@router.get("/roads")
def ui_roads(db:Session=Depends(get_db)):
    return ok([road_dict(r,db) for r in db.query(Road).all()])

@router.get("/roads/{road_id}")
def ui_road(road_id:int,db:Session=Depends(get_db)):
    r=db.query(Road).filter(Road.id==road_id).first()
    if not r: raise HTTPException(404,"Road not found")
    return ok(road_dict(r,db,True))

@router.post("/roads")
def ui_create_road(body:dict,user=Depends(current_user),db:Session=Depends(get_db)):
    r=Road(location_id=int(body["location_id"]),name=body["name"],length_km=float(body["length_km"]),
           width_m=float(body.get("width_m") or 0),road_condition=body["road_condition"],
           last_maintained_date=as_date(body.get("last_maintained_date")))
    db.add(r); db.commit(); db.refresh(r); return ok(road_dict(r,db),"Road created")

@router.put("/roads/{road_id}")
def ui_update_road(road_id:int,body:dict,user=Depends(current_user),db:Session=Depends(get_db)):
    r=db.query(Road).filter(Road.id==road_id).first()
    if not r: raise HTTPException(404,"Road not found")
    for k in ("name","road_condition","last_maintained_date"): 
        if k in body: setattr(r,k,as_date(body[k]) if k=="last_maintained_date" else body[k])
    for k in ("location_id","length_km","width_m"):
        if k in body and body[k] is not None: setattr(r,k,int(body[k]) if k=="location_id" else float(body[k]))
    db.commit(); return ok(road_dict(r,db),"Road updated")

@router.delete("/roads/{road_id}")
def ui_delete_road(road_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    r=db.query(Road).filter(Road.id==road_id).first()
    if not r: raise HTTPException(404,"Road not found")
    db.delete(r); db.commit(); return ok(None,"Road deleted")

# ---------------- PIPELINES ----------------
@router.get("/pipelines")
def ui_pipelines(db:Session=Depends(get_db)):
    return ok([pipeline_dict(p,db) for p in db.query(Pipeline).all()])

@router.post("/pipelines")
def ui_create_pipeline(body:dict,user=Depends(current_user),db:Session=Depends(get_db)):
    p=Pipeline(location_id=int(body["location_id"]),name=body["name"],pipeline_type=body["pipeline_type"],
               length_km=float(body["length_km"]),status=body["status"],installed_year=int(body["installed_year"]))
    db.add(p); db.commit(); db.refresh(p); return ok(pipeline_dict(p,db),"Pipeline created")

@router.put("/pipelines/{pipeline_id}")
def ui_update_pipeline(pipeline_id:int,body:dict,user=Depends(current_user),db:Session=Depends(get_db)):
    p=db.query(Pipeline).filter(Pipeline.id==pipeline_id).first()
    if not p: raise HTTPException(404,"Pipeline not found")
    for k in ("name","pipeline_type","status"): 
        if k in body: setattr(p,k,body[k])
    for k in ("location_id","installed_year"):
        if k in body and body[k] is not None: setattr(p,k,int(body[k]))
    if "length_km" in body and body["length_km"] is not None: p.length_km=float(body["length_km"])
    db.commit(); return ok(pipeline_dict(p,db),"Pipeline updated")

@router.delete("/pipelines/{pipeline_id}")
def ui_delete_pipeline(pipeline_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    p=db.query(Pipeline).filter(Pipeline.id==pipeline_id).first()
    if not p: raise HTTPException(404,"Pipeline not found")
    db.delete(p); db.commit(); return ok(None,"Pipeline deleted")

# ---------------- PROJECTS ----------------
@router.get("/projects/mine")
def ui_my_projects(user=Depends(current_user),db:Session=Depends(get_db)):
    if user.role=="OFFICER": q=db.query(Project).filter(Project.officer_id==user.id)
    elif user.role=="CONTRACTOR": q=db.query(Project).filter(Project.contractor_id==user.id)
    else: q=db.query(Project)
    return ok([project_dict(p,db) for p in q.order_by(Project.id.desc()).all()])

@router.get("/projects")
def ui_projects(status:Optional[str]=None,db:Session=Depends(get_db)):
    q=db.query(Project)
    if status: q=q.filter(Project.status==status)
    return ok([project_dict(p,db) for p in q.order_by(Project.id.desc()).all()])

@router.post("/projects")
def ui_create_project(body:dict,user=Depends(current_user),db:Session=Depends(get_db)):
    p=Project(title=body["title"],description=body.get("description"),location_id=int(body["location_id"]),
              road_id=int(body["road_id"]) if body.get("road_id") else None,
              pipeline_id=int(body["pipeline_id"]) if body.get("pipeline_id") else None,
              officer_id=int(body["officer_id"]),contractor_id=int(body["contractor_id"]),
              budget=float(body["budget"]),start_date=as_date(body["start_date"]),
              expected_completion_date=as_date(body["expected_completion_date"]),
              actual_completion_date=as_date(body.get("actual_completion_date")),
              status=body["status"],progress_percent=int(body.get("progress_percent") or 0),
              remarks=body.get("remarks"))
    db.add(p); db.commit(); db.refresh(p); return ok(project_dict(p,db),"Project created")

@router.put("/projects/{project_id}")
def ui_update_project(project_id:int,body:dict,user=Depends(current_user),db:Session=Depends(get_db)):
    p=db.query(Project).filter(Project.id==project_id).first()
    if not p: raise HTTPException(404,"Project not found")
    for k in ("title","description","start_date","expected_completion_date","actual_completion_date","status","remarks"):
        if k in body: setattr(p,k,as_date(body[k]) if k in ("start_date","expected_completion_date","actual_completion_date") else body[k])
    for k in ("location_id","road_id","pipeline_id","officer_id","contractor_id","progress_percent"):
        if k in body: setattr(p,k,int(body[k]) if body[k] is not None else None)
    if "budget" in body and body["budget"] is not None: p.budget=float(body["budget"])
    db.commit(); return ok(project_dict(p,db),"Project updated")

@router.delete("/projects/{project_id}")
def ui_delete_project(project_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    p=db.query(Project).filter(Project.id==project_id).first()
    if not p: raise HTTPException(404,"Project not found")
    db.delete(p); db.commit(); return ok(None,"Project deleted")

@router.put("/projects/{project_id}/status")
def ui_project_status(project_id:int,body:dict,user=Depends(current_user),db:Session=Depends(get_db)):
    p=db.query(Project).filter(Project.id==project_id).first()
    if not p: raise HTTPException(404,"Project not found")
    p.status=body["status"]; db.commit(); return ok(project_dict(p,db),"Project status updated")

# ---------------- PROGRESS ----------------
@router.post("/progress")
def ui_progress(body:dict,user=Depends(current_user),db:Session=Depends(get_db)):
    p=db.query(Project).filter(Project.id==int(body["project_id"])).first()
    if not p: raise HTTPException(404,"Project not found")
    pct=int(body["progress_percent"])
    if not 0<=pct<=100: raise HTTPException(400,"Progress must be 0-100")
    pp=ProjectProgress(project_id=p.id,progress_percent=pct,
                       progress_date=body.get("progress_date") or date.today(),
                       remarks=body.get("remarks"),updated_by=user.id)
    p.progress_percent=pct
    db.add(pp); db.commit(); db.refresh(pp)
    return ok({"id":pp.id,"project_id":pp.project_id,"progress_percent":pp.progress_percent,
               "progress_date":pp.progress_date,"remarks":pp.remarks,"updated_by":pp.updated_by},"Progress updated")

@router.get("/progress/project/{project_id}")
def ui_progress_history(project_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(ProjectProgress).filter(ProjectProgress.project_id==project_id).order_by(ProjectProgress.progress_date.desc()).all()
    return ok([{"id":r.id,"project_id":r.project_id,"progress_percent":r.progress_percent,
                "progress_date":r.progress_date,"remarks":r.remarks,"updated_by":r.updated_by} for r in rows])

# ---------------- PAYMENTS ----------------
@router.get("/payments")
def ui_payments(user=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(Payment).all(); out=[]
    for p in rows:
        pr=db.query(Project).filter(Project.id==p.project_id).first()
        c=db.query(Contractor).filter(Contractor.user_id==p.contractor_id).first()
        out.append({"id":p.id,"project_id":p.project_id,"project_title":pr.title if pr else None,
                    "contractor_id":p.contractor_id,"company_name":c.company_name if c else None,
                    "amount":float(p.amount),"payment_date":p.payment_date,"status":p.status,"description":p.description})
    return ok(out)

@router.post("/payments")
def ui_create_payment(body:dict,user=Depends(current_user),db:Session=Depends(get_db)):
    pr=db.query(Project).filter(Project.id==int(body["project_id"])).first()
    if not pr: raise HTTPException(404,"Project not found")
    contractor_id=pr.contractor_id
    p=Payment(project_id=pr.id,contractor_id=contractor_id,amount=float(body["amount"]),
              payment_date=as_date(body["payment_date"]),status=body["status"],description=body.get("description"))
    db.add(p); db.commit(); db.refresh(p); return ok({"id":p.id,"project_id":p.project_id,
        "contractor_id":p.contractor_id,"amount":float(p.amount),"payment_date":p.payment_date,
        "status":p.status,"description":p.description},"Payment created")

@router.put("/payments/{payment_id}")
def ui_update_payment(payment_id:int,body:dict,user=Depends(current_user),db:Session=Depends(get_db)):
    p=db.query(Payment).filter(Payment.id==payment_id).first()
    if not p: raise HTTPException(404,"Payment not found")
    for k in ("payment_date","status","description"):
        if k in body: setattr(p,k,as_date(body[k]) if k=="payment_date" else body[k])
    if "amount" in body: p.amount=float(body["amount"])
    if "project_id" in body and body["project_id"]:
        p.project_id=int(body["project_id"])
        pr=db.query(Project).filter(Project.id==p.project_id).first()
        if pr: p.contractor_id=pr.contractor_id
    db.commit(); return ok(None,"Payment updated")

@router.delete("/payments/{payment_id}")
def ui_delete_payment(payment_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    p=db.query(Payment).filter(Payment.id==payment_id).first()
    if not p: raise HTTPException(404,"Payment not found")
    db.delete(p); db.commit(); return ok(None,"Payment deleted")

# ---------------- MAINTENANCE ----------------
@router.get("/maintenance")
def ui_maintenance(user=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(Maintenance).all(); out=[]
    for m in rows:
        r=db.query(Road).filter(Road.id==m.road_id).first() if m.road_id else None
        p=db.query(Pipeline).filter(Pipeline.id==m.pipeline_id).first() if m.pipeline_id else None
        c=db.query(Contractor).filter(Contractor.user_id==m.assigned_contractor_id).first()
        o=db.query(User).filter(User.id==m.assigned_officer_id).first()
        out.append({"id":m.id,"project_id":m.project_id,"road_id":m.road_id,"pipeline_id":m.pipeline_id,
                    "description":m.description,"status":m.status,"maintenance_date":m.maintenance_date,
                    "assigned_contractor_id":m.assigned_contractor_id,"assigned_officer_id":m.assigned_officer_id,
                    "road_name":r.name if r else None,"pipeline_name":p.name if p else None,
                    "company_name":c.company_name if c else None,"officer_name":o.full_name if o else None})
    return ok(out)

@router.post("/maintenance")
def ui_create_maintenance(body:dict,user=Depends(current_user),db:Session=Depends(get_db)):
    m=Maintenance(project_id=int(body["project_id"]) if body.get("project_id") else None,
                  road_id=int(body["road_id"]) if body.get("road_id") else None,
                  pipeline_id=int(body["pipeline_id"]) if body.get("pipeline_id") else None,
                  description=body["description"],status=body["status"],maintenance_date=as_date(body["maintenance_date"]),
                  assigned_contractor_id=int(body["assigned_contractor_id"]),
                  assigned_officer_id=int(body["assigned_officer_id"]))
    if not m.road_id and not m.pipeline_id: raise HTTPException(400,"Select a road or pipeline")
    db.add(m); db.commit(); db.refresh(m); return ok({"id":m.id},"Maintenance created")

@router.put("/maintenance/{maintenance_id}")
def ui_update_maintenance(maintenance_id:int,body:dict,user=Depends(current_user),db:Session=Depends(get_db)):
    m=db.query(Maintenance).filter(Maintenance.id==maintenance_id).first()
    if not m: raise HTTPException(404,"Maintenance not found")
    for k in ("description","status","maintenance_date"):
        if k in body: setattr(m,k,as_date(body[k]) if k=="maintenance_date" else body[k])
    for k in ("project_id","road_id","pipeline_id","assigned_contractor_id","assigned_officer_id"):
        if k in body: setattr(m,k,int(body[k]) if body[k] else None)
    db.commit(); return ok(None,"Maintenance updated")

@router.put("/maintenance/{maintenance_id}/status")
def ui_maintenance_status(maintenance_id:int,body:dict,user=Depends(current_user),db:Session=Depends(get_db)):
    m=db.query(Maintenance).filter(Maintenance.id==maintenance_id).first()
    if not m: raise HTTPException(404,"Maintenance not found")
    m.status=body["status"]; db.commit(); return ok(None,"Maintenance status updated")

@router.delete("/maintenance/{maintenance_id}")
def ui_delete_maintenance(maintenance_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    m=db.query(Maintenance).filter(Maintenance.id==maintenance_id).first()
    if not m: raise HTTPException(404,"Maintenance not found")
    db.delete(m); db.commit(); return ok(None,"Maintenance deleted")

# ---------------- PUBLIC STATS ----------------
@router.get("/public/stats")
def ui_stats(db:Session=Depends(get_db)):
    projects=db.query(Project).all(); complaints=db.query(Complaint).all(); roads=db.query(Road).all()
    contractors=db.query(Contractor).count()
    total_budget=sum(float(p.budget) for p in projects)
    paid=sum(float(x.amount) for x in db.query(Payment).filter(Payment.status=="PAID").all())
    by_condition=[]
    for cond in ("GOOD","FAIR","POOR","UNDER_REPAIR"):
        by_condition.append({"road_condition":cond,"total":sum(1 for r in roads if r.road_condition==cond)})
    return ok({
        "projects":{"total":len(projects),"completed":sum(p.status=="COMPLETED" for p in projects),
                    "ongoing":sum(p.status=="IN_PROGRESS" for p in projects),"total_budget":total_budget},
        "complaints":{"total":len(complaints),"resolved":sum(p.status in ("RESOLVED","CLOSED") for p in complaints)},
        "contractors":contractors,"roads":{"total":len(roads),"total_km":sum(float(r.length_km) for r in roads),
                                           "by_condition":by_condition},"expenditure_paid":paid
    })

# ---------------- REPORTS ----------------
@router.get("/reports/complaints-by-status")
def report_complaints(db:Session=Depends(get_db)):
    rows=db.query(Complaint.status,func.count(Complaint.id).label("total")).group_by(Complaint.status).all()
    return ok([{"status":s,"total":int(n)} for s,n in rows])

@router.get("/reports/projects-by-status")
def report_projects(db:Session=Depends(get_db)):
    rows=db.query(Project.status,func.count(Project.id).label("total"),func.sum(Project.budget).label("total_budget")).group_by(Project.status).all()
    return ok([{"status":s,"total":int(n),"total_budget":float(b or 0)} for s,n,b in rows])

@router.get("/reports/expenditure")
def report_expenditure(db:Session=Depends(get_db)):
    out=[]
    for p in db.query(Project).all():
        paid=sum(float(x.amount) for x in db.query(Payment).filter(Payment.project_id==p.id,Payment.status=="PAID").all())
        out.append({"title":p.title,"budget":float(p.budget),"paid":paid,
                    "percent_of_budget_paid":round((paid/float(p.budget))*100,2) if p.budget else 0})
    return ok(out)

@router.get("/reports/contractor-projects")
def report_contractors(db:Session=Depends(get_db)):
    out=[]
    for c in db.query(Contractor).all():
        ps=db.query(Project).filter(Project.contractor_id==c.user_id).all()
        out.append({"company_name":c.company_name,"total_projects":len(ps),
                    "completed":sum(p.status=="COMPLETED" for p in ps),
                    "ongoing":sum(p.status=="IN_PROGRESS" for p in ps),
                    "total_budget":sum(float(p.budget) for p in ps)})
    return ok(out)

@router.get("/reports/road-maintenance")
def report_road_maintenance(db:Session=Depends(get_db)):
    out=[]
    for r in db.query(Road).all():
        ms=db.query(Maintenance).filter(Maintenance.road_id==r.id).all()
        out.append({"road":r.name,"road_condition":r.road_condition,"maintenance_jobs":len(ms),
                    "completed_jobs":sum(m.status=="COMPLETED" for m in ms),
                    "latest_job":max((m.maintenance_date for m in ms),default=None)})
    return ok(out)

@router.get("/reports/complaint-resolution")
def report_resolution(db:Session=Depends(get_db)):
    out=[]
    for cat in ("ROAD","WATER","SEWAGE","GARBAGE","STREETLIGHT","OTHER"):
        cs=db.query(Complaint).filter(Complaint.category==cat).all()
        fbs=[db.query(Feedback).filter(Feedback.complaint_id==c.id).first() for c in cs]
        fbs=[f for f in fbs if f]
        out.append({"category":cat,"total":len(cs),"resolved":sum(c.status in ("RESOLVED","CLOSED") for c in cs),
                     "average_rating":round(sum(f.rating for f in fbs)/len(fbs),2) if fbs else None})
    return ok(out)
