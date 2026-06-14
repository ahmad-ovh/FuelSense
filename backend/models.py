from sqlalchemy import Column, Integer, String, Float, ForeignKey
from .database import Base

class SessionStateModel(Base):
    __tablename__ = "session_state"

    session_id = Column(String, primary_key=True, index=True)
    status = Column(String, default="IDLE")  # IDLE, RUNNING, STOPPED, RESETTING
    active_scenario = Column(String, nullable=True)
    current_step = Column(Integer, default=0)
    start_timestamp = Column(Integer, nullable=True)


class TelemetryFrame(Base):
    __tablename__ = "telemetry_frame"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, index=True)
    timestamp = Column(Integer)
    speed_kmh = Column(Integer)
    rpm = Column(Integer)
    throttle_pct = Column(Integer)
    engine_load_pct = Column(Integer)
    fuel_level_pct = Column(Float)
    driving_mode = Column(String)
    fuel_burn_rate_lph = Column(Float)
