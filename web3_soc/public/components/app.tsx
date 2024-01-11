import React, { createContext } from 'react';
import { FormattedMessage, I18nProvider } from '@osd/i18n/react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';

import { EuiPage, EuiPageBody, EuiPageHeader, EuiTitle, EuiTabs, EuiTab } from '@elastic/eui';

import { CoreStart } from '../../../../src/core/public';
import { NavigationPublicPluginStart } from '../../../../src/plugins/navigation/public';

import { PLUGIN_ID, PLUGIN_NAME } from '../../common';
// import { EuiTabs, EuiTab } from '@opensearch-project/oui';
import { Link } from 'react-router-dom';
import { AlertsPage } from './alerts_page';
import { AlertConfigPage } from './alert_config_page';
import { WelcomePage } from './welcome_page';
import { NewAlertPage } from './new_alert_page';

interface Web3SocAppDeps {
  basename: string;
  notifications: CoreStart['notifications'];
  http: CoreStart['http'];
  navigation: NavigationPublicPluginStart;
}

const Web3SocContext = createContext<Web3SocAppDeps | null>(null);
export const useWeb3SocContext = () => React.useContext(Web3SocContext);

export const Web3SocApp = ({ basename, notifications, http, navigation }: Web3SocAppDeps) => {
  // Render the application DOM.
  // Note that `navigation.ui.TopNavMenu` is a stateful component exported on the `navigation` plugin's start contract.
  return (
    <Router basename={basename}>
      <Web3SocContext.Provider value={{ basename, notifications, http, navigation }}>
        <I18nProvider>
          <>
            <navigation.ui.TopNavMenu
              appName={PLUGIN_ID}
              showSearchBar={false}
              useDefaultBehaviors={true}
            />

            <EuiTabs>
              <Link to="/">
                <EuiTab>Home</EuiTab>
              </Link>

              <Link to="/alerts">
                <EuiTab>Alerts</EuiTab>
              </Link>
            </EuiTabs>

            <EuiPage restrictWidth="1000px">
              <EuiPageBody component="main">
                <EuiPageHeader>
                  <EuiTitle size="l">
                    <h1>
                      <FormattedMessage
                        id="web3Soc.helloWorldText"
                        defaultMessage="{name}"
                        values={{ name: PLUGIN_NAME }}
                      />
                    </h1>
                  </EuiTitle>
                </EuiPageHeader>
                <Switch>
                  <Route exact path="/" component={WelcomePage} />
                  <Route exact path="/alerts" component={AlertsPage} />
                  <Route exact path="/alerts/new" component={NewAlertPage} />
                  <Route exact path="/alerts/:id" component={AlertConfigPage} />
                </Switch>
              </EuiPageBody>
            </EuiPage>
          </>
        </I18nProvider>
      </Web3SocContext.Provider>
    </Router>
  );
};
