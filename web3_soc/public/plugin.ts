import { i18n } from '@osd/i18n';
import { AppMountParameters, CoreSetup, CoreStart, Plugin } from '../../../src/core/public';
import { Web3SocPluginSetup, Web3SocPluginStart, AppPluginStartDependencies } from './types';
import { PLUGIN_NAME } from '../common';

export class Web3SocPlugin implements Plugin<Web3SocPluginSetup, Web3SocPluginStart> {
  public setup(core: CoreSetup): Web3SocPluginSetup {
    // Register an application into the side navigation menu
    core.application.register({
      id: 'web3Soc',
      title: PLUGIN_NAME,
      category: {
        id: 'wazuh',
        label: 'RIGSEC',
        order: 10,
      },
      async mount(params: AppMountParameters) {
        // Load application bundle
        const { renderApp } = await import('./application');
        // Get start services as specified in opensearch_dashboards.json
        const [coreStart, depsStart] = await core.getStartServices();
        // Render the application
        return renderApp(coreStart, depsStart as AppPluginStartDependencies, params);
      },
    });

    // Return methods that should be available to other plugins
    return {
      getGreeting() {
        return i18n.translate('web3Soc.greetingText', {
          defaultMessage: 'Hello from {name}!',
          values: {
            name: PLUGIN_NAME,
          },
        });
      },
    };
  }

  public start(core: CoreStart): Web3SocPluginStart {
    return {};
  }

  public stop() {}
}
