import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://qouajkqgieynczayrkam.supabase.co';
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'sb_publishable_iKKTE7z0kV2WMqaPTUqpcg_dC4e0T0o';

if (!supabaseUrl || !supabaseKey) {
  throw new Error(
    'Missing required env vars: VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY'
  );
}

export const supabase = createClient(supabaseUrl, supabaseKey);
