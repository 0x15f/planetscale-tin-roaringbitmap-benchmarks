-- Run after loading a benchmark dataset. Replace the schema with dataset.json.schema.
BEGIN;
-- Uncomment and replace the schema name:
-- SET LOCAL search_path TO standard_YYYYMMDD_HHMMSS, public;

-- Native bounded ranking; full_score keeps dense common terms in scoring.
EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON)
SELECT id, tin.full_score(ctid) AS score
FROM documents
WHERE search_text ==> 'common'
ORDER BY tin.full_score(ctid) DESC LIMIT 30;

-- External logical-ID bitmap membership with identical exact result semantics.
EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON)
SELECT d.id, tin.full_score(d.ctid) AS score
FROM documents d CROSS JOIN eligibility_sets e
WHERE e.set_name = 'random_0.001'
  AND d.search_text ==> 'common' AND e.members @> d.id
ORDER BY tin.full_score(d.ctid) DESC LIMIT 30;

-- Enumeration is a SQL shape; the plan determines actual execution order.
EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON)
WITH eligible AS MATERIALIZED (
  SELECT rb64_iterate(members) id FROM eligibility_sets
  WHERE set_name = 'random_0.001'
)
SELECT d.id, tin.full_score(d.ctid) AS score
FROM eligible e JOIN documents d ON d.id = e.id
WHERE d.search_text ==> 'common'
ORDER BY tin.full_score(d.ctid) DESC LIMIT 30;

-- Explicitly give the planner accurate eligibility cardinality and an index.
-- Keep the same transaction/session when using a transaction pooler.
CREATE TEMP TABLE eligible_relation ON COMMIT DROP AS
SELECT d.id, d.ctid AS tid
FROM documents d CROSS JOIN eligibility_sets e
WHERE e.set_name = 'random_0.001' AND e.members @> d.id;
CREATE UNIQUE INDEX ON eligible_relation(id);
CREATE UNIQUE INDEX ON eligible_relation(tid);
ANALYZE eligible_relation;
EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON)
SELECT d.id, tin.full_score(d.ctid) AS score
FROM eligible_relation e JOIN documents d ON d.id = e.id
WHERE d.search_text ==> 'common'
ORDER BY tin.full_score(d.ctid) DESC LIMIT 30;
EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON)
SELECT d.id, tin.full_score(d.ctid) AS score
FROM eligible_relation e JOIN documents d ON d.ctid = e.tid
WHERE d.search_text ==> 'common'
ORDER BY tin.full_score(d.ctid) DESC LIMIT 30;
-- Keep the count path separate from ranked top-k.
EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON)
SELECT count(*) FROM documents WHERE search_text ==> 'common';
EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON)
SELECT count(*) FROM documents d CROSS JOIN eligibility_sets e
WHERE e.set_name = 'random_0.001'
  AND d.search_text ==> 'common' AND e.members @> d.id;

ROLLBACK; -- Drop the temporary relation; persistent fixtures are unchanged.
