import { NavigationPublicPluginStart } from '../../../src/plugins/navigation/public';

export interface Web3SocPluginSetup {
  getGreeting: () => string;
}
// eslint-disable-next-line @typescript-eslint/no-empty-interface
export interface Web3SocPluginStart {}

export interface AppPluginStartDependencies {
  navigation: NavigationPublicPluginStart;
}
