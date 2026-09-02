-- BE-010: Define Data Source Metadata

ALTER TABLE data_source
    ADD COLUMN source_type VARCHAR(50);

ALTER TABLE data_source
    ADD COLUMN effective_time TIMESTAMPTZ;

ALTER TABLE data_source
    ADD COLUMN coverage TEXT;

ALTER TABLE data_source
    ADD COLUMN resolution VARCHAR(100);