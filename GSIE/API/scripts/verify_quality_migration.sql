\set ON_ERROR_STOP on
BEGIN;

DO $$
DECLARE
    target_uuid uuid := gen_random_uuid();
    run_uuid uuid := gen_random_uuid();
    qa_uuid uuid;
    dimension_value quality_dimension;
    row_count integer;
    weighted_score double precision;
BEGIN
    INSERT INTO resource (id, type, metadata_json)
    VALUES (target_uuid, 'dataset_version', '{}'::jsonb);

    FOREACH dimension_value IN ARRAY ARRAY[
        'completeness'::quality_dimension,
        'positional_accuracy'::quality_dimension,
        'temporal_accuracy'::quality_dimension,
        'thematic_accuracy'::quality_dimension,
        'logical_consistency'::quality_dimension
    ] LOOP
        qa_uuid := gen_random_uuid();
        INSERT INTO resource (id, type, metadata_json)
        VALUES (qa_uuid, 'quality_assessment', '{}'::jsonb);
        INSERT INTO quality_assessment (
            id, target_id, dimension, score, method, assessed_at,
            assessment_run_id, policy_version, weight, details, automated
        ) VALUES (
            qa_uuid, target_uuid, dimension_value, 0.8,
            'test-migration-0048', now(), run_uuid,
            'registry-quality-1', 0.2, '{}'::jsonb, true
        );
    END LOOP;

    SELECT count(*), sum(score * weight) / sum(weight)
    INTO row_count, weighted_score
    FROM quality_assessment
    WHERE target_id = target_uuid AND assessment_run_id = run_uuid;

    IF row_count <> 5 OR abs(weighted_score - 0.8) > 0.000001 THEN
        RAISE EXCEPTION 'run complet invalide: count=%, score=%', row_count, weighted_score;
    END IF;

    BEGIN
        qa_uuid := gen_random_uuid();
        INSERT INTO resource (id, type, metadata_json)
        VALUES (qa_uuid, 'quality_assessment', '{}'::jsonb);
        INSERT INTO quality_assessment (
            id, target_id, dimension, score, method, assessed_at,
            assessment_run_id, policy_version, weight, details, automated
        ) VALUES (
            qa_uuid, target_uuid, 'completeness', 0.8,
            'test-duplicate', now(), run_uuid,
            'registry-quality-1', 0.2, '{}'::jsonb, true
        );
        RAISE EXCEPTION 'le doublon dimensionnel a été accepté';
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE 'unicité run/dimension: OK';
    END;

    BEGIN
        qa_uuid := gen_random_uuid();
        INSERT INTO resource (id, type, metadata_json)
        VALUES (qa_uuid, 'quality_assessment', '{}'::jsonb);
        INSERT INTO quality_assessment (
            id, target_id, dimension, score, method, assessed_at,
            assessment_run_id, policy_version, weight, details, automated
        ) VALUES (
            qa_uuid, target_uuid, 'completeness', 1.1,
            'test-score', now(), gen_random_uuid(),
            'registry-quality-1', 0.2, '{}'::jsonb, true
        );
        RAISE EXCEPTION 'le score hors borne a été accepté';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'contrainte score [0,1]: OK';
    END;

    RAISE NOTICE 'run complet persisté: 5 dimensions, score global 0.8';
END $$;

ROLLBACK;
