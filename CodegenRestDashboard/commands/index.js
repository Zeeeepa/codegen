#!/usr/bin/env node
const path = require('path');
const { loadEnv } = require('../utils/env');
loadEnv(path.join(__dirname, '..', '.env'));

module.exports = {
  create: require('./create_agent_run'),
  resume: require('./resume_agent_run'),
  list: require('./list_agent_runs'),
  get: require('./get_agent_run'),
  genSetup: require('./generate_setup_commands'),
};

