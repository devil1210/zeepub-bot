import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://qouajkqgieynczayrkam.supabase.co';
const supabaseKey = 'sb_publishable_iKKTE7z0kV2WMqaPTUqpcg_dC4e0T0o';

export const supabase = createClient(supabaseUrl, supabaseKey);
