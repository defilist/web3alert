import {
  PluginInitializerContext,
  CoreSetup,
  CoreStart,
  Plugin,
  Logger,
} from '../../../src/core/server';

import { Web3SocPluginSetup, Web3SocPluginStart } from './types';
import { defineRoutes } from './routes';

export class Web3SocPlugin implements Plugin<Web3SocPluginSetup, Web3SocPluginStart> {
  private readonly logger: Logger;

  constructor(initializerContext: PluginInitializerContext) {
    this.logger = initializerContext.logger.get();
  }

  public setup(core: CoreSetup) {
    this.logger.debug('web3_soc: Setup');
    const router = core.http.createRouter();

    // Register server side APIs
    defineRoutes(router);

    return {};
  }

  public start(core: CoreStart) {
    this.logger.debug('web3_soc: Started');
    return {};
  }

  public stop() {}
}
