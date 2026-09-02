-- BE-008: Relational and business-rule constraints

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_population_count_nonnegative'
          AND conrelid = 'population'::regclass
    ) THEN
ALTER TABLE population
    ADD CONSTRAINT chk_population_count_nonnegative
        CHECK (population_count >= 0);
END IF;
END $$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_infrastructure_capacity_nonnegative'
          AND conrelid = 'infrastructure'::regclass
    ) THEN
ALTER TABLE infrastructure
    ADD CONSTRAINT chk_infrastructure_capacity_nonnegative
        CHECK (capacity >= 0);
END IF;
END $$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_carrying_capacity_total_nonnegative'
          AND conrelid = 'carrying_capacity'::regclass
    ) THEN
ALTER TABLE carrying_capacity
    ADD CONSTRAINT chk_carrying_capacity_total_nonnegative
        CHECK (total_capacity >= 0);
END IF;
END $$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_carrying_capacity_estimated_nonnegative'
          AND conrelid = 'carrying_capacity'::regclass
    ) THEN
ALTER TABLE carrying_capacity
    ADD CONSTRAINT chk_carrying_capacity_estimated_nonnegative
        CHECK (estimated_capacity >= 0);
END IF;
END $$;