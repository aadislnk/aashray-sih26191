-- BE-010: Complete Data Source Metadata

ALTER TABLE data_source
    ADD COLUMN url VARCHAR(500);

ALTER TABLE data_source
    ADD COLUMN crs VARCHAR(100);

ALTER TABLE data_source
    ADD COLUMN notes TEXT;
