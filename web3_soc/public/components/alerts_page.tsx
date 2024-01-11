import React, { useEffect, useState } from 'react';
// import axios from 'axios';
import {
  EuiBasicTable,
  EuiBasicTableColumn,
  Criteria,
  EuiHealth,
  formatDate,
  EuiTableSortingType,
  EuiLoadingSpinner,
  EuiPanel,
  EuiText,
  EuiTitle,
  EuiHorizontalRule,
  EuiButton,
  EuiBadge,
  EuiSpacer,
  EuiFlexGroup,
  EuiFlexItem,
  EuiEmptyPrompt,
} from '@elastic/eui';
import { AlertMeta } from '../../models';
import { getAlertMetas } from '../../api/index';
import { Link } from 'react-router-dom';
import { useWeb3SocContext } from './app';
import { i18n } from '@osd/i18n';
import { FormattedMessage } from '@osd/i18n/react';

export const AlertsPage = () => {
  // Get stuff from context
  const web3SocConext = useWeb3SocContext()!;

  // Alert state
  const [alerts, setAlerts] = useState<AlertMeta[]>([]);

  // loading
  const [isLoading, setIsLoading] = useState(false);

  // Pagination & sorting
  const [totalItemCount, setTotalItemCount] = useState(0);
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(5);
  const [sortField, setSortField] = useState<keyof AlertMeta>('created_at');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const pagination = {
    pageIndex: pageIndex,
    pageSize: pageSize,
    totalItemCount: totalItemCount,
    pageSizeOptions: [3, 5, 8],
  };
  const sorting: EuiTableSortingType<AlertMeta> = {
    sort: {
      field: sortField,
      direction: sortDirection,
    },
  };

  const fetchAndUpdateAlerts = () => {
    setIsLoading(true);
    getAlertMetas({
      page_index: pageIndex,
      page_size: pageSize,
      sort_field: sortField,
      sort_direction: sortDirection,
    })
      .then((res) => {
        setTotalItemCount(res.total_item_count || 0);
        setAlerts(res.items || []);
        console.log('Successfully fetched alerts');
        web3SocConext.notifications.toasts.addSuccess(
          i18n.translate('web3Soc.alertsUpdated', {
            defaultMessage: 'Data updated',
          })
        );
      })
      .catch((error) => {
        console.error('Error fetching alerts:', error);
        web3SocConext.notifications.toasts.addDanger(
          i18n.translate('web3Soc.alertsUpdateError', {
            defaultMessage: `Couldn't update data, see console for details`,
          })
        );
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  //This function is for demo purpose only
  const removeAllAlerts = () => {
    setIsLoading(true);
    setTotalItemCount(0);
    setAlerts([]);
    setIsLoading(false);
  };

  useEffect(() => {
    // When pageLoad, fetch alerts
    // When pageSize changes, we need to fetch alerts again
    fetchAndUpdateAlerts();
  }, [pageSize]);

  const onTableChange = ({ page, sort }: Criteria<AlertMeta>) => {
    if (page) {
      const { index: pageIndex, size: pageSize } = page;
      setPageIndex(pageIndex);
      setPageSize(pageSize);
    }
    if (sort) {
      const { field: sortField, direction: sortDirection } = sort;
      setSortField(sortField);
      setSortDirection(sortDirection);
    }
  };

  const columns: Array<EuiBasicTableColumn<AlertMeta>> = [
    {
      field: 'name',
      name: 'Name',
      truncateText: true,
      render: (name: string, meta: AlertMeta) => {
        return (
          <Link to={`/alerts/${meta.id}`} target="_blank" rel="noopener noreferrer">
            {name}
          </Link>
        );
      },
    },
    {
      field: 'created_at',
      name: 'Created Time',
      datatype: 'date',
      render: (time: string) => formatDate(time, 'YYYY-MM-DD HH:mm:ss'),
      sortable: true,
    },
    {
      field: 'scope',
      name: 'Scope',
      render: (scope: string) => {
        return <EuiBadge color="hollow">{scope}</EuiBadge>;
      },
    },
    {
      field: 'description',
      name: 'Description',
      truncateText: true,
    },
    {
      field: 'is_active',
      name: 'Status',
      render: (is_active: boolean) => {
        const color = is_active ? 'success' : 'grey';
        const label = is_active ? 'Active' : 'Inactive';
        return <EuiHealth color={color}>{label}</EuiHealth>;
      },
    },
  ];

  const panel = (
    <EuiPanel paddingSize="m" style={{ marginTop: '2rem', marginBottom: '2rem' }}>
      <EuiTitle>
        <h3>Alerts</h3>
      </EuiTitle>
      <EuiSpacer size="l" />
      <EuiText>
        <p>
          <FormattedMessage
            id="web3Soc.tipDescription"
            defaultMessage="Here are some instructions or tips about managing and creating alerts. Use the button
            below to update your data."
          ></FormattedMessage>
        </p>
      </EuiText>
      <EuiHorizontalRule />
      <EuiFlexGroup responsive={true} wrap gutterSize="m" alignItems="center" justifyContent='spaceBetween'>
        <EuiFlexItem grow={false}>
          <Link to="/alerts/new">
            <EuiButton color="primary" iconSide="right" iconType="bell">
              <FormattedMessage id="web3Soc.addAlertButton" defaultMessage="Add Alert" />
            </EuiButton>
          </Link>
        </EuiFlexItem>
        <EuiFlexItem grow={false}>
          <EuiButton
            onClick={fetchAndUpdateAlerts}
            color="secondary"
            iconSide="right"
            iconType="refresh"
          >
            <FormattedMessage id="web3Soc.refreshAlertButton" defaultMessage="Refresh Alert" />
          </EuiButton>
        </EuiFlexItem>
        <EuiFlexItem grow={false}>
          <EuiButton onClick={removeAllAlerts} color="danger" iconSide="right" iconType="trash">
            <FormattedMessage id="web3Soc.ignoreThisMessage" defaultMessage="Delete All (for Demo)" />
          </EuiButton>
        </EuiFlexItem>
      </EuiFlexGroup>
    </EuiPanel>
  );

  if (isLoading) {
    return (
      <>
        {panel}
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100%',
            marginTop: '2rem',
          }}
        >
          <EuiLoadingSpinner size="xl" />
        </div>
      </>
    );
  }
  if (alerts.length === 0) {
    return (
      <>
        {panel}
        <EuiEmptyPrompt
          iconType="logoSecurity"
          title={
            <h2>
              <FormattedMessage id="web3Soc.newAlert" defaultMessage="New Alert"></FormattedMessage>
            </h2>
          }
          body={
            <p>
              <FormattedMessage
                id="web3Soc.newAlertDescription"
                defaultMessage="Add a new alert or change your filter settings."
              ></FormattedMessage>
            </p>
          }
          actions={
            <Link to="/alerts/new">
              <EuiButton color="primary" fill iconType="bell" iconSide="right">
                Add an alert
              </EuiButton>
            </Link>
          }
        ></EuiEmptyPrompt>
      </>
    );
  }
  return (
    <>
      {panel}
      <EuiBasicTable
        items={alerts}
        columns={columns}
        pagination={pagination}
        onChange={onTableChange}
        // sorting={sorting}
      />
    </>
  );
};
