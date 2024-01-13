alter system set max_connections = 300;
alter system set shared_buffers = '128MB';
alter system set default_text_search_config = 'pg_catalog.english';

select pg_reload_conf();