import {
  Alert,
  GetAlertMetasRequest,
  GetAlertMetasResponse,
  Receiver,
  LabelOption,
} from '../models';
import { MockAlertMetas, MockAlerts, MockReceivers, MockLabels } from '../mocks/index';
import axios from 'axios';

var baseURL = process.env.WEB_SERVER_URL || 'http://127.0.0.1:8800/v0';

console.log('WEB_SERVER_URL:', baseURL);

const API = axios.create({
  baseURL: baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Get an array of alert metadatas
export const getAlertMetas = (request: GetAlertMetasRequest): Promise<GetAlertMetasResponse> => {
  // TODO: This is a mock implementation. Replace it with a real one. with:
  // return API.get('/alerts', { params: request }).then((response) => response.data));

  return new Promise((resolve, reject) => {
    setTimeout(() => {
      console.debug('get mock alert metas', request);
      resolve({
        total_item_count: 2,
        items: MockAlertMetas,
      });
    }, 1000);
  });
};

// Get an alert by id
export const getAlertById = (alert_id: string): Promise<Alert> => {
  // TODO: This is a mock implementation. Replace it with a real one.
  // return API.get(`/alerts/${alert_id}`).then((response) => response.data));

  const alert = MockAlerts.find((alert) => alert.id === alert_id);
  if (!alert) {
    return Promise.reject(new Error('Alert not found'));
  }
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve(alert);
    }, 600);
  });
};

export const getReceivers = (): Promise<Receiver> => {
  // TODO: This is a mock implementation. Replace it with a real one.
  // return API.get('/receivers').then((response) => response.data));

  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve(MockReceivers);
    }, 300);
  });
};

export const getLabels = (): Promise<LabelOption[]> => {
  // TODO: This is a mock implementation. Replace it with a real one.
  // return API.get('/labels').then((response) => response.data));

  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve(MockLabels);
    }, 300);
  });
};

// Add an alert
export const newAlert = (alert: Omit<Alert, 'id' | 'created_at' | 'is_active'>): Promise<void> => {
  // TODO: This is a mock implementation. Replace it with a real one.
  // return API.post('/alerts', alert).then((response) => response.data));

  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve();
    }, 1000);
  });
};
