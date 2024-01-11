import React, { useState, useEffect, useMemo } from 'react';
import {
  EuiFieldText,
  EuiForm,
  EuiFormRow,
  EuiDescribedFormGroup,
  EuiSelect,
  EuiFlexGroup,
  EuiFlexItem,
  EuiCodeBlock,
  EuiTextArea,
  EuiButton,
  EuiPageContent,
  EuiFlyout,
  EuiFlyoutHeader,
  EuiFlyoutBody,
  EuiTitle,
  EuiComboBox,
  EuiModal,
  EuiModalBody,
  EuiModalHeader,
  EuiModalFooter,
  EuiModalHeaderTitle,
  EuiButtonIcon,
  EuiButtonEmpty,
  EuiSpacer,
} from '@elastic/eui';
import { FormattedMessage } from '@osd/i18n/react';
import { i18n } from '@osd/i18n';
import { Alert, Receiver, LabelOption } from '../../models';
import { getReceivers, newAlert, getLabels } from '../../api';
import { useWeb3SocContext } from './app';
import { useHistory } from 'react-router-dom';
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

type PartialAlert = Omit<Alert, 'id' | 'created_at' | 'is_active'>;

export const NewAlertPage = () => {
  // context
  const { notifications } = useWeb3SocContext()!;

  // router
  const router = useHistory();

  // controller
  const [isLoading, setIsLoading] = useState(false);
  const [isFlyoutOpen, setIsFlyoutOpen] = useState(false);

  // State for each field
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [scope, setScope] = useState('block');
  const [where, setWhere] = useState('');
  const [output, setOutput] = useState('');
  const [labels, setLabels] = useState<LabelOption[]>([]);
  const [labelOpts, setLabelOpts] = useState<LabelOption[]>([]);
  const [selectedReceivers, setSelectedReceivers] = useState<Receiver>({} as Receiver);
  const [defaultReceivers, setDefaultReceivers] = useState<Receiver>({} as Receiver);
  const [isReceiversModalOpen, setIsReceiversModalOpen] = useState(false);

  // State for receiver modal
  const [customReceiverName, setCustomReceiverName] = useState('');
  const [customReceiver, setCustomReceiver] = useState('slack');
  const [customReceiverUrl, setCustomReceiverUrl] = useState('');
  const [customReceiverUsername, setCustomReceiverUsername] = useState('');
  const [customReceiverChannel, setCustomReceiverChannel] = useState('');

  // invalid state for each field
  const [nameInvalid, setNameInvalid] = useState(false);
  const [descriptionInvalid, setDescriptionInvalid] = useState(false);
  const [outputInvalid, setOutputInvalid] = useState(false);
  const [nameError, setNameError] = useState('');
  const [descriptionError, setDescriptionError] = useState('');
  const [outputError, setOutputError] = useState('');

  // alias
  const closeReceiversModal = () => setIsReceiversModalOpen(false);

  // Handlers for each field
  const handleNameChange = (event: any) => setName(event.target.value);
  const handleDescriptionChange = (event: any) => setDescription(event.target.value);
  const handleScopeChange = (event: any) => setScope(event.target.value);
  const handleWhereChange = (event: any) => setWhere(event.target.value);
  const handleOutputChange = (event: any) => setOutput(event.target.value);
  const handleLabelsChange = (index: number, kind: 'key' | 'value', value: any) => {
    console.log(index, kind, value);
    const newLabels = [...labels];
    newLabels[index][kind] = value;
    setLabels(newLabels);
  };
  const handleAddPair = () => {
    const newLabels = [...labels, { key: '', value: '' }];
    setLabels(newLabels);
  };
  const handleRemovePair = (index: number) => {
    const newLabels = labels.filter((_, i) => i !== index);
    setLabels(newLabels);
  };
  const handleSelectedReceiversChange = (event: any) => {
    const selectedReceivers: Receiver = {};
    event.forEach((receiver: any) => {
      selectedReceivers[receiver.label] = defaultReceivers[receiver.label];
    });
    setSelectedReceivers(selectedReceivers);
  };
  const handleSaveReceiverModal = () => {
    // Validate
    if (customReceiverName === '' || defaultReceivers[customReceiverName] !== undefined) {
      notifications.toasts.addDanger({
        title: i18n.translate('web3Soc.newAlert.customReceivers.name.error.title', {
          defaultMessage: "Receiver's name is empty or already exists",
        }),
      });
      return;
    }
    if (customReceiver === '') {
      notifications.toasts.addDanger({
        title: i18n.translate('web3Soc.newAlert.customReceivers.receiver.error.title', {
          defaultMessage: 'Receiver is required',
        }),
      });
      return;
    }
    if (customReceiverUrl === '') {
      notifications.toasts.addDanger({
        title: i18n.translate('web3Soc.newAlert.customReceivers.url.error.title', {
          defaultMessage: 'Url is required',
        }),
      });
      return;
    }
    if (customReceiverUsername === '') {
      notifications.toasts.addDanger({
        title: i18n.translate('web3Soc.newAlert.customReceivers.username.error.title', {
          defaultMessage: 'Username is required',
        }),
      });
      return;
    }
    if (customReceiverChannel === '') {
      notifications.toasts.addDanger({
        title: i18n.translate('web3Soc.newAlert.customReceivers.channel.error.title', {
          defaultMessage: 'Channel is required',
        }),
      });
      return;
    }
    const newReceiver: Receiver = {
      [customReceiverName]: {
        receiver: customReceiver,
        init_args: {
          url: customReceiverUrl,
          username: customReceiverUsername,
          channel: customReceiverChannel,
        },
      },
    };
    setDefaultReceivers({ ...defaultReceivers, ...newReceiver });
    setSelectedReceivers({ ...selectedReceivers, ...newReceiver });
    resetReceiverModalForm();
    setIsReceiversModalOpen(false);
  };
  const handleReturn = () => {
    if (
      confirm(
        i18n.translate('web3Soc.newAlert.return.confirm', {
          defaultMessage: 'Are you sure to return? All data will be lost!',
        })
      )
    ) {
      router.push('/alerts');
    }
  };
  const handleCancelReceiverModalForm = () => {
    resetReceiverModalForm();
    setIsReceiversModalOpen(false);
  };

  // API calls
  const handleGetReceivers = () => {
    getReceivers()
      .then((res: Receiver) => {
        setDefaultReceivers(res);
      })
      .catch((err) => {
        notifications.toasts.addDanger({
          title: i18n.translate('web3Soc.newAlert.fetchReceivers.error.title', {
            defaultMessage: 'Failed to fetch receivers',
          }),
          text: err.message,
        });
      });
  };
  const handleGetLabelOptions = () => {
    getLabels()
      .then((res) => {
        setLabelOpts(res);
      })
      .catch((err) => {
        notifications.toasts.addDanger({
          title: i18n.translate('web3Soc.newAlert.fetchLabels.error.title', {
            defaultMessage: 'Failed to fetch labels',
          }),
          text: err.message,
        });
      });
  };

  // Reset form and invalid state
  const resetForm = () => {
    // reset form
    setName('');
    setDescription('');
    setScope('block');
    setWhere('');
    setOutput('');
    setLabels([]);
    setSelectedReceivers({} as Receiver);
  };
  const resetInvalidState = () => {
    setNameInvalid(false);
    setDescriptionInvalid(false);
    setOutputInvalid(false);
    setNameError('');
    setDescriptionError('');
    setOutputError('');
  };
  const resetReceiverModalForm = () => {
    setCustomReceiverName('');
    setCustomReceiver('slack');
    setCustomReceiverUrl('');
    setCustomReceiverUsername('');
    setCustomReceiverChannel('');
  };

  // Handle submit form
  const handleSubmitForm = () => {
    if (name === '') {
      setNameInvalid(true);
      setNameError("Name can't be empty");
      notifications.toasts.addDanger({
        title: i18n.translate('web3Soc.newAlert.formValidation.name.error.title', {
          defaultMessage: 'Name is required',
        }),
      });
      return;
    }
    if (description === '') {
      setDescriptionInvalid(true);
      setDescriptionError("Description can't be empty");
      notifications.toasts.addDanger({
        title: i18n.translate('web3Soc.newAlert.formValidation.description.error.title', {
          defaultMessage: 'Description is required',
        }),
      });
      return;
    }
    if (output === '') {
      setOutputInvalid(true);
      setOutputError("Output can't be empty");
      notifications.toasts.addDanger({
        title: i18n.translate('web3Soc.newAlert.formValidation.output.error.title', {
          defaultMessage: 'Output is required',
        }),
      });
      return;
    }
    setIsLoading(true);
    const alert: PartialAlert = {
      name,
      description,
      scope: scope as any,
      where,
      output,
      labels,
      receivers: selectedReceivers,
    };
    newAlert(alert)
      .then(() => {
        notifications.toasts.addSuccess({
          title: i18n.translate('web3Soc.newAlert.createAlert.success.title', {
            defaultMessage: 'New Alarm Success',
          }),
        });

        resetForm();
        resetInvalidState();
        // get receivers again
        handleGetReceivers();
      })
      .catch((err) => {
        notifications.toasts.addWarning({
          title: i18n.translate('web3Soc.newAlert.createAlert.error.title', {
            defaultMessage: 'Failed to create new alarm',
          }),
          text: err.message,
        });
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  // Fetch default receivers at first
  useEffect(() => {
    handleGetReceivers();
    handleGetLabelOptions();
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
      description: 'Give your alert a name.',
      required: true,
      errors: [nameError],
      component: (
        <EuiFieldText
          name="name"
          required={true}
          placeholder="Christmas Alert"
          value={name}
          onChange={handleNameChange}
          isInvalid={nameInvalid}
        />
      ),
    },
    {
      title: 'Description',
      description: 'Give your alert a description.',
      required: true,
      errors: [descriptionError],
      component: (
        <EuiFieldText
          name="description"
          required={true}
          placeholder="This alert is for Christmas"
          value={description}
          onChange={handleDescriptionChange}
          isInvalid={descriptionInvalid}
        />
      ),
    },
    {
      title: 'Scope',
      description: 'Select one scope for your alert, the choices are: block, tx, log',
      required: true,
      component: (
        <EuiSelect
          value={scope}
          defaultChecked={true}
          defaultValue={scope}
          onChange={handleScopeChange}
          options={[
            {
              value: 'block',
              text: i18n.translate('web3Soc.newAlert.scope.options.block', {
                defaultMessage: 'block',
              }),
            },
            {
              value: 'tx',
              text: i18n.translate('web3Soc.newAlert.scope.options.tx', {
                defaultMessage: 'tx',
              }),
            },
            {
              value: 'log',
              text: i18n.translate('web3Soc.newAlert.scope.options.log', {
                defaultMessage: 'log',
              }),
            },
          ]}
        ></EuiSelect>
      ),
    },
    {
      title: 'Where',
      description: 'An sql expression for when the alert should be triggered.',
      example: (
        <EuiCodeBlock language="sql" isCopyable>
          {'tx.value > 1000 AND tx.receipt != 0'}
        </EuiCodeBlock>
      ),
      required: false,
      component: <EuiTextArea name="where" compressed value={where} onChange={handleWhereChange} />,
    },
    {
      title: 'Output',
      description: 'The output template string for the alert.',
      required: true,
      errors: [outputError],
      example: (
        <EuiCodeBlock language="markdown" isCopyable={true}>{`\
# Alert from web3_soc
[This transaction](https://etherscan.com/) send {{value}} ETH from {{from_address}} to {{to_address}}, the gas is {{gas}}.`}</EuiCodeBlock>
      ),
      component: (
        <EuiTextArea
          name="output"
          lang="markdown"
          value={output}
          required={true}
          onChange={handleOutputChange}
          isInvalid={outputInvalid}
        />
      ),
    },
    {
      title: 'Receivers',
      description:
        'Select receivers for this alert, if you want to add new receivers, click plus button.',
      required: true,
      component: (
        <>
          <EuiFlexGroup alignItems="center" justifyContent="spaceBetween">
            <EuiFlexItem grow={9}>
              <EuiComboBox
                placeholder="Select multiple receivers"
                options={Object.keys(defaultReceivers).map((key) => {
                  return { label: key };
                })}
                selectedOptions={Object.keys(selectedReceivers).map((key) => {
                  return { label: key };
                })}
                onChange={handleSelectedReceiversChange}
                isClearable={true}
              />
            </EuiFlexItem>
            <EuiFlexItem grow={false}>
              <EuiButtonIcon
                aria-label="Add new receivers"
                iconType="plus"
                color="subdued"
                onClick={() => setIsReceiversModalOpen(true)}
              />
            </EuiFlexItem>
          </EuiFlexGroup>
        </>
      ),
    },
    {
      title: 'Labels',
      description: 'Add labels to this alert. Label is a key-value pair.',
      required: false,
      component: (
        <>
          {labels.map((label, index) => {
            return (
              <EuiFlexGroup
                gutterSize="s"
                alignItems="center"
                justifyContent="center"
                key={`label-${label.key}-${label.value}-${index}`}
              >
                <EuiFlexItem grow={4}>
                  <EuiComboBox
                    prepend="Key"
                    singleSelection={{ asPlainText: true }}
                    options={labelOpts
                      .filter((v, i, arr) => {
                        // remove duplicate and those keys that are already selected in labels array
                        return (
                          arr.findIndex((opt) => opt.key === v.key) === i &&
                          labels.findIndex((l) => l.key === v.key) === -1
                        );
                      })
                      .map((opt) => {
                        return { label: opt.key };
                      })}
                    onCreateOption={(opt) => handleLabelsChange(index, 'key', opt)}
                    selectedOptions={label.key === '' ? [] : [{ label: label.key }]}
                    onChange={(opt) => handleLabelsChange(index, 'key', opt[0].label)}
                    isClearable={false}
                  />
                </EuiFlexItem>
                <EuiFlexItem grow={4}>
                  <EuiComboBox
                    prepend="Value"
                    singleSelection={{ asPlainText: true }}
                    contentEditable={label.key === ''}
                    onCreateOption={(opt) => handleLabelsChange(index, 'value', opt)}
                    options={labelOpts
                      .filter((v, i, arr) => {
                        return (
                          arr.findIndex((opt) => opt.key === label.key && opt.value === v.value) ===
                          i
                        );
                      })
                      .map((opt) => {
                        return { label: opt.value };
                      })}
                    selectedOptions={label.value === '' ? [] : [{ label: label.value }]}
                    onChange={(opt) => handleLabelsChange(index, 'value', opt[0].label)}
                    isClearable={false}
                  />
                </EuiFlexItem>
                <EuiFlexItem grow={1}>
                  <EuiButtonIcon
                    aria-label="Remove this pair"
                    iconType="cross"
                    color="danger"
                    onClick={() => handleRemovePair(index)}
                  />
                </EuiFlexItem>
              </EuiFlexGroup>
            );
          })}
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              marginTop: '1rem',
            }}
          >
            <EuiButton
              size="s"
              aria-label="Add new pair"
              iconType="plus"
              iconSide='right'
              color="primary"
              onClick={handleAddPair}
            >
              New Pair
            </EuiButton>
          </div>
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

  const receiversModal = (
    <EuiModal onClose={closeReceiversModal} initialFocus="[name=popswitch]">
      <EuiModalHeader>
        <EuiModalHeaderTitle>
          <FormattedMessage
            id="web3Soc.newAlert.customReceivers.title"
            defaultMessage="Add Custom Receiver"
          />
        </EuiModalHeaderTitle>
      </EuiModalHeader>

      <EuiModalBody>
        <EuiForm>
          <EuiFormRow
            label={i18n.translate('web3Soc.newAlert.customReceivers.name', {
              defaultMessage: "Receiver's Name",
            })}
          >
            <EuiFieldText
              placeholder="slack_alert_public"
              value={customReceiverName}
              onChange={(e) => setCustomReceiverName(e.target.value)}
            />
          </EuiFormRow>

          <EuiSpacer />

          <EuiFormRow
            label={i18n.translate('web3Soc.newAlert.customReceivers.receiver', {
              defaultMessage: 'receiver',
            })}
          >
            <EuiSelect
              defaultValue={customReceiver}
              options={[{ value: 'slack', text: 'slack' }]}
              value={customReceiver}
              onChange={(e) => setCustomReceiver(e.target.value)}
            />
          </EuiFormRow>

          <EuiFormRow
            label={i18n.translate('web3Soc.newAlert.customReceivers.init_args.url', {
              defaultMessage: 'url',
            })}
          >
            <EuiFieldText
              value={customReceiverUrl}
              onChange={(e) => setCustomReceiverUrl(e.target.value)}
            />
          </EuiFormRow>

          <EuiFormRow
            label={i18n.translate('web3Soc.newAlert.customReceivers.init_args.username', {
              defaultMessage: 'username',
            })}
          >
            <EuiFieldText
              value={customReceiverUsername}
              onChange={(e) => setCustomReceiverUsername(e.target.value)}
            />
          </EuiFormRow>

          <EuiFormRow
            label={i18n.translate('web3Soc.newAlert.customReceivers.init_args.channel', {
              defaultMessage: 'channel',
            })}
          >
            <EuiFieldText
              value={customReceiverChannel}
              onChange={(e) => setCustomReceiverChannel(e.target.value)}
            />
          </EuiFormRow>
        </EuiForm>
      </EuiModalBody>

      <EuiModalFooter>
        <EuiButtonEmpty onClick={handleCancelReceiverModalForm}>
          <FormattedMessage id="web3Soc.newAlert.customReceivers.cancel" defaultMessage="Cancel" />
        </EuiButtonEmpty>
        <EuiButton type="button" onClick={handleSaveReceiverModal} fill>
          <FormattedMessage id="web3Soc.newAlert.customReceivers.submit" defaultMessage="Save" />
        </EuiButton>
      </EuiModalFooter>
    </EuiModal>
  );

  return (
    <>
      {isReceiversModalOpen && receiversModal}
      <EuiPageContent
        style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}
      >
        <EuiForm component="div" invalidCallout="above" style={{ alignItems: 'center' }}>
          {fields.map((field, index) => {
            return (
              <EuiDescribedFormGroup
                title={
                  <h3>
                    <FormattedMessage
                      id={`web3Soc.newAlert.${field.title}.title`}
                      defaultMessage={field.title}
                    />
                  </h3>
                }
                description={
                  <p style={{ textAlign: 'justify' }}>
                    <FormattedMessage
                      id={`web3Soc.newAlert.${field.title}.description`}
                      defaultMessage={field.description}
                    />
                    {field.example}
                  </p>
                }
              >
                <EuiFormRow
                  label={`${field.title}${field.required ? '*' : ''}`}
                  isInvalid={field.isInvalid || false}
                  error={field.errors || []}
                >
                  {field.component}
                </EuiFormRow>
              </EuiDescribedFormGroup>
            );
          })}
          <EuiSpacer size="l"></EuiSpacer>
          <EuiFlexGroup justifyContent="spaceEvenly" alignItems="center" gutterSize="l">
            <EuiFlexItem grow={false}>
              <EuiButton
                onClick={handleReturn}
                isLoading={isLoading}
                color="accent"
                iconSide="right"
                iconType="arrowLeft"
              >
                <FormattedMessage id="web3Soc.newAlert.return.button" defaultMessage="Return" />
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
                <FormattedMessage id="web3Soc.newAlert.preview.button" defaultMessage="Preview" />
              </EuiButton>
            </EuiFlexItem>
            <EuiFlexItem grow={false}>
              <EuiButton
                fill
                onClick={handleSubmitForm}
                isLoading={isLoading}
                color="primary"
                iconSide="right"
                iconType="check"
              >
                <FormattedMessage id="web3Soc.newAlert.submit.button" defaultMessage="Submit" />
              </EuiButton>
            </EuiFlexItem>
          </EuiFlexGroup>
        </EuiForm>
        {isFlyoutOpen && flyout}
      </EuiPageContent>
    </>
  );
};
