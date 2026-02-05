create table if not exists token_blocklist (
  id bigserial primary key,
  jti varchar(36) not null unique,
  token_type varchar(10) not null, -- 'access' ou 'refresh'
  user_id bigint not null references app_user(id) on delete cascade,
  revoked_at timestamptz not null default now(),
  expires_at timestamptz not null
);

create index if not exists idx_token_blocklist_user_id on token_blocklist(user_id);
create index if not exists idx_token_blocklist_expires_at on token_blocklist(expires_at);
