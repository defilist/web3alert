import React from 'react';
import {
  EuiPageContent,
  EuiPageContentHeader,
  EuiTitle,
  EuiPageContentBody,
  EuiHorizontalRule,
  EuiText,
  EuiButton,
} from '@elastic/eui';
import { Link } from 'react-router-dom';
import { FormattedMessage } from '@osd/i18n/react';

export const WelcomePage = () => {
  return (
    <EuiPageContent>
      <EuiPageContentHeader>
        <EuiTitle>
          <h2>
            <FormattedMessage
              id="web3Soc.congratulationsTitle"
              defaultMessage="Security Operations Center for Your Web3 digital assets!"
            />
          </h2>
        </EuiTitle>
      </EuiPageContentHeader>
      <EuiPageContentBody>
        <EuiText>
          <p>
            <FormattedMessage
              id="web3Soc.content"
              defaultMessage="Look through the generated code and check out the plugin development documentation."
            />
          </p>
          <EuiHorizontalRule />
          <Link to="/alerts">
            <EuiButton type="primary" size="s">
              <FormattedMessage id="web3Soc.explore" defaultMessage="Explore"></FormattedMessage>
            </EuiButton>
          </Link>
        </EuiText>
      </EuiPageContentBody>
    </EuiPageContent>
  );
};
