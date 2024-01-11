import { AlertMeta, Alert, Receiver, LabelOption } from '../models';

export const MockAlertMetas: AlertMeta[] = [
  {
    id: '62f84779-5895-4caf-be42-818c4d457008',
    name: 'Flash Loan Alert',
    description: 'Alert for unusual flashloan activity',
    scope: 'tx',
    created_at: '2021-07-21T15:36:00.000Z',
    is_active: true,
  },
  {
    id: '0681ce1a-f59f-4ea4-948b-6b930f3e6c82',
    name: 'Christmas Alert',
    description: 'Santa Claus is coming to town!',
    scope: 'log',
    created_at: '2023-12-25T00:00:00.000Z',
    is_active: false,
  },
];

export const MockAlerts: Alert[] = [
  {
    id: '62f84779-5895-4caf-be42-818c4d457008',
    name: 'Flash Loan Alert',
    description: 'Alert for unusual flashloan activity',
    scope: 'tx',
    created_at: '2021-07-21T15:36:00.000Z',
    is_active: true,
    where: 'block_number > 1000000',
    output: 'Flashloan activity detected in block {{block_number}}',
    labels: [
      {
        key: 'severity',
        value: 'low',
      },
      {
        key: 'bug',
        value: 'reentrancy',
      },
    ],
    receivers: {
      slack_alert_public: {
        receiver: 'slack',
        init_args: {
          url: 'https://hooks.slack.com/services/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',
          username: 'Chain Alert',
          channel: '#web3-slack-alert',
        },
      },
    },
  },
  {
    id: '0681ce1a-f59f-4ea4-948b-6b930f3e6c82',
    name: 'Christmas Alert',
    description: 'Santa Claus is coming to town!',
    scope: 'log',
    created_at: '2023-12-25T00:00:00.000Z',
    is_active: false,
    where: 'block_number > 1000000',
    output: 'Santa Claus is coming to town!',
    labels: [
      {
        key: 'severity',
        value: 'critical',
      },
      {
        key: 'bug',
        value: 'reentrancy',
      },
    ],
    receivers: {
      slack_alert_private: {
        receiver: 'slack',
        init_args: {
          url: 'https://hooks.slack.com/services/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',
          username: 'Santa Alert',
          channel: '#santa-alert',
        },
      },
    },
  },
];

export const MockReceivers: Receiver = {
  slack_alert_public: {
    receiver: 'slack',
    init_args: {
      channel: '#alerts',
      url: 'https://hooks.slack.com/services/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',
      username: 'Chain Alert',
    },
  },
  slack_alert_private: {
    receiver: 'slack',
    init_args: {
      channel: '#alerts',
      url: 'https://hooks.slack.com/services/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',
      username: 'Chain Alert - private',
    },
  },
};

export const MockLabels: LabelOption[] = [
  {
    key: 'severity',
    value: 'critical',
  },
  {
    key: 'severity',
    value: 'high',
  },
  {
    key: 'severity',
    value: 'medium',
  },
  {
    key: 'severity',
    value: 'low',
  },
  {
    key: 'bug',
    value: 'reentrant',
  },
  {
    key: 'bug',
    value: 'overflow',
  },
  {
    key: 'bug',
    value: 'flashloan',
  },
];
