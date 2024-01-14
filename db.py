from supabase import create_client, Client
import config

supabase_client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)
