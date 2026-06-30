require('dotenv').config();

const config = {
  supabaseUrl: process.env.SUPABASE_URL,
  supabaseServiceRoleKey: process.env.SUPABASE_SERVICE_ROLE_KEY,
  port: process.env.PORT || 8000,
  tallyUrl: process.env.TALLY_URL || 'http://localhost:9000'
};

// Validate mandatory environment configs
if (!config.supabaseUrl || config.supabaseUrl === 'https://your-project.supabase.co') {
  console.error('ERROR: SUPABASE_URL has not been configured in .env');
  process.exit(1);
}

if (!config.supabaseServiceRoleKey || config.supabaseServiceRoleKey === 'your-service-role-key') {
  console.error('ERROR: SUPABASE_SERVICE_ROLE_KEY has not been configured in .env');
  process.exit(1);
}

module.exports = config;
