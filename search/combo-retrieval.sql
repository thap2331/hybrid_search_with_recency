----------------- vector -----------------
create extension if not exists vector;

----------------- Fuzzy Search -----------------
create extension if not exists pg_trgm;
create index if not exists idx_documents_title_trgm on table1 using gin (topic gin_trgm_ops);

-- fuzzy search
create or replace function combo_search(
  query_text text,
  query_embedding vector(1536),
  match_count int,
  fts_feature_weight float = 1,
  fts_product_weight float = 1,
  semantic_weight float = 1,
  fuzzy_weight float = 1,
  recency_boost float = 1,
  rrf_k int = 50
)
-- returns setof table1
returns table( 
    id bigint,
    company text,
    product text, 
    fts_product tsvector,
    feature text,
    fts_feature tsvector,
    location text, 
    content text, 
    topic text,  
    pub_date TIMESTAMP, 
    age_category text,
    content_embedding VECTOR(1536),
    combined_rank float, 
    rankings jsonb
    )
language sql
as $$
with fuzzy as (
    select id,
           similarity(topic, query_text) as sim_score,
           row_number() over (order by similarity(topic, query_text) desc) as rank_ix
    from table1
    where topic % query_text
    order by rank_ix
    limit least(match_count, 30)
),
fts_product as (
    select id,
           ts_rank_cd(fts_product, websearch_to_tsquery(query_text)) as rank_score,
           row_number() over (order by ts_rank_cd(fts_product, websearch_to_tsquery(query_text)) desc) as rank_ix
    from table1
    where fts_product @@ websearch_to_tsquery(query_text)
    order by rank_ix
    limit least(match_count, 30)
),
fts_feature as (
    select
        id,
        ts_rank_cd(to_tsvector('english', topic), websearch_to_tsquery(query_text)) as rank_score,
        row_number() over(order by ts_rank_cd(fts_feature, websearch_to_tsquery(query_text)) desc) as rank_ix
    from
        table1
    where
        fts_feature @@ websearch_to_tsquery(query_text)
    order by rank_ix
    limit least(match_count, 30)
),
semantic as (
    select
        id,
        1 - (content_embedding <=> query_embedding) as cosine_similarity,
        row_number() over (order by content_embedding <#> query_embedding) as rank_ix
    from
        table1
    order by rank_ix
    limit least(match_count, 30)
)
select
    table1.*,
    coalesce(1.0 / (rrf_k + fuzzy.rank_ix), 0.0) * fuzzy_weight +
    coalesce(1.0 / (rrf_k + fts_feature.rank_ix), 0.0) * fts_feature_weight +
    coalesce(1.0 / (rrf_k + fts_product.rank_ix), 0.0) * fts_product_weight +
    coalesce(1.0 / (rrf_k + semantic.rank_ix), 0.0) * semantic_weight +
    coalesce(1 + recency_boost * (1 - extract(epoch from (now() - table1.pub_date)) / extract(epoch from (now() - '2010-01-01'::timestamp))))
    as combined_rank,
    json_build_object(
      'fuzzy', json_build_object('rank_ix', fuzzy.rank_ix, 'sim_score', fuzzy.sim_score),
      'fts_feature', json_build_object('rank_ix', fts_feature.rank_ix, 'rank_score', fts_feature.rank_score),
      'fts_product', json_build_object('rank_ix', fts_product.rank_ix, 'rank_score', fts_product.rank_score),
      'semantic', json_build_object('rank_ix', semantic.rank_ix, 'cosine_similarity', semantic.cosine_similarity),
      'recency_boost', (1 - extract(epoch from (now() - table1.pub_date)) / extract(epoch from (now() - '2010-01-01'::timestamp)))
    ) as rankings
from
    fuzzy
    full outer join fts_feature on fuzzy.id = fts_feature.id
    full outer join fts_product on coalesce(fuzzy.id, fts_feature.id) = fts_product.id
    full outer join semantic on coalesce(fuzzy.id, fts_feature.id) = semantic.id
    join table1 on coalesce(fuzzy.id, fts_feature.id, semantic.id) = table1.id
order by combined_rank desc
limit least(match_count, 30)
$$;