alter system set max_connections = 300;
alter system set tcp_keepalives_idle = 30;
alter system set shared_buffers = '128MB';
alter system set idle_in_transaction_session_timeout = 10000;
alter system set default_text_search_config = 'pg_catalog.english';
alter system set tcp_keepalives_count = 5;
alter system set tcp_user_timeout = 10000;
select pg_reload_conf();