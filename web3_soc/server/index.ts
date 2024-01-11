import { PluginInitializerContext } from '../../../src/core/server';
import { Web3SocPlugin } from './plugin';

// This exports static code and TypeScript types,
// as well as, OpenSearch Dashboards Platform `plugin()` initializer.

export function plugin(initializerContext: PluginInitializerContext) {
  return new Web3SocPlugin(initializerContext);
}

export { Web3SocPluginSetup, Web3SocPluginStart } from './types';
