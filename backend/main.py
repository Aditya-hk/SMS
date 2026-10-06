from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.models.location import Location
from backend.schemas.location import LocationCreate, LocationResponse
from backend.security import hash_password, verify_password
from backend.dependencies import get_db
from backend.models.contractor import Contractor
from backend.schemas.contractor import ContractorCreate, ContractorResponse
from backend.models.user import User
from backend.models.citizen import Citizen
from backend.models.officer import Officer
from backend.schemas.officer import OfficerCreate, OfficerResponse
from backend.schemas.user import UserCreate, UserResponse
from backend.schemas.auth import LoginRequest
from backend.schemas.citizen import CitizenCreate, CitizenResponse
from backend.models.road import Road
from backend.schemas.road import RoadCreate, RoadResponse
from backend.models.pipeline import Pipeline
from backend.schemas.pipeline import PipelineCreate, PipelineResponse
from backend.models.project import Project
from backend.schemas.project import ProjectCreate, ProjectResponse
from backend.models.payment import Payment
from backend.schemas.payment import PaymentCreate, PaymentResponse
from backend.models.project_progress import ProjectProgress

from backend.schemas.project_progress import (
    ProjectProgressCreate,
    ProjectProgressResponse
)
from backend.models.maintenance import Maintenance
from backend.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceResponse
)
from backend.models.complaint import Complaint
from backend.schemas.complaint import ComplaintCreate, ComplaintResponse
from backend.models.complaint_status_history import ComplaintStatusHistory
from backend.schemas.complaint_status_history import (
    ComplaintStatusHistoryCreate,
    ComplaintStatusHistoryResponse
)
from backend.models.feedback import Feedback
from backend.schemas.feedback import FeedbackCreate, FeedbackResponse
from backend.models.alert import Alert
from backend.schemas.alert import AlertCreate, AlertResponse

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend compatibility layer for the supplied HTML/JS application.
from backend.frontend_api import router as frontend_router
app.include_router(frontend_router)


@app.get("/")
def root():
    return {
        "message": "Smart Municipal Corporation API is running"
    }


@app.get("/api/db-test")
def database_test(db: Session = Depends(get_db)):
    return {
        "message": "Database session created successfully"
    }


# =========================================================
# USER APIs
# =========================================================

# CREATE USER
@app.post("/api/users", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        phone=user_data.phone,
        role=user_data.role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# GET ALL USERS
@app.get("/api/users", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()


# GET ONE USER
@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


# UPDATE USER
@app.put("/api/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    existing_user = (
        db.query(User)
        .filter(
            User.email == user_data.email,
            User.id != user_id
        )
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=400,
            detail="Email already registered by another user"
        )

    user.full_name = user_data.full_name
    user.email = user_data.email

    # Always hash the password
    user.password_hash = hash_password(
        user_data.password
    )

    user.phone = user_data.phone
    user.role = user_data.role

    db.commit()
    db.refresh(user)

    return user


# DELETE USER
@app.delete("/api/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    db.delete(user)
    db.commit()

    return {
        "message": "User deleted successfully"
    }


# =========================================================
# AUTHENTICATION
# =========================================================

@app.post("/api/auth/login")
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.email == login_data.email)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        login_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "message": "Login successful",
        "user_id": user.id,
        "email": user.email,
        "role": user.role
    }


# =========================================================
# CITIZEN APIs
# =========================================================

# CREATE CITIZEN
@app.post(
    "/api/citizens",
    response_model=CitizenResponse
)
def create_citizen(
    citizen_data: CitizenCreate,
    db: Session = Depends(get_db)
):
    # Check whether user exists
    user = (
        db.query(User)
        .filter(User.id == citizen_data.user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Check whether citizen profile already exists
    existing_citizen = (
        db.query(Citizen)
        .filter(
            Citizen.user_id == citizen_data.user_id
        )
        .first()
    )

    if existing_citizen is not None:
        raise HTTPException(
            status_code=400,
            detail="Citizen profile already exists for this user"
        )

    citizen = Citizen(
        user_id=citizen_data.user_id,
        address=citizen_data.address,
        ward=citizen_data.ward
    )

    db.add(citizen)
    db.commit()
    db.refresh(citizen)

    return citizen


# GET ALL CITIZENS
@app.get(
    "/api/citizens",
    response_model=list[CitizenResponse]
)
def get_citizens(
    db: Session = Depends(get_db)
):
    return db.query(Citizen).all()


# GET ONE CITIZEN
@app.get(
    "/api/citizens/{user_id}",
    response_model=CitizenResponse
)
def get_citizen(
    user_id: int,
    db: Session = Depends(get_db)
):
    citizen = (
        db.query(Citizen)
        .filter(Citizen.user_id == user_id)
        .first()
    )

    if citizen is None:
        raise HTTPException(
            status_code=404,
            detail="Citizen profile not found"
        )

    return citizen


# UPDATE CITIZEN
@app.put(
    "/api/citizens/{user_id}",
    response_model=CitizenResponse
)
def update_citizen(
    user_id: int,
    citizen_data: CitizenCreate,
    db: Session = Depends(get_db)
):
    citizen = (
        db.query(Citizen)
        .filter(Citizen.user_id == user_id)
        .first()
    )

    if citizen is None:
        raise HTTPException(
            status_code=404,
            detail="Citizen profile not found"
        )

    if citizen_data.user_id != user_id:
        raise HTTPException(
            status_code=400,
            detail="user_id in request body must match the URL user_id"
        )

    citizen.address = citizen_data.address
    citizen.ward = citizen_data.ward

    db.commit()
    db.refresh(citizen)

    return citizen


# DELETE CITIZEN
@app.delete("/api/citizens/{user_id}")
def delete_citizen(
    user_id: int,
    db: Session = Depends(get_db)
):
    citizen = (
        db.query(Citizen)
        .filter(Citizen.user_id == user_id)
        .first()
    )

    if citizen is None:
        raise HTTPException(
            status_code=404,
            detail="Citizen profile not found"
        )

    db.delete(citizen)
    db.commit()

    return {
        "message": "Citizen profile deleted successfully"
    }

# =========================================================
# OFFICER APIs
# =========================================================

# CREATE OFFICER
@app.post(
    "/api/officers",
    response_model=OfficerResponse
)
def create_officer(
    officer_data: OfficerCreate,
    db: Session = Depends(get_db)
):
    # Check whether user exists
    user = (
        db.query(User)
        .filter(User.id == officer_data.user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Check whether officer profile already exists
    existing_officer = (
        db.query(Officer)
        .filter(
            Officer.user_id == officer_data.user_id
        )
        .first()
    )

    if existing_officer is not None:
        raise HTTPException(
            status_code=400,
            detail="Officer profile already exists for this user"
        )

    officer = Officer(
        user_id=officer_data.user_id,
        department=officer_data.department,
        designation=officer_data.designation
    )

    db.add(officer)
    db.commit()
    db.refresh(officer)

    return officer


# GET ALL OFFICERS
@app.get(
    "/api/officers",
    response_model=list[OfficerResponse]
)
def get_officers(
    db: Session = Depends(get_db)
):
    return db.query(Officer).all()


# GET ONE OFFICER
@app.get(
    "/api/officers/{user_id}",
    response_model=OfficerResponse
)
def get_officer(
    user_id: int,
    db: Session = Depends(get_db)
):
    officer = (
        db.query(Officer)
        .filter(Officer.user_id == user_id)
        .first()
    )

    if officer is None:
        raise HTTPException(
            status_code=404,
            detail="Officer profile not found"
        )

    return officer


# UPDATE OFFICER
@app.put(
    "/api/officers/{user_id}",
    response_model=OfficerResponse
)
def update_officer(
    user_id: int,
    officer_data: OfficerCreate,
    db: Session = Depends(get_db)
):
    officer = (
        db.query(Officer)
        .filter(Officer.user_id == user_id)
        .first()
    )

    if officer is None:
        raise HTTPException(
            status_code=404,
            detail="Officer profile not found"
        )

    if officer_data.user_id != user_id:
        raise HTTPException(
            status_code=400,
            detail="user_id in request body must match the URL user_id"
        )

    officer.department = officer_data.department
    officer.designation = officer_data.designation

    db.commit()
    db.refresh(officer)

    return officer


# DELETE OFFICER
@app.delete("/api/officers/{user_id}")
def delete_officer(
    user_id: int,
    db: Session = Depends(get_db)
):
    officer = (
        db.query(Officer)
        .filter(Officer.user_id == user_id)
        .first()
    )

    if officer is None:
        raise HTTPException(
            status_code=404,
            detail="Officer profile not found"
        )

    db.delete(officer)
    db.commit()

    return {
        "message": "Officer profile deleted successfully"
    }
# =========================================================
# CONTRACTOR APIs
# =========================================================

# CREATE CONTRACTOR
@app.post(
    "/api/contractors",
    response_model=ContractorResponse
)
def create_contractor(
    contractor_data: ContractorCreate,
    db: Session = Depends(get_db)
):
    # Check whether user exists
    user = (
        db.query(User)
        .filter(User.id == contractor_data.user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Check whether contractor profile already exists
    existing_contractor = (
        db.query(Contractor)
        .filter(
            Contractor.user_id == contractor_data.user_id
        )
        .first()
    )

    if existing_contractor is not None:
        raise HTTPException(
            status_code=400,
            detail="Contractor profile already exists for this user"
        )

    # Check unique license number
    existing_license = (
        db.query(Contractor)
        .filter(
            Contractor.license_no == contractor_data.license_no
        )
        .first()
    )

    if existing_license is not None:
        raise HTTPException(
            status_code=400,
            detail="License number already registered"
        )

    contractor = Contractor(
        user_id=contractor_data.user_id,
        company_name=contractor_data.company_name,
        license_no=contractor_data.license_no,
        address=contractor_data.address
    )

    db.add(contractor)
    db.commit()
    db.refresh(contractor)

    return contractor


# GET ALL CONTRACTORS
@app.get(
    "/api/contractors",
    response_model=list[ContractorResponse]
)
def get_contractors(
    db: Session = Depends(get_db)
):
    return db.query(Contractor).all()


# GET ONE CONTRACTOR
@app.get(
    "/api/contractors/{user_id}",
    response_model=ContractorResponse
)
def get_contractor(
    user_id: int,
    db: Session = Depends(get_db)
):
    contractor = (
        db.query(Contractor)
        .filter(Contractor.user_id == user_id)
        .first()
    )

    if contractor is None:
        raise HTTPException(
            status_code=404,
            detail="Contractor profile not found"
        )

    return contractor


# UPDATE CONTRACTOR
@app.put(
    "/api/contractors/{user_id}",
    response_model=ContractorResponse
)
def update_contractor(
    user_id: int,
    contractor_data: ContractorCreate,
    db: Session = Depends(get_db)
):
    contractor = (
        db.query(Contractor)
        .filter(Contractor.user_id == user_id)
        .first()
    )

    if contractor is None:
        raise HTTPException(
            status_code=404,
            detail="Contractor profile not found"
        )

    if contractor_data.user_id != user_id:
        raise HTTPException(
            status_code=400,
            detail="user_id in request body must match the URL user_id"
        )

    # Check whether another contractor uses this license
    existing_license = (
        db.query(Contractor)
        .filter(
            Contractor.license_no == contractor_data.license_no,
            Contractor.user_id != user_id
        )
        .first()
    )

    if existing_license is not None:
        raise HTTPException(
            status_code=400,
            detail="License number already registered"
        )

    contractor.company_name = contractor_data.company_name
    contractor.license_no = contractor_data.license_no
    contractor.address = contractor_data.address

    db.commit()
    db.refresh(contractor)

    return contractor


# DELETE CONTRACTOR
@app.delete("/api/contractors/{user_id}")
def delete_contractor(
    user_id: int,
    db: Session = Depends(get_db)
):
    contractor = (
        db.query(Contractor)
        .filter(Contractor.user_id == user_id)
        .first()
    )

    if contractor is None:
        raise HTTPException(
            status_code=404,
            detail="Contractor profile not found"
        )

    db.delete(contractor)
    db.commit()

    return {
        "message": "Contractor profile deleted successfully"
    }

# =========================================================
# LOCATION APIs
# =========================================================

# CREATE LOCATION
@app.post(
    "/api/locations",
    response_model=LocationResponse
)
def create_location(
    location_data: LocationCreate,
    db: Session = Depends(get_db)
):
    existing_location = (
        db.query(Location)
        .filter(
            Location.area_name == location_data.area_name,
            Location.ward == location_data.ward
        )
        .first()
    )

    if existing_location is not None:
        raise HTTPException(
            status_code=400,
            detail="Location with this area and ward already exists"
        )

    location = Location(
        area_name=location_data.area_name,
        ward=location_data.ward,
        pincode=location_data.pincode
    )

    db.add(location)
    db.commit()
    db.refresh(location)

    return location


# GET ALL LOCATIONS
@app.get(
    "/api/locations",
    response_model=list[LocationResponse]
)
def get_locations(
    db: Session = Depends(get_db)
):
    return db.query(Location).all()


# GET ONE LOCATION
@app.get(
    "/api/locations/{location_id}",
    response_model=LocationResponse
)
def get_location(
    location_id: int,
    db: Session = Depends(get_db)
):
    location = (
        db.query(Location)
        .filter(Location.id == location_id)
        .first()
    )

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found"
        )

    return location


# UPDATE LOCATION
@app.put(
    "/api/locations/{location_id}",
    response_model=LocationResponse
)
def update_location(
    location_id: int,
    location_data: LocationCreate,
    db: Session = Depends(get_db)
):
    location = (
        db.query(Location)
        .filter(Location.id == location_id)
        .first()
    )

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found"
        )

    # Check composite unique constraint
    existing_location = (
        db.query(Location)
        .filter(
            Location.area_name == location_data.area_name,
            Location.ward == location_data.ward,
            Location.id != location_id
        )
        .first()
    )

    if existing_location is not None:
        raise HTTPException(
            status_code=400,
            detail="Location with this area and ward already exists"
        )

    location.area_name = location_data.area_name
    location.ward = location_data.ward
    location.pincode = location_data.pincode

    db.commit()
    db.refresh(location)

    return location


# DELETE LOCATION
@app.delete("/api/locations/{location_id}")
def delete_location(
    location_id: int,
    db: Session = Depends(get_db)
):
    location = (
        db.query(Location)
        .filter(Location.id == location_id)
        .first()
    )

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found"
        )

    db.delete(location)
    db.commit()

    return {
        "message": "Location deleted successfully"
    }

# =========================================================
# ROAD APIs
# =========================================================

# CREATE ROAD
@app.post(
    "/api/roads",
    response_model=RoadResponse
)
def create_road(
    road_data: RoadCreate,
    db: Session = Depends(get_db)
):
    # Check whether location exists
    location = (
        db.query(Location)
        .filter(Location.id == road_data.location_id)
        .first()
    )

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found"
        )

    road = Road(
        location_id=road_data.location_id,
        name=road_data.name,
        length_km=road_data.length_km,
        width_m=road_data.width_m,
        road_condition=road_data.road_condition,
        last_maintained_date=road_data.last_maintained_date
    )

    db.add(road)
    db.commit()
    db.refresh(road)

    return road


# GET ALL ROADS
@app.get(
    "/api/roads",
    response_model=list[RoadResponse]
)
def get_roads(
    db: Session = Depends(get_db)
):
    return db.query(Road).all()


# GET ONE ROAD
@app.get(
    "/api/roads/{road_id}",
    response_model=RoadResponse
)
def get_road(
    road_id: int,
    db: Session = Depends(get_db)
):
    road = (
        db.query(Road)
        .filter(Road.id == road_id)
        .first()
    )

    if road is None:
        raise HTTPException(
            status_code=404,
            detail="Road not found"
        )

    return road


# UPDATE ROAD
@app.put(
    "/api/roads/{road_id}",
    response_model=RoadResponse
)
def update_road(
    road_id: int,
    road_data: RoadCreate,
    db: Session = Depends(get_db)
):
    road = (
        db.query(Road)
        .filter(Road.id == road_id)
        .first()
    )

    if road is None:
        raise HTTPException(
            status_code=404,
            detail="Road not found"
        )

    # Check location exists
    location = (
        db.query(Location)
        .filter(Location.id == road_data.location_id)
        .first()
    )

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found"
        )

    road.location_id = road_data.location_id
    road.name = road_data.name
    road.length_km = road_data.length_km
    road.width_m = road_data.width_m
    road.road_condition = road_data.road_condition
    road.last_maintained_date = road_data.last_maintained_date

    db.commit()
    db.refresh(road)

    return road


# DELETE ROAD
@app.delete("/api/roads/{road_id}")
def delete_road(
    road_id: int,
    db: Session = Depends(get_db)
):
    road = (
        db.query(Road)
        .filter(Road.id == road_id)
        .first()
    )

    if road is None:
        raise HTTPException(
            status_code=404,
            detail="Road not found"
        )

    db.delete(road)
    db.commit()

    return {
        "message": "Road deleted successfully"
    }

# =========================================================
# PIPELINE APIs
# =========================================================

# CREATE PIPELINE
@app.post(
    "/api/pipelines",
    response_model=PipelineResponse
)
def create_pipeline(
    pipeline_data: PipelineCreate,
    db: Session = Depends(get_db)
):
    # Check whether location exists
    location = (
        db.query(Location)
        .filter(Location.id == pipeline_data.location_id)
        .first()
    )

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found"
        )

    pipeline = Pipeline(
        location_id=pipeline_data.location_id,
        name=pipeline_data.name,
        pipeline_type=pipeline_data.pipeline_type,
        length_km=pipeline_data.length_km,
        status=pipeline_data.status,
        installed_year=pipeline_data.installed_year
    )

    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)

    return pipeline


# GET ALL PIPELINES
@app.get(
    "/api/pipelines",
    response_model=list[PipelineResponse]
)
def get_pipelines(
    db: Session = Depends(get_db)
):
    return db.query(Pipeline).all()


# GET ONE PIPELINE
@app.get(
    "/api/pipelines/{pipeline_id}",
    response_model=PipelineResponse
)
def get_pipeline(
    pipeline_id: int,
    db: Session = Depends(get_db)
):
    pipeline = (
        db.query(Pipeline)
        .filter(Pipeline.id == pipeline_id)
        .first()
    )

    if pipeline is None:
        raise HTTPException(
            status_code=404,
            detail="Pipeline not found"
        )

    return pipeline


# UPDATE PIPELINE
@app.put(
    "/api/pipelines/{pipeline_id}",
    response_model=PipelineResponse
)
def update_pipeline(
    pipeline_id: int,
    pipeline_data: PipelineCreate,
    db: Session = Depends(get_db)
):
    pipeline = (
        db.query(Pipeline)
        .filter(Pipeline.id == pipeline_id)
        .first()
    )

    if pipeline is None:
        raise HTTPException(
            status_code=404,
            detail="Pipeline not found"
        )

    # Check location exists
    location = (
        db.query(Location)
        .filter(Location.id == pipeline_data.location_id)
        .first()
    )

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found"
        )

    pipeline.location_id = pipeline_data.location_id
    pipeline.name = pipeline_data.name
    pipeline.pipeline_type = pipeline_data.pipeline_type
    pipeline.length_km = pipeline_data.length_km
    pipeline.status = pipeline_data.status
    pipeline.installed_year = pipeline_data.installed_year

    db.commit()
    db.refresh(pipeline)

    return pipeline


# DELETE PIPELINE
@app.delete("/api/pipelines/{pipeline_id}")
def delete_pipeline(
    pipeline_id: int,
    db: Session = Depends(get_db)
):
    pipeline = (
        db.query(Pipeline)
        .filter(Pipeline.id == pipeline_id)
        .first()
    )

    if pipeline is None:
        raise HTTPException(
            status_code=404,
            detail="Pipeline not found"
        )

    db.delete(pipeline)
    db.commit()

    return {
        "message": "Pipeline deleted successfully"
    }

# =========================================================
# PROJECT APIs
# =========================================================

# CREATE PROJECT
@app.post(
    "/api/projects",
    response_model=ProjectResponse
)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db)
):
    # Check location
    location = (
        db.query(Location)
        .filter(Location.id == project_data.location_id)
        .first()
    )

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found"
        )

    # Check road if provided
    if project_data.road_id is not None:
        road = (
            db.query(Road)
            .filter(Road.id == project_data.road_id)
            .first()
        )

        if road is None:
            raise HTTPException(
                status_code=404,
                detail="Road not found"
            )

    # Check pipeline if provided
    if project_data.pipeline_id is not None:
        pipeline = (
            db.query(Pipeline)
            .filter(Pipeline.id == project_data.pipeline_id)
            .first()
        )

        if pipeline is None:
            raise HTTPException(
                status_code=404,
                detail="Pipeline not found"
            )

    # Check officer
    officer = (
        db.query(User)
        .filter(
            User.id == project_data.officer_id,
            User.role == "OFFICER"
        )
        .first()
    )

    if officer is None:
        raise HTTPException(
            status_code=404,
            detail="Officer user not found"
        )

    # Check contractor
    contractor = (
        db.query(User)
        .filter(
            User.id == project_data.contractor_id,
            User.role == "CONTRACTOR"
        )
        .first()
    )

    if contractor is None:
        raise HTTPException(
            status_code=404,
            detail="Contractor user not found"
        )

    project = Project(
        title=project_data.title,
        description=project_data.description,
        location_id=project_data.location_id,
        road_id=project_data.road_id,
        pipeline_id=project_data.pipeline_id,
        officer_id=project_data.officer_id,
        contractor_id=project_data.contractor_id,
        budget=project_data.budget,
        start_date=project_data.start_date,
        expected_completion_date=project_data.expected_completion_date,
        actual_completion_date=project_data.actual_completion_date,
        status=project_data.status,
        progress_percent=project_data.progress_percent,
        remarks=project_data.remarks
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


# GET ALL PROJECTS
@app.get(
    "/api/projects",
    response_model=list[ProjectResponse]
)
def get_projects(
    db: Session = Depends(get_db)
):
    return db.query(Project).all()


# GET ONE PROJECT
@app.get(
    "/api/projects/{project_id}",
    response_model=ProjectResponse
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    return project


# UPDATE PROJECT
@app.put(
    "/api/projects/{project_id}",
    response_model=ProjectResponse
)
def update_project(
    project_id: int,
    project_data: ProjectCreate,
    db: Session = Depends(get_db)
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    # Validate location
    location = (
        db.query(Location)
        .filter(Location.id == project_data.location_id)
        .first()
    )

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found"
        )

    # Validate road
    if project_data.road_id is not None:
        road = (
            db.query(Road)
            .filter(Road.id == project_data.road_id)
            .first()
        )

        if road is None:
            raise HTTPException(
                status_code=404,
                detail="Road not found"
            )

    # Validate pipeline
    if project_data.pipeline_id is not None:
        pipeline = (
            db.query(Pipeline)
            .filter(Pipeline.id == project_data.pipeline_id)
            .first()
        )

        if pipeline is None:
            raise HTTPException(
                status_code=404,
                detail="Pipeline not found"
            )

    # Validate officer
    officer = (
        db.query(User)
        .filter(
            User.id == project_data.officer_id,
            User.role == "OFFICER"
        )
        .first()
    )

    if officer is None:
        raise HTTPException(
            status_code=404,
            detail="Officer user not found"
        )

    # Validate contractor
    contractor = (
        db.query(User)
        .filter(
            User.id == project_data.contractor_id,
            User.role == "CONTRACTOR"
        )
        .first()
    )

    if contractor is None:
        raise HTTPException(
            status_code=404,
            detail="Contractor user not found"
        )

    project.title = project_data.title
    project.description = project_data.description
    project.location_id = project_data.location_id
    project.road_id = project_data.road_id
    project.pipeline_id = project_data.pipeline_id
    project.officer_id = project_data.officer_id
    project.contractor_id = project_data.contractor_id
    project.budget = project_data.budget
    project.start_date = project_data.start_date
    project.expected_completion_date = project_data.expected_completion_date
    project.actual_completion_date = project_data.actual_completion_date
    project.status = project_data.status
    project.progress_percent = project_data.progress_percent
    project.remarks = project_data.remarks

    db.commit()
    db.refresh(project)

    return project


# DELETE PROJECT
@app.delete("/api/projects/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    db.delete(project)
    db.commit()

    return {
        "message": "Project deleted successfully"
    }

# =========================================================
# PROJECT PROGRESS APIs
# =========================================================

# CREATE PROJECT PROGRESS
@app.post(
    "/api/project-progress",
    response_model=ProjectProgressResponse
)
def create_project_progress(
    progress_data: ProjectProgressCreate,
    db: Session = Depends(get_db)
):
    # Check project exists
    project = (
        db.query(Project)
        .filter(Project.id == progress_data.project_id)
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    # Check updater exists
    updater = (
        db.query(User)
        .filter(User.id == progress_data.updated_by)
        .first()
    )

    if updater is None:
        raise HTTPException(
            status_code=404,
            detail="User who updated progress not found"
        )

    progress = ProjectProgress(
        project_id=progress_data.project_id,
        progress_percent=progress_data.progress_percent,
        progress_date=progress_data.progress_date,
        remarks=progress_data.remarks,
        updated_by=progress_data.updated_by
    )

    db.add(progress)
    db.commit()
    db.refresh(progress)

    return progress


# GET ALL PROJECT PROGRESS RECORDS
@app.get(
    "/api/project-progress",
    response_model=list[ProjectProgressResponse]
)
def get_project_progress(
    db: Session = Depends(get_db)
):
    return db.query(ProjectProgress).all()


# GET ONE PROJECT PROGRESS RECORD
@app.get(
    "/api/project-progress/{progress_id}",
    response_model=ProjectProgressResponse
)
def get_project_progress_record(
    progress_id: int,
    db: Session = Depends(get_db)
):
    progress = (
        db.query(ProjectProgress)
        .filter(ProjectProgress.id == progress_id)
        .first()
    )

    if progress is None:
        raise HTTPException(
            status_code=404,
            detail="Project progress record not found"
        )

    return progress


# UPDATE PROJECT PROGRESS
@app.put(
    "/api/project-progress/{progress_id}",
    response_model=ProjectProgressResponse
)
def update_project_progress(
    progress_id: int,
    progress_data: ProjectProgressCreate,
    db: Session = Depends(get_db)
):
    progress = (
        db.query(ProjectProgress)
        .filter(ProjectProgress.id == progress_id)
        .first()
    )

    if progress is None:
        raise HTTPException(
            status_code=404,
            detail="Project progress record not found"
        )

    # Check project exists
    project = (
        db.query(Project)
        .filter(Project.id == progress_data.project_id)
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    # Check updater exists
    updater = (
        db.query(User)
        .filter(User.id == progress_data.updated_by)
        .first()
    )

    if updater is None:
        raise HTTPException(
            status_code=404,
            detail="User who updated progress not found"
        )

    progress.project_id = progress_data.project_id
    progress.progress_percent = progress_data.progress_percent
    progress.progress_date = progress_data.progress_date
    progress.remarks = progress_data.remarks
    progress.updated_by = progress_data.updated_by

    db.commit()
    db.refresh(progress)

    return progress


# DELETE PROJECT PROGRESS
@app.delete("/api/project-progress/{progress_id}")
def delete_project_progress(
    progress_id: int,
    db: Session = Depends(get_db)
):
    progress = (
        db.query(ProjectProgress)
        .filter(ProjectProgress.id == progress_id)
        .first()
    )

    if progress is None:
        raise HTTPException(
            status_code=404,
            detail="Project progress record not found"
        )

    db.delete(progress)
    db.commit()

    return {
        "message": "Project progress deleted successfully"
    }

# =========================================================
# PAYMENT APIs
# =========================================================

# CREATE PAYMENT
@app.post(
    "/api/payments",
    response_model=PaymentResponse
)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db)
):
    # Check project exists
    project = (
        db.query(Project)
        .filter(Project.id == payment_data.project_id)
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    # Check contractor exists and has CONTRACTOR role
    contractor = (
        db.query(User)
        .filter(
            User.id == payment_data.contractor_id,
            User.role == "CONTRACTOR"
        )
        .first()
    )

    if contractor is None:
        raise HTTPException(
            status_code=404,
            detail="Contractor user not found"
        )

    payment = Payment(
        project_id=payment_data.project_id,
        contractor_id=payment_data.contractor_id,
        amount=payment_data.amount,
        payment_date=payment_data.payment_date,
        status=payment_data.status,
        description=payment_data.description
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


# GET ALL PAYMENTS
@app.get(
    "/api/payments",
    response_model=list[PaymentResponse]
)
def get_payments(
    db: Session = Depends(get_db)
):
    return db.query(Payment).all()


# GET ONE PAYMENT
@app.get(
    "/api/payments/{payment_id}",
    response_model=PaymentResponse
)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db)
):
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id)
        .first()
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    return payment


# UPDATE PAYMENT
@app.put(
    "/api/payments/{payment_id}",
    response_model=PaymentResponse
)
def update_payment(
    payment_id: int,
    payment_data: PaymentCreate,
    db: Session = Depends(get_db)
):
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id)
        .first()
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    # Check project
    project = (
        db.query(Project)
        .filter(Project.id == payment_data.project_id)
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    # Check contractor
    contractor = (
        db.query(User)
        .filter(
            User.id == payment_data.contractor_id,
            User.role == "CONTRACTOR"
        )
        .first()
    )

    if contractor is None:
        raise HTTPException(
            status_code=404,
            detail="Contractor user not found"
        )

    payment.project_id = payment_data.project_id
    payment.contractor_id = payment_data.contractor_id
    payment.amount = payment_data.amount
    payment.payment_date = payment_data.payment_date
    payment.status = payment_data.status
    payment.description = payment_data.description

    db.commit()
    db.refresh(payment)

    return payment


# DELETE PAYMENT
@app.delete("/api/payments/{payment_id}")
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db)
):
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id)
        .first()
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    db.delete(payment)
    db.commit()

    return {
        "message": "Payment deleted successfully"
    }

# =========================================================
# MAINTENANCE APIs
# =========================================================

# CREATE MAINTENANCE
@app.post(
    "/api/maintenance",
    response_model=MaintenanceResponse
)
def create_maintenance(
    maintenance_data: MaintenanceCreate,
    db: Session = Depends(get_db)
):
    # At least road OR pipeline must be provided
    if (
        maintenance_data.road_id is None
        and maintenance_data.pipeline_id is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Either road_id or pipeline_id must be provided"
        )

    # Check project if provided
    if maintenance_data.project_id is not None:
        project = (
            db.query(Project)
            .filter(Project.id == maintenance_data.project_id)
            .first()
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

    # Check road if provided
    if maintenance_data.road_id is not None:
        road = (
            db.query(Road)
            .filter(Road.id == maintenance_data.road_id)
            .first()
        )

        if road is None:
            raise HTTPException(
                status_code=404,
                detail="Road not found"
            )

    # Check pipeline if provided
    if maintenance_data.pipeline_id is not None:
        pipeline = (
            db.query(Pipeline)
            .filter(Pipeline.id == maintenance_data.pipeline_id)
            .first()
        )

        if pipeline is None:
            raise HTTPException(
                status_code=404,
                detail="Pipeline not found"
            )

    # Check contractor
    contractor = (
        db.query(User)
        .filter(
            User.id == maintenance_data.assigned_contractor_id,
            User.role == "CONTRACTOR"
        )
        .first()
    )

    if contractor is None:
        raise HTTPException(
            status_code=404,
            detail="Contractor user not found"
        )

    # Check officer
    officer = (
        db.query(User)
        .filter(
            User.id == maintenance_data.assigned_officer_id,
            User.role == "OFFICER"
        )
        .first()
    )

    if officer is None:
        raise HTTPException(
            status_code=404,
            detail="Officer user not found"
        )

    maintenance = Maintenance(
        project_id=maintenance_data.project_id,
        road_id=maintenance_data.road_id,
        pipeline_id=maintenance_data.pipeline_id,
        description=maintenance_data.description,
        status=maintenance_data.status,
        maintenance_date=maintenance_data.maintenance_date,
        assigned_contractor_id=maintenance_data.assigned_contractor_id,
        assigned_officer_id=maintenance_data.assigned_officer_id
    )

    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)

    return maintenance


# GET ALL MAINTENANCE
@app.get(
    "/api/maintenance",
    response_model=list[MaintenanceResponse]
)
def get_maintenance(
    db: Session = Depends(get_db)
):
    return db.query(Maintenance).all()


# GET ONE MAINTENANCE
@app.get(
    "/api/maintenance/{maintenance_id}",
    response_model=MaintenanceResponse
)
def get_maintenance_record(
    maintenance_id: int,
    db: Session = Depends(get_db)
):
    maintenance = (
        db.query(Maintenance)
        .filter(Maintenance.id == maintenance_id)
        .first()
    )

    if maintenance is None:
        raise HTTPException(
            status_code=404,
            detail="Maintenance record not found"
        )

    return maintenance


# UPDATE MAINTENANCE
@app.put(
    "/api/maintenance/{maintenance_id}",
    response_model=MaintenanceResponse
)
def update_maintenance(
    maintenance_id: int,
    maintenance_data: MaintenanceCreate,
    db: Session = Depends(get_db)
):
    maintenance = (
        db.query(Maintenance)
        .filter(Maintenance.id == maintenance_id)
        .first()
    )

    if maintenance is None:
        raise HTTPException(
            status_code=404,
            detail="Maintenance record not found"
        )

    if (
        maintenance_data.road_id is None
        and maintenance_data.pipeline_id is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Either road_id or pipeline_id must be provided"
        )

    # Validate project
    if maintenance_data.project_id is not None:
        project = (
            db.query(Project)
            .filter(Project.id == maintenance_data.project_id)
            .first()
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

    # Validate road
    if maintenance_data.road_id is not None:
        road = (
            db.query(Road)
            .filter(Road.id == maintenance_data.road_id)
            .first()
        )

        if road is None:
            raise HTTPException(
                status_code=404,
                detail="Road not found"
            )

    # Validate pipeline
    if maintenance_data.pipeline_id is not None:
        pipeline = (
            db.query(Pipeline)
            .filter(Pipeline.id == maintenance_data.pipeline_id)
            .first()
        )

        if pipeline is None:
            raise HTTPException(
                status_code=404,
                detail="Pipeline not found"
            )

    # Validate contractor
    contractor = (
        db.query(User)
        .filter(
            User.id == maintenance_data.assigned_contractor_id,
            User.role == "CONTRACTOR"
        )
        .first()
    )

    if contractor is None:
        raise HTTPException(
            status_code=404,
            detail="Contractor user not found"
        )

    # Validate officer
    officer = (
        db.query(User)
        .filter(
            User.id == maintenance_data.assigned_officer_id,
            User.role == "OFFICER"
        )
        .first()
    )

    if officer is None:
        raise HTTPException(
            status_code=404,
            detail="Officer user not found"
        )

    maintenance.project_id = maintenance_data.project_id
    maintenance.road_id = maintenance_data.road_id
    maintenance.pipeline_id = maintenance_data.pipeline_id
    maintenance.description = maintenance_data.description
    maintenance.status = maintenance_data.status
    maintenance.maintenance_date = maintenance_data.maintenance_date
    maintenance.assigned_contractor_id = (
        maintenance_data.assigned_contractor_id
    )
    maintenance.assigned_officer_id = (
        maintenance_data.assigned_officer_id
    )

    db.commit()
    db.refresh(maintenance)

    return maintenance


# DELETE MAINTENANCE
@app.delete("/api/maintenance/{maintenance_id}")
def delete_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db)
):
    maintenance = (
        db.query(Maintenance)
        .filter(Maintenance.id == maintenance_id)
        .first()
    )

    if maintenance is None:
        raise HTTPException(
            status_code=404,
            detail="Maintenance record not found"
        )

    db.delete(maintenance)
    db.commit()

    return {
        "message": "Maintenance record deleted successfully"
    }# =========================================================
# COMPLAINT APIs
# =========================================================

# CREATE COMPLAINT
@app.post(
    "/api/complaints",
    response_model=ComplaintResponse
)
def create_complaint(
    complaint_data: ComplaintCreate,
    db: Session = Depends(get_db)
):
    # Check citizen
    citizen = (
        db.query(User)
        .filter(
            User.id == complaint_data.citizen_id,
            User.role == "CITIZEN"
        )
        .first()
    )

    if citizen is None:
        raise HTTPException(
            status_code=404,
            detail="Citizen user not found"
        )

    # Check location
    location = (
        db.query(Location)
        .filter(Location.id == complaint_data.location_id)
        .first()
    )

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found"
        )

    # Check assigned officer if provided
    if complaint_data.assigned_officer_id is not None:
        officer = (
            db.query(User)
            .filter(
                User.id == complaint_data.assigned_officer_id,
                User.role == "OFFICER"
            )
            .first()
        )

        if officer is None:
            raise HTTPException(
                status_code=404,
                detail="Assigned officer not found"
            )

    complaint = Complaint(
        citizen_id=complaint_data.citizen_id,
        title=complaint_data.title,
        description=complaint_data.description,
        category=complaint_data.category,
        location_id=complaint_data.location_id,
        complaint_date=complaint_data.complaint_date,
        status=complaint_data.status,
        assigned_officer_id=complaint_data.assigned_officer_id
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return complaint


# GET ALL COMPLAINTS
@app.get(
    "/api/complaints",
    response_model=list[ComplaintResponse]
)
def get_complaints(
    db: Session = Depends(get_db)
):
    return db.query(Complaint).all()


# GET ONE COMPLAINT
@app.get(
    "/api/complaints/{complaint_id}",
    response_model=ComplaintResponse
)
def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db)
):
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == complaint_id)
        .first()
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    return complaint


# UPDATE COMPLAINT
@app.put(
    "/api/complaints/{complaint_id}",
    response_model=ComplaintResponse
)
def update_complaint(
    complaint_id: int,
    complaint_data: ComplaintCreate,
    db: Session = Depends(get_db)
):
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == complaint_id)
        .first()
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    # Validate citizen
    citizen = (
        db.query(User)
        .filter(
            User.id == complaint_data.citizen_id,
            User.role == "CITIZEN"
        )
        .first()
    )

    if citizen is None:
        raise HTTPException(
            status_code=404,
            detail="Citizen user not found"
        )

    # Validate location
    location = (
        db.query(Location)
        .filter(Location.id == complaint_data.location_id)
        .first()
    )

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found"
        )

    # Validate officer if provided
    if complaint_data.assigned_officer_id is not None:
        officer = (
            db.query(User)
            .filter(
                User.id == complaint_data.assigned_officer_id,
                User.role == "OFFICER"
            )
            .first()
        )

        if officer is None:
            raise HTTPException(
                status_code=404,
                detail="Assigned officer not found"
            )

    complaint.citizen_id = complaint_data.citizen_id
    complaint.title = complaint_data.title
    complaint.description = complaint_data.description
    complaint.category = complaint_data.category
    complaint.location_id = complaint_data.location_id
    complaint.complaint_date = complaint_data.complaint_date
    complaint.status = complaint_data.status
    complaint.assigned_officer_id = complaint_data.assigned_officer_id

    db.commit()
    db.refresh(complaint)

    return complaint


# DELETE COMPLAINT
@app.delete("/api/complaints/{complaint_id}")
def delete_complaint(
    complaint_id: int,
    db: Session = Depends(get_db)
):
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == complaint_id)
        .first()
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    db.delete(complaint)
    db.commit()

    return {
        "message": "Complaint deleted successfully"
    }

# =========================================================
# COMPLAINT STATUS HISTORY APIs
# =========================================================

# CREATE STATUS HISTORY
@app.post(
    "/api/complaint-status-history",
    response_model=ComplaintStatusHistoryResponse
)
def create_complaint_status_history(
    history_data: ComplaintStatusHistoryCreate,
    db: Session = Depends(get_db)
):
    # Check complaint exists
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == history_data.complaint_id)
        .first()
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    # Check user exists
    user = (
        db.query(User)
        .filter(User.id == history_data.changed_by)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    history = ComplaintStatusHistory(
        complaint_id=history_data.complaint_id,
        old_status=history_data.old_status,
        new_status=history_data.new_status,
        changed_by=history_data.changed_by,
        remarks=history_data.remarks
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return history


# GET ALL STATUS HISTORY
@app.get(
    "/api/complaint-status-history",
    response_model=list[ComplaintStatusHistoryResponse]
)
def get_complaint_status_history(
    db: Session = Depends(get_db)
):
    return db.query(ComplaintStatusHistory).all()


# GET ONE STATUS HISTORY
@app.get(
    "/api/complaint-status-history/{history_id}",
    response_model=ComplaintStatusHistoryResponse
)
def get_complaint_status_history_record(
    history_id: int,
    db: Session = Depends(get_db)
):
    history = (
        db.query(ComplaintStatusHistory)
        .filter(ComplaintStatusHistory.id == history_id)
        .first()
    )

    if history is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint status history record not found"
        )

    return history


# GET HISTORY FOR ONE COMPLAINT
@app.get(
    "/api/complaints/{complaint_id}/status-history",
    response_model=list[ComplaintStatusHistoryResponse]
)
def get_complaint_history(
    complaint_id: int,
    db: Session = Depends(get_db)
):
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == complaint_id)
        .first()
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    return (
        db.query(ComplaintStatusHistory)
        .filter(
            ComplaintStatusHistory.complaint_id == complaint_id
        )
        .order_by(
            ComplaintStatusHistory.changed_at.asc()
        )
        .all()
    )


# UPDATE STATUS HISTORY
@app.put(
    "/api/complaint-status-history/{history_id}",
    response_model=ComplaintStatusHistoryResponse
)
def update_complaint_status_history(
    history_id: int,
    history_data: ComplaintStatusHistoryCreate,
    db: Session = Depends(get_db)
):
    history = (
        db.query(ComplaintStatusHistory)
        .filter(ComplaintStatusHistory.id == history_id)
        .first()
    )

    if history is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint status history record not found"
        )

    # Check complaint
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == history_data.complaint_id)
        .first()
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    # Check user
    user = (
        db.query(User)
        .filter(User.id == history_data.changed_by)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    history.complaint_id = history_data.complaint_id
    history.old_status = history_data.old_status
    history.new_status = history_data.new_status
    history.changed_by = history_data.changed_by
    history.remarks = history_data.remarks

    db.commit()
    db.refresh(history)

    return history


# DELETE STATUS HISTORY
@app.delete("/api/complaint-status-history/{history_id}")
def delete_complaint_status_history(
    history_id: int,
    db: Session = Depends(get_db)
):
    history = (
        db.query(ComplaintStatusHistory)
        .filter(ComplaintStatusHistory.id == history_id)
        .first()
    )

    if history is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint status history record not found"
        )

    db.delete(history)
    db.commit()

    return {
        "message": "Complaint status history deleted successfully"
    }

# =========================================================
# FEEDBACK APIs
# =========================================================

# CREATE FEEDBACK
@app.post(
    "/api/feedback",
    response_model=FeedbackResponse
)
def create_feedback(
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db)
):
    # Check complaint exists
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == feedback_data.complaint_id)
        .first()
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    # Check citizen exists and has CITIZEN role
    citizen = (
        db.query(User)
        .filter(
            User.id == feedback_data.citizen_id,
            User.role == "CITIZEN"
        )
        .first()
    )

    if citizen is None:
        raise HTTPException(
            status_code=404,
            detail="Citizen user not found"
        )

    # Make sure this citizen actually owns the complaint
    if complaint.citizen_id != feedback_data.citizen_id:
        raise HTTPException(
            status_code=403,
            detail="Citizen can only give feedback for their own complaint"
        )

    # One feedback per complaint
    existing_feedback = (
        db.query(Feedback)
        .filter(
            Feedback.complaint_id == feedback_data.complaint_id
        )
        .first()
    )

    if existing_feedback is not None:
        raise HTTPException(
            status_code=400,
            detail="Feedback already exists for this complaint"
        )

    feedback = Feedback(
        complaint_id=feedback_data.complaint_id,
        citizen_id=feedback_data.citizen_id,
        rating=feedback_data.rating,
        comment=feedback_data.comment
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return feedback


# GET ALL FEEDBACK
@app.get(
    "/api/feedback",
    response_model=list[FeedbackResponse]
)
def get_feedback(
    db: Session = Depends(get_db)
):
    return db.query(Feedback).all()


# GET ONE FEEDBACK
@app.get(
    "/api/feedback/{feedback_id}",
    response_model=FeedbackResponse
)
def get_feedback_record(
    feedback_id: int,
    db: Session = Depends(get_db)
):
    feedback = (
        db.query(Feedback)
        .filter(Feedback.id == feedback_id)
        .first()
    )

    if feedback is None:
        raise HTTPException(
            status_code=404,
            detail="Feedback not found"
        )

    return feedback


# GET FEEDBACK FOR A COMPLAINT
@app.get(
    "/api/complaints/{complaint_id}/feedback",
    response_model=FeedbackResponse
)
def get_complaint_feedback(
    complaint_id: int,
    db: Session = Depends(get_db)
):
    feedback = (
        db.query(Feedback)
        .filter(Feedback.complaint_id == complaint_id)
        .first()
    )

    if feedback is None:
        raise HTTPException(
            status_code=404,
            detail="Feedback not found for this complaint"
        )

    return feedback


# UPDATE FEEDBACK
@app.put(
    "/api/feedback/{feedback_id}",
    response_model=FeedbackResponse
)
def update_feedback(
    feedback_id: int,
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db)
):
    feedback = (
        db.query(Feedback)
        .filter(Feedback.id == feedback_id)
        .first()
    )

    if feedback is None:
        raise HTTPException(
            status_code=404,
            detail="Feedback not found"
        )

    # Check complaint
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == feedback_data.complaint_id)
        .first()
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    # Check citizen
    citizen = (
        db.query(User)
        .filter(
            User.id == feedback_data.citizen_id,
            User.role == "CITIZEN"
        )
        .first()
    )

    if citizen is None:
        raise HTTPException(
            status_code=404,
            detail="Citizen user not found"
        )

    # Citizen must own the complaint
    if complaint.citizen_id != feedback_data.citizen_id:
        raise HTTPException(
            status_code=403,
            detail="Citizen can only give feedback for their own complaint"
        )

    # Check duplicate feedback if complaint is changed
    existing_feedback = (
        db.query(Feedback)
        .filter(
            Feedback.complaint_id == feedback_data.complaint_id,
            Feedback.id != feedback_id
        )
        .first()
    )

    if existing_feedback is not None:
        raise HTTPException(
            status_code=400,
            detail="Feedback already exists for this complaint"
        )

    feedback.complaint_id = feedback_data.complaint_id
    feedback.citizen_id = feedback_data.citizen_id
    feedback.rating = feedback_data.rating
    feedback.comment = feedback_data.comment

    db.commit()
    db.refresh(feedback)

    return feedback


# DELETE FEEDBACK
@app.delete("/api/feedback/{feedback_id}")
def delete_feedback(
    feedback_id: int,
    db: Session = Depends(get_db)
):
    feedback = (
        db.query(Feedback)
        .filter(Feedback.id == feedback_id)
        .first()
    )

    if feedback is None:
        raise HTTPException(
            status_code=404,
            detail="Feedback not found"
        )

    db.delete(feedback)
    db.commit()

    return {
        "message": "Feedback deleted successfully"
    }

# =========================================================
# ALERT APIs
# =========================================================

# CREATE ALERT
@app.post(
    "/api/alerts",
    response_model=AlertResponse
)
def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db)
):
    # Check creator exists
    creator = (
        db.query(User)
        .filter(User.id == alert_data.created_by)
        .first()
    )

    if creator is None:
        raise HTTPException(
            status_code=404,
            detail="Creator user not found"
        )

    alert = Alert(
        title=alert_data.title,
        message=alert_data.message,
        severity=alert_data.severity,
        audience=alert_data.audience,
        expires_at=alert_data.expires_at,
        created_by=alert_data.created_by
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert


# GET ALL ALERTS
@app.get(
    "/api/alerts",
    response_model=list[AlertResponse]
)
def get_alerts(
    db: Session = Depends(get_db)
):
    return db.query(Alert).all()


# GET ONE ALERT
@app.get(
    "/api/alerts/{alert_id}",
    response_model=AlertResponse
)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id)
        .first()
    )

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )

    return alert


# UPDATE ALERT
@app.put(
    "/api/alerts/{alert_id}",
    response_model=AlertResponse
)
def update_alert(
    alert_id: int,
    alert_data: AlertCreate,
    db: Session = Depends(get_db)
):
    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id)
        .first()
    )

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )

    # Check creator
    creator = (
        db.query(User)
        .filter(User.id == alert_data.created_by)
        .first()
    )

    if creator is None:
        raise HTTPException(
            status_code=404,
            detail="Creator user not found"
        )

    alert.title = alert_data.title
    alert.message = alert_data.message
    alert.severity = alert_data.severity
    alert.audience = alert_data.audience
    alert.expires_at = alert_data.expires_at
    alert.created_by = alert_data.created_by

    db.commit()
    db.refresh(alert)

    return alert


# DELETE ALERT
@app.delete("/api/alerts/{alert_id}")
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id)
        .first()
    )

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )

    db.delete(alert)
    db.commit()

    return {
        "message": "Alert deleted successfully"
    }