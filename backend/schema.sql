-- GoldenHour schema. Idempotent. Never holds user content.
create table if not exists meta (key text primary key, value text not null);
create table if not exists rules (
  id text primary key, weight int not null, category text not null, critical bool not null default false,
  pattern text not null, flags text not null default 'i', unless_before text,
  label jsonb not null, why jsonb not null, examples jsonb not null, counter_examples jsonb not null,
  enabled bool not null default true);
create table if not exists kb_entries (
  id text primary key, q jsonb not null, a jsonb not null, keywords text[] not null,
  sources jsonb not null, verified_on date not null, review_by date not null);
create table if not exists ai_usage (day date primary key, tokens bigint not null default 0);
create table if not exists error_reports (
  id bigserial primary key, created_at timestamptz not null default now(),
  page text, note text not null check (length(note) <= 500));
insert into meta (key, value) values ('version', '0') on conflict do nothing;
