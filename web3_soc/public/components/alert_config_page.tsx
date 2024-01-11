import React, { useState, useEffect, useMemo } from 'react';
import {
  EuiFieldText,
  EuiFormRow,
  EuiSelect,
  EuiFlexGroup,
  EuiFlexItem,
  EuiCodeBlock,
  EuiButton,
  EuiPageContent,
  EuiFlyout,
  EuiFlyoutHeader,
  EuiFlyoutBody,
  EuiTitle,
  EuiComboBox,
  EuiSpacer,
  formatDate,
} from '@elastic/eui';
import { FormattedMessage } from '@osd/i18n/react';
import { i18n } from '@osd/i18n';
import { Receiver, LabelOption } from '../../models';
import { getAlertById } from '../../api';
import { useWeb3SocContext } from './app';
import { useHistory, useParams } from 'react-router-dom';
import yaml from 'js-yaml';

interface Field {
  title: string;
  description: string;
  required: boolean;
  isInvalid?: boolean;
  errors?: string[];
  example?: JSX.Element;
  component: JSX.Element;
}
export const AlertConfigPage = () => {
  // get alert id from url params
  const { id } = useParams<{ id: string }>();

  // context
  const { notifications } = useWeb3SocContext()!;

  // router
  const router = useHistory();

  // controller
  const [isLoading, setIsLoading] = useState(false);
  const [isFlyoutOpen, setIsFlyoutOpen] = useState(false);

  // State for each field
  const [alarmID, setAlarmID] = useState(id);
  const [created_at, setCreatedAt] = useState('');
  const [is_active, setIsActive] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [scope, setScope] = useState('block');
  const [where, setWhere] = useState('');
  const [output, setOutput] = useState('');
  const [labels, setLabels] = useState<LabelOption[]>([]);
  const [selectedReceivers, setSelectedReceivers] = useState<Receiver>({} as Receiver);

  // API calls
  const handleGetAlert = (id: string) => {
    setIsLoading(true);
    getAlertById(id)
      .then((alert) => {
        setAlarmID(alert.id);
        setCreatedAt(alert.created_at);
        setIsActive(alert.is_active);
        setName(alert.name);
        setDescription(alert.description);
        setScope(alert.scope);
        setWhere(alert.where);
        setOutput(alert.output);
        setLabels(alert.labels);
        setSelectedReceivers(alert.receivers);
      })
      .catch((err) => {
        notifications.toasts.addDanger({
          title: i18n.translate('web3Soc.viewAlert.getAlert.error.title', {
            defaultMessage: 'Get alert error',
          }),
          text: i18n.translate('web3Soc.viewAlert.getAlert.error.text', {
            defaultMessage: `Couldn't get alert, see console for details`,
          }),
        });
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  // Fetch default receivers at first
  useEffect(() => {
    handleGetAlert(id);
  });

  // Computed props
  const yamlFormat = useMemo(() => {
    return yaml.dump(
      {
        name,
        description,
        scope,
        where,
        output,
        labels,
        receivers: selectedReceivers,
      },
      { indent: 2 }
    );
  }, [name, description, scope, where, output, labels, selectedReceivers]);

  const fields: Field[] = [
    {
      title: 'Name',
      description: `You have created an alert named ${name}.`,
      required: true,
      component: (
        <EuiFieldText
          name="name"
          required={true}
          placeholder="Christmas Alert"
          value={name}
          contentEditable={false}
        />
      ),
    },
    {
      title: 'Description',
      description: 'A short description of the alert.',
      required: true,
      component: (
        <EuiFieldText
          name="description"
          required={true}
          value={description}
          contentEditable={false}
        />
      ),
    },
    {
      title: 'Created Time',
      description: `You have created this alert at ${formatDate(
        created_at,
        'YYYY-MM-DD HH:MM:SS'
      )}.`,
      required: true,
      component: (
        <EuiFieldText
          name="created_at"
          required={true}
          value={formatDate(created_at, 'YYYY-MM-DD HH:MM:SS')}
          contentEditable={false}
        />
      ),
    },
    {
      title: 'Scope',
      description: `You are now subscribing to ${scope}.`,
      required: true,
      component: (
        <EuiSelect
          value={scope}
          defaultChecked={true}
          defaultValue={scope}
          contentEditable={false}
          options={[{ text: scope, value: scope }]}
        ></EuiSelect>
      ),
    },
    {
      title: 'Where',
      description: 'An sql expression for when the alert should be triggered.',
      required: false,
      component: (
        <EuiCodeBlock language="sql" isCopyable>
          {where}
        </EuiCodeBlock>
      ),
    },
    {
      title: 'Output',
      description: 'The output template string for the alert.',
      required: true,

      component: (
        <EuiCodeBlock language="markdown" isCopyable={true}>
          {output}
        </EuiCodeBlock>
      ),
    },
    {
      title: 'Receivers',
      description: `Send alert to ${Object.keys(selectedReceivers).join(', ')}.`,
      required: true,
      component: (
        <>
          <EuiComboBox
            placeholder="Select multiple receivers"
            options={Object.keys(selectedReceivers).map((key) => {
              return { label: key };
            })}
            selectedOptions={Object.keys(selectedReceivers).map((key) => {
              return { label: key };
            })}
            contentEditable={false}
            isClearable={false}
          />
        </>
      ),
    },
    {
      title: 'Labels',
      description:
        'Add labels to this alert. Label is a key-value pair. For example: {vulnerability: reentrancy, posibility: high}',
      required: false,
      component: (
        <>
          {labels.map((label, index) => {
            return (
              <EuiFlexGroup
                gutterSize="s"
                alignItems="center"
                justifyContent="spaceEvenly"
                key={`label-${label.key}-${label.value}`}
              >
                <EuiFlexItem grow={4}>
                  <EuiSelect
                    prepend="Key"
                    options={[{ value: label.key, text: label.key }]}
                    value={label.key}
                    contentEditable={false}
                  />
                </EuiFlexItem>
                <EuiFlexItem grow={4}>
                  <EuiSelect
                    prepend="Value"
                    contentEditable={false}
                    options={[{ value: label.value, text: label.value }]}
                    value={label.value}
                  />
                </EuiFlexItem>
              </EuiFlexGroup>
            );
          })}
        </>
      ),
    },
  ];

  const flyout = (
    <EuiFlyout
      ownFocus
      onClose={() => {
        setIsFlyoutOpen(false);
      }}
    >
      <EuiFlyoutHeader hasBorder>
        <EuiTitle>
          <h2 id="flyoutTitle">Preview in YAML</h2>
        </EuiTitle>
      </EuiFlyoutHeader>
      <EuiFlyoutBody>
        <div style={{ blockSize: '100%' }}>
          <EuiCodeBlock language="yaml" fontSize="m" isCopyable>
            {yamlFormat}
          </EuiCodeBlock>
        </div>
      </EuiFlyoutBody>
    </EuiFlyout>
  );

  return (
    <>
      <EuiPageContent>
        <EuiFlexGroup justifyContent="spaceEvenly" gutterSize="l" direction="column">
          {fields.map((field, index) => {
            return (
              <EuiFlexItem>
                <EuiTitle size="m">
                  <h2>{field.title}</h2>
                </EuiTitle>
                <EuiFlexItem>{field.component}</EuiFlexItem>
              </EuiFlexItem>
            );
          })}
        </EuiFlexGroup>
        <EuiSpacer size="l"></EuiSpacer>
        <EuiFlexGroup justifyContent="spaceEvenly" alignItems="center" gutterSize="l">
          <EuiFlexItem grow={false}>
            <EuiButton
              color="accent"
              iconSide="right"
              iconType="arrowLeft"
              onClick={() => {
                router.push('/alerts');
              }}
            >
              <FormattedMessage id="web3Soc.viewAlert.return.button" defaultMessage="Return" />
            </EuiButton>
          </EuiFlexItem>
          <EuiFlexItem grow={false}>
            <EuiButton
              color="secondary"
              iconSide="right"
              iconType="eye"
              onClick={() => {
                setIsFlyoutOpen((isFlyoutOpen) => !isFlyoutOpen);
              }}
            >
              <FormattedMessage id="web3Soc.viewAlert.preview.button" defaultMessage="Preview" />
            </EuiButton>
          </EuiFlexItem>
        </EuiFlexGroup>
        {isFlyoutOpen && flyout}
      </EuiPageContent>
    </>
  );
};
