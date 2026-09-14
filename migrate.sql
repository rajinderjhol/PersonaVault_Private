BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 097f92621c9c

CREATE TABLE approval_requests (
    id SERIAL NOT NULL, 
    action VARCHAR, 
    resource_type VARCHAR, 
    resource_id INTEGER, 
    requester_id INTEGER, 
    approver_ids JSON, 
    status VARCHAR, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    approved_at TIMESTAMP WITHOUT TIME ZONE, 
    approved_by INTEGER, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_approval_requests_id ON approval_requests (id);

CREATE TABLE behaviour_packs (
    id VARCHAR NOT NULL, 
    name VARCHAR, 
    version VARCHAR, 
    domain VARCHAR, 
    description TEXT, 
    entities JSON, 
    events JSON, 
    decision_types JSON, 
    metrics JSON, 
    prompts JSON, 
    views JSON, 
    policies JSON, 
    temporal_patterns JSON, 
    evaluation_rules JSON, 
    is_active BOOLEAN, 
    installed_at TIMESTAMP WITHOUT TIME ZONE, 
    installed_by INTEGER, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_behaviour_packs_domain ON behaviour_packs (domain);

CREATE INDEX ix_behaviour_packs_id ON behaviour_packs (id);

CREATE INDEX ix_behaviour_packs_name ON behaviour_packs (name);

CREATE TABLE bulk_ingestion_jobs (
    id SERIAL NOT NULL, 
    job_id VARCHAR(64) NOT NULL, 
    folder_path VARCHAR(512) NOT NULL, 
    status VARCHAR(20), 
    total_files INTEGER, 
    successful_files INTEGER, 
    failed_files INTEGER, 
    error_message TEXT, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    completed_at TIMESTAMP WITHOUT TIME ZONE, 
    job_metadata JSON, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_bulk_ingestion_jobs_id ON bulk_ingestion_jobs (id);

CREATE UNIQUE INDEX ix_bulk_ingestion_jobs_job_id ON bulk_ingestion_jobs (job_id);

CREATE TABLE document_ingestion_jobs (
    id SERIAL NOT NULL, 
    job_id VARCHAR(64) NOT NULL, 
    filename VARCHAR(255) NOT NULL, 
    file_type VARCHAR(50) NOT NULL, 
    status VARCHAR(20), 
    total_blocks INTEGER, 
    qualified_blocks INTEGER, 
    error_message TEXT, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    completed_at TIMESTAMP WITHOUT TIME ZONE, 
    job_metadata JSON, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_document_ingestion_jobs_id ON document_ingestion_jobs (id);

CREATE UNIQUE INDEX ix_document_ingestion_jobs_job_id ON document_ingestion_jobs (job_id);

CREATE TABLE episodic_entries (
    id SERIAL NOT NULL, 
    user_id INTEGER, 
    query TEXT, 
    plan JSON, 
    results JSON, 
    answer TEXT, 
    evaluation JSON, 
    governance_receipt_id VARCHAR, 
    signature VARCHAR, 
    hitl_approved BOOLEAN, 
    user_feedback INTEGER, 
    timestamp TIMESTAMP WITHOUT TIME ZONE, 
    consolidated BOOLEAN, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_episodic_entries_governance_receipt_id ON episodic_entries (governance_receipt_id);

CREATE INDEX ix_episodic_entries_id ON episodic_entries (id);

CREATE INDEX ix_episodic_entries_user_id ON episodic_entries (user_id);

CREATE TABLE evidence_blocks (
    id SERIAL NOT NULL, 
    block_id VARCHAR(64) NOT NULL, 
    content TEXT NOT NULL, 
    content_hash VARCHAR(64) NOT NULL, 
    source VARCHAR(255) NOT NULL, 
    source_type VARCHAR(50) NOT NULL, 
    block_metadata JSON, 
    confidence FLOAT, 
    provenance_score FLOAT, 
    quality_score FLOAT, 
    is_qualified BOOLEAN, 
    tags JSON, 
    verifiable_attestation VARCHAR(255), 
    extracted_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_evidence_blocks_block_id ON evidence_blocks (block_id);

CREATE INDEX ix_evidence_blocks_id ON evidence_blocks (id);

CREATE TABLE organizations (
    id SERIAL NOT NULL, 
    name VARCHAR NOT NULL, 
    slug VARCHAR NOT NULL, 
    description TEXT, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    is_active BOOLEAN, 
    settings JSON, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_organizations_id ON organizations (id);

CREATE UNIQUE INDEX ix_organizations_slug ON organizations (slug);

CREATE TABLE pending_actions (
    id SERIAL NOT NULL, 
    agent_type VARCHAR, 
    query TEXT, 
    options JSON, 
    status VARCHAR, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    resolved_at TIMESTAMP WITHOUT TIME ZONE, 
    user_response TEXT, 
    vap_hash VARCHAR, 
    action_chain_id VARCHAR, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_pending_actions_id ON pending_actions (id);

CREATE INDEX ix_pending_actions_vap_hash ON pending_actions (vap_hash);

CREATE TABLE roles (
    id SERIAL NOT NULL, 
    name VARCHAR NOT NULL, 
    description TEXT, 
    permissions JSON, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    is_system BOOLEAN, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_roles_id ON roles (id);

CREATE UNIQUE INDEX ix_roles_name ON roles (name);

CREATE TABLE semantic_patterns (
    id SERIAL NOT NULL, 
    pattern_type VARCHAR, 
    trigger TEXT, 
    correction TEXT, 
    occurrence_count INTEGER, 
    success_count INTEGER, 
    weight FLOAT, 
    is_active BOOLEAN, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_semantic_patterns_id ON semantic_patterns (id);

CREATE INDEX ix_semantic_patterns_pattern_type ON semantic_patterns (pattern_type);

CREATE TABLE simulation_jobs (
    id SERIAL NOT NULL, 
    job_id VARCHAR(64) NOT NULL, 
    domain VARCHAR(50) NOT NULL, 
    params JSON NOT NULL, 
    status VARCHAR(20), 
    result_metrics JSON, 
    error_message TEXT, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    completed_at TIMESTAMP WITHOUT TIME ZONE, 
    attestation VARCHAR(255), 
    PRIMARY KEY (id)
);

CREATE INDEX ix_simulation_jobs_id ON simulation_jobs (id);

CREATE UNIQUE INDEX ix_simulation_jobs_job_id ON simulation_jobs (job_id);

CREATE TABLE system_configs (
    key VARCHAR NOT NULL, 
    value VARCHAR NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (key)
);

CREATE INDEX ix_system_configs_key ON system_configs (key);

CREATE TABLE users (
    id SERIAL NOT NULL, 
    username VARCHAR NOT NULL, 
    email VARCHAR NOT NULL, 
    hashed_password VARCHAR NOT NULL, 
    full_name VARCHAR, 
    role VARCHAR, 
    organization_id INTEGER, 
    is_active BOOLEAN, 
    sidebar_prefs JSON, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    last_login TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    UNIQUE (email), 
    UNIQUE (username)
);

CREATE TABLE ai_settings (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    profile_name VARCHAR NOT NULL, 
    provider_type VARCHAR NOT NULL, 
    model_name VARCHAR NOT NULL, 
    deployment_type VARCHAR, 
    parameters JSON, 
    is_active BOOLEAN, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_ai_settings_id ON ai_settings (id);

CREATE TABLE api_keys (
    id SERIAL NOT NULL, 
    key VARCHAR NOT NULL, 
    name VARCHAR NOT NULL, 
    user_id INTEGER, 
    organization_id INTEGER, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    expires_at TIMESTAMP WITHOUT TIME ZONE, 
    last_used TIMESTAMP WITHOUT TIME ZONE, 
    is_active BOOLEAN, 
    PRIMARY KEY (id), 
    FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_api_keys_id ON api_keys (id);

CREATE UNIQUE INDEX ix_api_keys_key ON api_keys (key);

CREATE TABLE audit_logs (
    id SERIAL NOT NULL, 
    user_id INTEGER, 
    action VARCHAR NOT NULL, 
    resource_type VARCHAR, 
    resource_id VARCHAR, 
    details TEXT, 
    ip_address VARCHAR, 
    user_agent VARCHAR, 
    timestamp TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_audit_logs_action ON audit_logs (action);

CREATE INDEX ix_audit_logs_id ON audit_logs (id);

CREATE INDEX ix_audit_logs_resource_type ON audit_logs (resource_type);

CREATE INDEX ix_audit_logs_timestamp ON audit_logs (timestamp);

CREATE TABLE chat_sessions (
    id SERIAL NOT NULL, 
    user_id INTEGER, 
    title VARCHAR, 
    pinned INTEGER, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_chat_sessions_id ON chat_sessions (id);

CREATE INDEX ix_chat_sessions_user_id ON chat_sessions (user_id);

CREATE TABLE intelligence_sources (
    id VARCHAR(36) NOT NULL, 
    user_id VARCHAR(36) NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    type VARCHAR(50) NOT NULL, 
    trust_score FLOAT NOT NULL, 
    trust_level VARCHAR(20) NOT NULL, 
    trust_history JSON NOT NULL, 
    contribution_metrics JSON NOT NULL, 
    memory_access JSON NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    last_contribution TIMESTAMP WITHOUT TIME ZONE, 
    registered_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    extra_metadata JSON NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_intelligence_sources_status ON intelligence_sources (status);

CREATE INDEX idx_intelligence_sources_trust_score ON intelligence_sources (trust_score);

CREATE INDEX idx_intelligence_sources_type ON intelligence_sources (type);

CREATE INDEX idx_intelligence_sources_user_id ON intelligence_sources (user_id);

CREATE TABLE iot_devices (
    id SERIAL NOT NULL, 
    device_id VARCHAR NOT NULL, 
    device_name VARCHAR, 
    device_type VARCHAR, 
    user_id INTEGER NOT NULL, 
    location VARCHAR, 
    status VARCHAR, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    last_seen TIMESTAMP WITHOUT TIME ZONE, 
    extra_data JSON, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE UNIQUE INDEX ix_iot_devices_device_id ON iot_devices (device_id);

CREATE INDEX ix_iot_devices_id ON iot_devices (id);

CREATE TABLE legal_matters (
    id SERIAL NOT NULL, 
    matter_number VARCHAR NOT NULL, 
    title VARCHAR NOT NULL, 
    description TEXT, 
    client_id INTEGER NOT NULL, 
    assigned_attorney_id INTEGER, 
    status VARCHAR, 
    priority VARCHAR, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(assigned_attorney_id) REFERENCES users (id), 
    FOREIGN KEY(client_id) REFERENCES users (id)
);

CREATE INDEX ix_legal_matters_id ON legal_matters (id);

CREATE UNIQUE INDEX ix_legal_matters_matter_number ON legal_matters (matter_number);

CREATE TABLE medical_alerts (
    id SERIAL NOT NULL, 
    device_id VARCHAR NOT NULL, 
    user_id INTEGER NOT NULL, 
    alert_type VARCHAR, 
    severity VARCHAR, 
    message TEXT, 
    value JSON, 
    is_acknowledged BOOLEAN, 
    acknowledged_at TIMESTAMP WITHOUT TIME ZONE, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_medical_alerts_alert_type ON medical_alerts (alert_type);

CREATE INDEX ix_medical_alerts_device_id ON medical_alerts (device_id);

CREATE INDEX ix_medical_alerts_id ON medical_alerts (id);

CREATE TABLE memories (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    environment_id VARCHAR, 
    title VARCHAR NOT NULL, 
    content TEXT NOT NULL, 
    query TEXT, 
    tags VARCHAR, 
    modality VARCHAR, 
    embedding JSON, 
    extra_data JSON, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    expiry_days INTEGER, 
    is_encrypted BOOLEAN, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_memories_created_at ON memories (created_at);

CREATE INDEX ix_memories_environment_id ON memories (environment_id);

CREATE INDEX ix_memories_id ON memories (id);

CREATE TABLE policies (
    id SERIAL NOT NULL, 
    name VARCHAR, 
    version VARCHAR, 
    domain VARCHAR, 
    description TEXT, 
    triggers JSON, 
    actions JSON, 
    conditions JSON, 
    confidence FLOAT, 
    success_count INTEGER, 
    failure_count INTEGER, 
    last_used TIMESTAMP WITHOUT TIME ZONE, 
    is_active BOOLEAN, 
    is_promoted BOOLEAN, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    created_by INTEGER, 
    approved_by INTEGER, 
    approved_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(approved_by) REFERENCES users (id), 
    FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE INDEX ix_policies_domain ON policies (domain);

CREATE INDEX ix_policies_id ON policies (id);

CREATE INDEX ix_policies_name ON policies (name);

CREATE TABLE user_personas (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    persona_type VARCHAR NOT NULL, 
    name VARCHAR NOT NULL, 
    description TEXT, 
    traits JSON, 
    preferences JSON, 
    is_active BOOLEAN, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_user_personas_id ON user_personas (id);

CREATE TABLE user_profiles (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    preferences JSON, 
    active_persona VARCHAR, 
    workspace_config JSON, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    UNIQUE (user_id)
);

CREATE INDEX ix_user_profiles_id ON user_profiles (id);

CREATE TABLE user_sessions (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    session_token VARCHAR NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    is_active BOOLEAN, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_user_sessions_id ON user_sessions (id);

CREATE UNIQUE INDEX ix_user_sessions_session_token ON user_sessions (session_token);

CREATE TABLE user_widgets (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    widget_type VARCHAR NOT NULL, 
    config JSON, 
    position INTEGER, 
    is_active BOOLEAN, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_user_widgets_id ON user_widgets (id);

CREATE TABLE workflow_tasks (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    title VARCHAR NOT NULL, 
    description TEXT, 
    task_type VARCHAR NOT NULL, 
    status VARCHAR, 
    priority VARCHAR, 
    assigned_to INTEGER, 
    due_date TIMESTAMP WITHOUT TIME ZONE, 
    completed_at TIMESTAMP WITHOUT TIME ZONE, 
    extra_data JSON, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(assigned_to) REFERENCES users (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_workflow_tasks_id ON workflow_tasks (id);

CREATE TABLE behaviour_events (
    id SERIAL NOT NULL, 
    user_id INTEGER, 
    timestamp TIMESTAMP WITHOUT TIME ZONE, 
    event_type VARCHAR, 
    actor VARCHAR, 
    artefact VARCHAR, 
    decision VARCHAR, 
    reason TEXT, 
    outcome VARCHAR, 
    confidence FLOAT, 
    extra_data JSON, 
    pattern_id INTEGER, 
    policy_id INTEGER, 
    correction JSON, 
    learned BOOLEAN, 
    audit_id VARCHAR, 
    reviewed_by INTEGER, 
    reviewed_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(pattern_id) REFERENCES semantic_patterns (id), 
    FOREIGN KEY(policy_id) REFERENCES policies (id), 
    FOREIGN KEY(reviewed_by) REFERENCES users (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_behaviour_events_audit_id ON behaviour_events (audit_id);

CREATE INDEX ix_behaviour_events_event_type ON behaviour_events (event_type);

CREATE INDEX ix_behaviour_events_id ON behaviour_events (id);

CREATE TABLE chat_messages (
    id SERIAL NOT NULL, 
    session_id INTEGER, 
    role VARCHAR, 
    content TEXT, 
    provider VARCHAR, 
    trace_ids JSON, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(session_id) REFERENCES chat_sessions (id)
);

CREATE INDEX ix_chat_messages_id ON chat_messages (id);

CREATE INDEX ix_chat_messages_session_id ON chat_messages (session_id);

CREATE TABLE decision_trajectories (
    id SERIAL NOT NULL, 
    user_id INTEGER, 
    timestamp TIMESTAMP WITHOUT TIME ZONE, 
    decisions JSON, 
    outcomes JSON, 
    context JSON, 
    pattern_id INTEGER, 
    policy_id INTEGER, 
    confidence FLOAT, 
    success_score FLOAT, 
    time_taken INTEGER, 
    corrections INTEGER, 
    PRIMARY KEY (id), 
    FOREIGN KEY(pattern_id) REFERENCES semantic_patterns (id), 
    FOREIGN KEY(policy_id) REFERENCES policies (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_decision_trajectories_id ON decision_trajectories (id);

CREATE TABLE iot_data (
    id SERIAL NOT NULL, 
    device_id VARCHAR NOT NULL, 
    data_type VARCHAR, 
    value JSON NOT NULL, 
    timestamp TIMESTAMP WITHOUT TIME ZONE, 
    user_id INTEGER NOT NULL, 
    linked_memory_id INTEGER, 
    PRIMARY KEY (id), 
    FOREIGN KEY(linked_memory_id) REFERENCES memories (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_iot_data_data_type ON iot_data (data_type);

CREATE INDEX ix_iot_data_device_id ON iot_data (device_id);

CREATE INDEX ix_iot_data_id ON iot_data (id);

CREATE INDEX ix_iot_data_timestamp ON iot_data (timestamp);

CREATE TABLE legal_documents (
    id SERIAL NOT NULL, 
    matter_id INTEGER NOT NULL, 
    title VARCHAR NOT NULL, 
    content TEXT, 
    document_type VARCHAR, 
    file_path VARCHAR, 
    created_by INTEGER NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(created_by) REFERENCES users (id), 
    FOREIGN KEY(matter_id) REFERENCES legal_matters (id)
);

CREATE INDEX ix_legal_documents_id ON legal_documents (id);

CREATE TABLE personal_contexts (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    context_type VARCHAR, 
    value TEXT, 
    associated_memory_id INTEGER, 
    created_at TIMESTAMP WITHOUT TIME ZONE, 
    updated_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(associated_memory_id) REFERENCES memories (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_personal_contexts_context_type ON personal_contexts (context_type);

CREATE INDEX ix_personal_contexts_id ON personal_contexts (id);

CREATE TABLE decision_evidence_links (
    id SERIAL NOT NULL, 
    decision_id INTEGER NOT NULL, 
    evidence_id INTEGER NOT NULL, 
    confidence FLOAT, 
    reasoning TEXT, 
    linked_at TIMESTAMP WITHOUT TIME ZONE, 
    audit_hash VARCHAR(64) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(decision_id) REFERENCES behaviour_events (id), 
    FOREIGN KEY(evidence_id) REFERENCES evidence_blocks (id)
);

CREATE INDEX ix_decision_evidence_links_decision_id ON decision_evidence_links (decision_id);

CREATE INDEX ix_decision_evidence_links_evidence_id ON decision_evidence_links (evidence_id);

CREATE INDEX ix_decision_evidence_links_id ON decision_evidence_links (id);

CREATE TYPE tracestep AS ENUM ('PERCEPTION', 'POLICY_MATCH', 'AI_RECOMMENDATION', 'ACTION', 'OUTCOME', 'SUMMARY');

CREATE TABLE decision_traces (
    id UUID NOT NULL, 
    session_id INTEGER, 
    message_id INTEGER, 
    step tracestep NOT NULL, 
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    data JSON NOT NULL, 
    confidence_score FLOAT, 
    agent_id VARCHAR, 
    is_crystallized BOOLEAN, 
    decision_id VARCHAR, 
    user_id INTEGER, 
    query VARCHAR, 
    response VARCHAR, 
    trace JSON, 
    explanation VARCHAR, 
    pack_name VARCHAR, 
    pack_version VARCHAR, 
    latency_ms FLOAT, 
    PRIMARY KEY (id), 
    FOREIGN KEY(message_id) REFERENCES chat_messages (id), 
    FOREIGN KEY(session_id) REFERENCES chat_sessions (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_decision_traces_decision_id ON decision_traces (decision_id);

CREATE TABLE provenance_records (
    id UUID NOT NULL, 
    trace_id UUID NOT NULL, 
    source_type VARCHAR NOT NULL, 
    source_id VARCHAR NOT NULL, 
    source_text VARCHAR, 
    relevance_score FLOAT, 
    receipt_hash VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(trace_id) REFERENCES decision_traces (id)
);

INSERT INTO alembic_version (version_num) VALUES ('097f92621c9c') RETURNING alembic_version.version_num;

-- Running upgrade 097f92621c9c -> 2b6430d7ed62

ALTER TABLE semantic_patterns ADD COLUMN derived_from JSON;

UPDATE alembic_version SET version_num='2b6430d7ed62' WHERE alembic_version.version_num = '097f92621c9c';

COMMIT;

