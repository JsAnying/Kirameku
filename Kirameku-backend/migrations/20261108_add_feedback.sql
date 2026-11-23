-- PostgreSQL：新增反馈表，不改变已有内容表。
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    type VARCHAR(20) NOT NULL,
    content VARCHAR(2000) NOT NULL,
    contact VARCHAR(200) NOT NULL DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    admin_note VARCHAR(2000) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_feedback_type ON feedback(type);
CREATE INDEX IF NOT EXISTS ix_feedback_status ON feedback(status);
CREATE INDEX IF NOT EXISTS ix_feedback_created_at ON feedback(created_at);
