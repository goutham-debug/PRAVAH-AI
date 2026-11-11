-- PRAVAH AI schema for Supabase (PostgreSQL). Run once in the Supabase SQL editor.
-- Row Level Security is ENABLED with no policies: the public Supabase Data API (anon/authenticated keys)
-- cannot read or write these tables. Only the backend, connecting with the database password, can.

create table if not exists users (
  id serial primary key,
  email varchar(254) not null unique,
  password_hash varchar(255) not null,
  full_name varchar(120) not null,
  role varchar(40) not null default 'READ_ONLY_ANALYST',
  phone varchar(30),
  is_active boolean not null default true,
  must_change_password boolean not null default false,
  failed_logins integer not null default 0,
  locked_until timestamp,
  last_login_at timestamp,
  password_changed_at timestamp,
  created_at timestamp default now()
);
create table if not exists login_audit (
  id serial primary key,
  user_id integer,
  email varchar(254) not null,
  event varchar(40) not null,
  ip_address varchar(64),
  user_agent varchar(255),
  detail varchar(255),
  created_at timestamp default now()
);
create index if not exists ix_login_audit_user_id on login_audit (user_id);
create index if not exists ix_login_audit_created_at on login_audit (created_at);
create table if not exists neighbourhoods (
  id varchar(50) primary key,
  name varchar(120) not null,
  zone varchar(80) not null default 'Mahadevapura',
  ward_no integer,
  population integer not null default 0,
  area_sqkm double precision not null default 1.0,
  hazard_factor double precision not null default 50.0,
  drainage_factor double precision not null default 50.0,
  elevation_m double precision,
  lake_proximity varchar(255),
  centroid_lat double precision not null,
  centroid_lon double precision not null,
  is_pilot boolean default true,
  verification_status varchar(80) default 'UNVERIFIED'
);
create table if not exists facilities (
  id varchar(50) primary key,
  name varchar(150) not null,
  type varchar(40) not null,
  subtype varchar(60),
  lat double precision not null,
  lon double precision not null,
  nearest_node_id varchar(50) not null,
  capacity_beds integer default 0,
  icu_beds integer default 0,
  has_emergency_ward boolean default false,
  phone varchar(40),
  address varchar(255),
  neighbourhood_id varchar(50),
  verification_status varchar(80) default 'UNVERIFIED',
  operational_status varchar(40) default 'OPERATIONAL'
);
create table if not exists shelters (
  id varchar(50) primary key,
  name varchar(150) not null,
  address varchar(255),
  lat double precision not null,
  lon double precision not null,
  nearest_node_id varchar(50) not null,
  total_capacity integer not null default 500,
  current_occupancy integer not null default 0,
  status varchar(40) default 'OPERATIONAL',
  amenities_json text default '[]',
  elevation_m double precision,
  neighbourhood_id varchar(50),
  contact_officer varchar(120),
  phone varchar(40)
);
create table if not exists rescue_teams (
  id varchar(50) primary key,
  name varchar(150) not null,
  type varchar(50) not null,
  capabilities_json text default '[]',
  personnel_count integer default 5,
  boats_count integer default 0,
  pumps_count integer default 0,
  ambulances_count integer default 0,
  status varchar(40) default 'AVAILABLE',
  current_assigned_incident_id varchar(50),
  base_lat double precision not null,
  base_lon double precision not null,
  nearest_node_id varchar(50) not null,
  contact_commander varchar(120),
  phone varchar(40)
);
create table if not exists incident_reports (
  id serial primary key,
  tracking_id varchar(30) not null unique,
  user_id integer,
  citizen_name varchar(120) not null,
  phone varchar(30) not null,
  lat double precision not null,
  lon double precision not null,
  neighbourhood_id varchar(50),
  nearest_node_id varchar(50),
  incident_type varchar(50) not null,
  severity varchar(20) not null default 'MODERATE',
  description text not null,
  photo_url varchar(255),
  status varchar(40) default 'PENDING_VERIFICATION',
  authority_notes text,
  assigned_team_id varchar(50),
  created_at timestamp default now(),
  updated_at timestamp default now()
);
create table if not exists scenarios (
  id varchar(50) primary key,
  name varchar(150) not null,
  description text,
  rainfall_scenario varchar(40) not null default 'HEAVY',
  rainfall_mm double precision not null default 85.0,
  active_disruptions_json text default '[]',
  status varchar(40) default 'COMPLETED',
  run_by_user_id integer,
  created_at timestamp default now()
);
create table if not exists situation_reports (
  id varchar(50) primary key,
  scenario_id varchar(50) not null,
  report_title varchar(200) not null,
  executive_summary text not null,
  metrics_json text default '{}',
  recommendations_json text default '[]',
  generated_by varchar(100) default 'PRAVAH AI Intelligence Engine',
  created_at timestamp default now()
);

alter table login_audit add constraint fk_login_audit_user foreign key (user_id) references users(id);
alter table incident_reports add constraint fk_incident_user foreign key (user_id) references users(id);

alter table users enable row level security;
alter table login_audit enable row level security;
alter table neighbourhoods enable row level security;
alter table facilities enable row level security;
alter table shelters enable row level security;
alter table rescue_teams enable row level security;
alter table incident_reports enable row level security;
alter table scenarios enable row level security;
alter table situation_reports enable row level security;
