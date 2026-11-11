-- PRAVAH AI migration 0002: data registry, ingestion log, verification flags, PostGIS point columns.
-- Run in the Supabase SQL editor after 0001. Idempotent. NOT executed against a live Supabase project in the
-- development sandbox (no network) — review and run in a staging project first.

-- 1. Provenance flags on tables that lacked them
alter table shelters      add column if not exists verification_status varchar(80) default 'UNVERIFIED';
alter table rescue_teams  add column if not exists verification_status varchar(80) default 'UNVERIFIED';

-- 2. Central data registry
create table if not exists data_sources (
  key varchar(60) primary key,
  provider varchar(150) not null,
  name varchar(200) not null,
  dataset_type varchar(80) not null,
  source_url varchar(500) not null,
  data_format varchar(20) not null default 'json',
  licence varchar(300),
  coverage varchar(300),
  classification varchar(20) not null default 'NOT_ASSESSED',
  validation_status varchar(20) not null default 'NOT_RUN',
  last_status varchar(20),
  last_attempt_at timestamp,
  last_success_at timestamp,
  retrieved_at timestamp,
  observation_date varchar(60),
  record_count integer,
  checksum varchar(64),
  storage_path varchar(500),
  ttl_seconds integer not null default 3600,
  configured boolean not null default false,
  missing_credentials varchar(300),
  last_error varchar(500),
  validation_json text default '{}',
  notes varchar(500),
  constraint ck_data_sources_class check (classification in
    ('OBSERVED','OFFICIAL','FORECAST','MODELLED','UNVERIFIED','STALE','UNAVAILABLE','NOT_ASSESSED'))
);
create table if not exists ingestion_runs (
  id serial primary key,
  source_key varchar(60) not null references data_sources(key),
  status varchar(20) not null default 'RUNNING',
  triggered_by varchar(80),
  started_at timestamp default now(),
  finished_at timestamp,
  http_status integer,
  attempts integer,
  duration_ms integer,
  records integer,
  error varchar(500),
  validation_json text default '{}'
);
create index if not exists ix_ingestion_runs_source_key on ingestion_runs (source_key);
create index if not exists ix_ingestion_runs_started_at on ingestion_runs (started_at);
create table if not exists ingestion_events (
  id serial primary key,
  run_id integer references ingestion_runs(id),
  source_key varchar(60) not null,
  level varchar(10) not null default 'INFO',
  message varchar(500) not null,
  created_at timestamp default now()
);
create index if not exists ix_ingestion_events_run_id on ingestion_events (run_id);
create index if not exists ix_ingestion_events_source_key on ingestion_events (source_key);
create index if not exists ix_ingestion_events_created_at on ingestion_events (created_at);

alter table data_sources enable row level security;
alter table ingestion_runs enable row level security;
alter table ingestion_events enable row level security;

-- 3. PostGIS: point geometry derived from the existing lat/lon columns (single source of truth stays lat/lon).
create extension if not exists postgis;
alter table facilities     add column if not exists geom geometry(Point, 4326)
  generated always as (st_setsrid(st_makepoint(lon, lat), 4326)) stored;
alter table shelters       add column if not exists geom geometry(Point, 4326)
  generated always as (st_setsrid(st_makepoint(lon, lat), 4326)) stored;
alter table rescue_teams   add column if not exists geom geometry(Point, 4326)
  generated always as (st_setsrid(st_makepoint(base_lon, base_lat), 4326)) stored;
alter table incident_reports add column if not exists geom geometry(Point, 4326)
  generated always as (st_setsrid(st_makepoint(lon, lat), 4326)) stored;
alter table neighbourhoods add column if not exists centroid geometry(Point, 4326)
  generated always as (st_setsrid(st_makepoint(centroid_lon, centroid_lat), 4326)) stored;
create index if not exists ix_facilities_geom on facilities using gist (geom);
create index if not exists ix_shelters_geom on shelters using gist (geom);
create index if not exists ix_rescue_teams_geom on rescue_teams using gist (geom);
create index if not exists ix_incident_reports_geom on incident_reports using gist (geom);
create index if not exists ix_neighbourhoods_centroid on neighbourhoods using gist (centroid);
-- Ward polygons and road geometry (from GBA/BBMP and OSM ingestion) are imported in a later stage into
-- geometry(MultiPolygon,4326) / geometry(LineString,4326) tables; none are created here to avoid empty placeholders.
