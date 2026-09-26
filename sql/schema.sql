CREATE TABLE documents (
 id bigint PRIMARY KEY, tenant_id integer NOT NULL, channel smallint NOT NULL,
 category_id integer NOT NULL, active boolean NOT NULL, title text NOT NULL,
 description text NOT NULL, search_text text NOT NULL
);
CREATE TABLE eligibility_sets (
 set_name text PRIMARY KEY, member_count bigint NOT NULL, members public.roaringbitmap64 NOT NULL
);
