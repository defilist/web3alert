import './index.scss';

import { Web3SocPlugin } from './plugin';

// This exports static code and TypeScript types,
// as well as, OpenSearch Dashboards Platform `plugin()` initializer.
export function plugin() {
  return new Web3SocPlugin();
}
export { Web3SocPluginSetup, Web3SocPluginStart } from './types';
