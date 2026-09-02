CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE admin_boundary (
    id UUID PRIMARY KEY,
    parent_boundary_id UUID NULL,
    name VARCHAR NOT NULL,
    boundary_type VARCHAR NOT NULL,
    geometry geometry(MultiPolygon,4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_admin_boundary_parent_boundary
        FOREIGN KEY (parent_boundary_id) REFERENCES admin_boundary (id)
);

CREATE TABLE data_source (
    id UUID PRIMARY KEY,
    provider VARCHAR NOT NULL,
    dataset VARCHAR NOT NULL,
    license VARCHAR NULL,
    fetch_time TIMESTAMPTZ NULL,
    freshness_class VARCHAR NULL
);

CREATE TABLE model_version (
    id UUID PRIMARY KEY,
    model_name VARCHAR NOT NULL,
    version VARCHAR NOT NULL,
    parameters JSONB NULL,
    validation_metrics JSONB NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE app_user (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    password_hash VARCHAR NOT NULL,
    active BOOLEAN NOT NULL,
    CONSTRAINT uq_app_user_email UNIQUE (email)
);

CREATE TABLE habitation (
    id UUID PRIMARY KEY,
    lgd_code VARCHAR NULL,
    admin_boundary_id UUID NOT NULL,
    name VARCHAR NOT NULL,
    geometry geometry(Polygon,4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_habitation_lgd_code UNIQUE (lgd_code),
    CONSTRAINT fk_habitation_admin_boundary
        FOREIGN KEY (admin_boundary_id) REFERENCES admin_boundary (id)
);

CREATE TABLE population (
    id UUID PRIMARY KEY,
    habitation_id UUID NOT NULL,
    population_count INTEGER NOT NULL,
    year INTEGER NOT NULL,
    source VARCHAR NULL,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_population_habitation
        FOREIGN KEY (habitation_id) REFERENCES habitation (id)
);

CREATE TABLE infrastructure (
    id UUID PRIMARY KEY,
    habitation_id UUID NOT NULL,
    infrastructure_type VARCHAR NOT NULL,
    status VARCHAR NULL,
    geometry geometry(Point,4326) NOT NULL,
    capacity INTEGER NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_infrastructure_habitation
        FOREIGN KEY (habitation_id) REFERENCES habitation (id)
);

CREATE TABLE vulnerability (
    id UUID PRIMARY KEY,
    habitation_id UUID NOT NULL,
    hvi_score DECIMAL NULL,
    exposure_score DECIMAL NULL,
    coping_capacity DECIMAL NULL,
    component_data JSONB NULL,
    assessment_year INTEGER NULL,
    data_source_id UUID NULL,
    CONSTRAINT fk_vulnerability_habitation
        FOREIGN KEY (habitation_id) REFERENCES habitation (id),
    CONSTRAINT fk_vulnerability_data_source
        FOREIGN KEY (data_source_id) REFERENCES data_source (id)
);

CREATE TABLE hazard_assessment (
    id UUID PRIMARY KEY,
    habitation_id UUID NOT NULL,
    hazard_type VARCHAR NOT NULL,
    susceptibility DECIMAL NULL,
    exposure DECIMAL NULL,
    confidence DECIMAL NULL,
    applicable BOOLEAN NOT NULL,
    assessment_time TIMESTAMPTZ NOT NULL,
    data_source_id UUID NULL,
    model_version_id UUID NULL,
    CONSTRAINT fk_hazard_assessment_habitation
        FOREIGN KEY (habitation_id) REFERENCES habitation (id),
    CONSTRAINT fk_hazard_assessment_data_source
        FOREIGN KEY (data_source_id) REFERENCES data_source (id),
    CONSTRAINT fk_hazard_assessment_model_version
        FOREIGN KEY (model_version_id) REFERENCES model_version (id)
);

CREATE TABLE risk_assessment (
    id UUID PRIMARY KEY,
    habitation_id UUID NOT NULL,
    risk_score DECIMAL NOT NULL,
    risk_band VARCHAR NOT NULL,
    priority VARCHAR NOT NULL,
    confidence DECIMAL NULL,
    assessment_time TIMESTAMPTZ NOT NULL,
    data_source_id UUID NULL,
    model_version_id UUID NULL,
    CONSTRAINT fk_risk_assessment_habitation
        FOREIGN KEY (habitation_id) REFERENCES habitation (id),
    CONSTRAINT fk_risk_assessment_data_source
        FOREIGN KEY (data_source_id) REFERENCES data_source (id),
    CONSTRAINT fk_risk_assessment_model_version
        FOREIGN KEY (model_version_id) REFERENCES model_version (id)
);

CREATE TABLE relocation_site (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    geometry geometry(Polygon,4326) NOT NULL,
    status VARCHAR NOT NULL,
    suitability_score DECIMAL NULL,
    data_source_id UUID NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_relocation_site_data_source
        FOREIGN KEY (data_source_id) REFERENCES data_source (id)
);

CREATE TABLE carrying_capacity (
    id UUID PRIMARY KEY,
    relocation_site_id UUID NOT NULL,
    total_capacity INTEGER NOT NULL,
    estimated_capacity INTEGER NULL,
    binding_sector VARCHAR NULL,
    calculated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_carrying_capacity_relocation_site
        FOREIGN KEY (relocation_site_id) REFERENCES relocation_site (id)
);

CREATE TABLE recommendation (
    id UUID PRIMARY KEY,
    habitation_id UUID NOT NULL,
    status VARCHAR NOT NULL,
    suitability_score DECIMAL NULL,
    allocated_population INTEGER NULL,
    split_required BOOLEAN NOT NULL,
    reason_codes JSONB NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_recommendation_habitation
        FOREIGN KEY (habitation_id) REFERENCES habitation (id)
);

CREATE TABLE recommendation_site (
    id UUID PRIMARY KEY,
    recommendation_id UUID NOT NULL,
    relocation_site_id UUID NOT NULL,
    allocation_population INTEGER NOT NULL,
    allocation_percentage DECIMAL NULL,
    rank INTEGER NULL,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_recommendation_site_recommendation
        FOREIGN KEY (recommendation_id) REFERENCES recommendation (id),
    CONSTRAINT fk_recommendation_site_relocation_site
        FOREIGN KEY (relocation_site_id) REFERENCES relocation_site (id)
);

CREATE TABLE scenario (
    id UUID PRIMARY KEY,
    habitation_id UUID NOT NULL,
    name VARCHAR NOT NULL,
    scenario_type VARCHAR NOT NULL,
    parameters JSONB NOT NULL,
    result_summary JSONB NULL,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_scenario_habitation
        FOREIGN KEY (habitation_id) REFERENCES habitation (id)
);

CREATE TABLE decision (
    id UUID PRIMARY KEY,
    recommendation_id UUID NOT NULL,
    officer_id UUID NOT NULL,
    decision VARCHAR NOT NULL,
    justification TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_decision_recommendation
        FOREIGN KEY (recommendation_id) REFERENCES recommendation (id),
    CONSTRAINT fk_decision_officer
        FOREIGN KEY (officer_id) REFERENCES app_user (id)
);

CREATE TABLE audit_log (
    id UUID PRIMARY KEY,
    actor_id UUID NULL,
    action VARCHAR NOT NULL,
    target_type VARCHAR NOT NULL,
    target_id UUID NULL,
    before_state JSONB NULL,
    after_state JSONB NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_audit_log_actor
        FOREIGN KEY (actor_id) REFERENCES app_user (id)
);

CREATE INDEX idx_admin_boundary_parent_boundary_id ON admin_boundary (parent_boundary_id);
CREATE INDEX idx_admin_boundary_geometry ON admin_boundary USING GIST (geometry);

CREATE INDEX idx_habitation_admin_boundary_id ON habitation (admin_boundary_id);
CREATE INDEX idx_habitation_geometry ON habitation USING GIST (geometry);

CREATE INDEX idx_population_habitation_id ON population (habitation_id);

CREATE INDEX idx_infrastructure_habitation_id ON infrastructure (habitation_id);
CREATE INDEX idx_infrastructure_geometry ON infrastructure USING GIST (geometry);

CREATE INDEX idx_vulnerability_habitation_id ON vulnerability (habitation_id);
CREATE INDEX idx_vulnerability_data_source_id ON vulnerability (data_source_id);

CREATE INDEX idx_hazard_assessment_habitation_id ON hazard_assessment (habitation_id);
CREATE INDEX idx_hazard_assessment_data_source_id ON hazard_assessment (data_source_id);
CREATE INDEX idx_hazard_assessment_model_version_id ON hazard_assessment (model_version_id);

CREATE INDEX idx_risk_assessment_habitation_id ON risk_assessment (habitation_id);
CREATE INDEX idx_risk_assessment_data_source_id ON risk_assessment (data_source_id);
CREATE INDEX idx_risk_assessment_model_version_id ON risk_assessment (model_version_id);

CREATE INDEX idx_relocation_site_data_source_id ON relocation_site (data_source_id);
CREATE INDEX idx_relocation_site_geometry ON relocation_site USING GIST (geometry);

CREATE INDEX idx_carrying_capacity_relocation_site_id ON carrying_capacity (relocation_site_id);

CREATE INDEX idx_recommendation_habitation_id ON recommendation (habitation_id);

CREATE INDEX idx_recommendation_site_recommendation_id ON recommendation_site (recommendation_id);
CREATE INDEX idx_recommendation_site_relocation_site_id ON recommendation_site (relocation_site_id);

CREATE INDEX idx_scenario_habitation_id ON scenario (habitation_id);

CREATE INDEX idx_decision_recommendation_id ON decision (recommendation_id);
CREATE INDEX idx_decision_officer_id ON decision (officer_id);

CREATE INDEX idx_audit_log_actor_id ON audit_log (actor_id);
