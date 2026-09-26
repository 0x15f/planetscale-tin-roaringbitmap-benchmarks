SELECT version();
SELECT name, default_version, installed_version FROM pg_available_extensions
WHERE name IN ('tin','roaringbitmap') ORDER BY name;
SELECT extname, extversion FROM pg_extension ORDER BY extname;
SELECT name, setting, unit FROM pg_settings
WHERE name IN ('server_version','shared_buffers','work_mem','effective_cache_size',
'random_page_cost','seq_page_cost','max_parallel_workers_per_gather');
SELECT n.nspname, p.proname, pg_get_function_identity_arguments(p.oid)
FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
WHERE n.nspname='tin' ORDER BY p.proname;
SELECT typname FROM pg_type WHERE typname LIKE 'roaring%';
SELECT n.nspname,p.proname,pg_get_function_identity_arguments(p.oid),pg_get_function_result(p.oid)
FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
WHERE p.proname LIKE 'rb64_%' ORDER BY p.proname;
