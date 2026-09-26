CREATE INDEX documents_tenant_idx ON documents (tenant_id);
CREATE INDEX documents_channel_idx ON documents (channel);
CREATE INDEX documents_category_idx ON documents (category_id);
CREATE INDEX documents_tenant_channel_idx ON documents (tenant_id, channel);
CREATE INDEX documents_search_tin ON documents USING tin (search_text);
ANALYZE documents;
ANALYZE eligibility_sets;
