export interface AlertMeta {
  id: string; // alert name, should be unique
  name: string; // Name of the alert, .e.g. Flash Loan Detector
  description: string; // Description of the alert
  created_at: string; // ISO 8601 date string, e.g. 2020-01-01T00:00:00.000Z
  scope: 'block' | 'tx' | 'log' | 'token_xfer'; // Scope of the alert (i.e. block, tx, log)
  is_active: boolean; // Whether the alert is active
}

export interface SlackInitArgs {
  url: string; // slack webhook url, e.g. https://hooks.slack.com/services/XXXXX/XXXXX/XXXXX
  username: string; // slack username, e.g. Chain Alert
  channel: string; // slack channel, e.g. web3-slack-alert
}

export interface ReceiverValue {
  receiver: string; // receiver type, e.g. email, slack, etc.
  init_args: SlackInitArgs;
}

export interface Receiver {
  [key: string]: ReceiverValue;
}

export interface LabelOption {
  key: string;
  value: string;
}

export interface Alert extends AlertMeta {
  where: string; // SQL where clause
  output: string; // Formattable template for the alert message
  labels: LabelOption[]; // key value pairs
  receivers: Receiver; // receiver object
}
